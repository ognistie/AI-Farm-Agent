"""
FileAgent v13 — Sysadmin senior com skills + validacao + safety gates.

Skills (NOVO):
- _detect_operation(task) — classifica em organize, move, copy, rename,
  delete, find_duplicates, search, archive
- _categorize_extension(ext) — mapeia .pdf/.docx -> Documentos, etc
- _is_destructive(op) — flag para gates de seguranca

Safety gates (NOVO):
- Operacoes destrutivas (delete, rmtree) precisam de CONFIRMACAO EXPLICITA
  na tarefa ("confirma", "tenho certeza"). Sem isso, o codigo gerado deve
  apenas LISTAR o que seria afetado (dry-run).
- Bloqueia rmtree em paths sensiveis (root, /Windows, /Users)
- Validacao AST + 1 retry com feedback

Boas praticas (NOVO):
- Logging via BaseAgent
- Metricas via helper
- Detecta path sensivel ANTES de enviar pro LLM (defesa em profundidade)
"""

import ast
import json
import os
import re
import getpass
from typing import Optional

from agents.base_agent import BaseAgent
from core.json_validator import safe_parse


USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


# ───────────────────────────────────────────────────────────────────
#  Skills: deteccao de operacao
# ───────────────────────────────────────────────────────────────────

OPERATIONS: dict[str, dict] = {
    # Operacoes mais especificas vem primeiro (find_duplicates antes de copy,
    # por exemplo) — sao consultadas em ordem e prioridade vai para a primeira
    # com maior score.
    "find_duplicates": {
        "keywords": ["duplicad", "duplicate", "repetid", "iguais"],
        "destructive": False,
    },
    "organize": {
        "keywords": ["organiz", "arrum", "agrupa", "categoriz", "separa por tipo",
                     "separa por extens"],
        "destructive": False,
    },
    "archive": {
        # word-boundary: "rar" sozinho matcharia "encontRAR", "compactar" etc.
        # Por isso usamos termos compostos e palavras completas.
        "keywords": ["zip", "compactar", "compacta", "arquivar", " rar ", ".rar"],
        "destructive": False,
    },
    "move": {
        "keywords": ["mover ", "move ", "transferir", "passar para"],
        "destructive": False,
    },
    "copy": {
        # "duplicar" foi removido (ambiguo com find_duplicates).
        # "duplica" idem. Quem quer copiar usa copiar/copia/backup explicito.
        "keywords": ["copiar", "copia ", "fazer copia", "backup"],
        "destructive": False,
    },
    "rename": {
        "keywords": ["renomear", "renomeia", "rename"],
        "destructive": False,
    },
    "delete": {
        # Imperativos tambem ("apague", "exclua", "remova", "limpe"): antes so
        # o infinitivo era reconhecido e "apague os arquivos" nao era destrutivo.
        "keywords": ["delete", "deletar", "remover ", "remove ", "remova", "apagar",
                     "apaga ", "apague", "excluir", "exclui", "exclua", "limpar",
                     "limpa ", "limpe", "jogue fora", "lixeira"],
        "destructive": True,
    },
    "search": {
        "keywords": ["procur", "buscar", "busca ", "encontrar", "encontre",
                     "localiz"],
        "destructive": False,
    },
}

# Categorias para organize
EXTENSION_CATEGORIES: dict[str, list[str]] = {
    "Imagens":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic"],
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".tex"],
    "Planilhas":  [".xlsx", ".xls", ".csv", ".ods", ".tsv"],
    "Apresentacoes": [".pptx", ".ppt", ".odp", ".key"],
    "Videos":     [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"],
    "Audio":      [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Codigo":     [".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
                   ".cpp", ".c", ".h", ".java", ".rs", ".go"],
    "Executaveis": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk"],
}

# Paths sensiveis onde NUNCA deveriamos deletar em massa.
# IMPORTANTE: usar regex para distinguir "C:/Users" (raiz, sensivel) de
# "C:/Users/eu/Documents" (subpasta do usuario, OK).
# Lookbehind `(?<![\w/])` evita falso-positivo em paths que CONTEM esses
# tokens como subpath valido (ex: "/home/etc/conf" nao matcha /etc).
SENSITIVE_PATTERNS = [
    re.compile(r"c:[\\/]+windows",                  re.I),
    re.compile(r"c:[\\/]+program files",            re.I),
    re.compile(r"(?<![\w/])/etc(?:/|$|\s)",         re.I),
    re.compile(r"(?<![\w/])/var/(?:log|lib|spool)", re.I),
    re.compile(r"(?<![\w/])/usr/(?:bin|lib|local|share)", re.I),
    re.compile(r"(?<![\w/])/boot(?:/|$|\s)",        re.I),
    re.compile(r"system32",                         re.I),
    # Raiz de Users SEM subpath (C:/Users no fim, sem /algo)
    re.compile(r"c:[\\/]+users(?:[\\/]?$|[\\/]?\s|[\\/]?[^/\\\w\s])", re.I),
]

# Marcadores de confirmacao explicita na task
CONFIRMATION_MARKERS = [
    "confirma", "confirmo", "tenho certeza", "pode apagar", "pode deletar",
    "yes delete", "force delete", "remover mesmo",
]


def _detect_operation(task: str) -> Optional[str]:
    """Detecta tipo de operacao na task. Retorna None se ambigua."""
    t = task.lower()
    best, best_score = None, 0
    for op, meta in OPERATIONS.items():
        score = sum(1 for kw in meta["keywords"] if kw in t)
        if score > best_score:
            best_score = score
            best = op
    return best if best_score > 0 else None


def _is_destructive(op: Optional[str]) -> bool:
    return bool(op and OPERATIONS.get(op, {}).get("destructive", False))


def _has_explicit_confirmation(task: str) -> bool:
    t = task.lower()
    return any(m in t for m in CONFIRMATION_MARKERS)


def _mentions_sensitive_path(task: str) -> Optional[str]:
    """
    Retorna o path sensivel mencionado, ou None.
    Usa regex para nao dar falso-positivo em subpastas legitimas
    como C:/Users/eu/Documents (raiz do user e diferente de subpasta).
    """
    for pat in SENSITIVE_PATTERNS:
        m = pat.search(task)
        if m:
            return m.group(0)
    return None


# ───────────────────────────────────────────────────────────────────
#  Prompt
# ───────────────────────────────────────────────────────────────────

BASE_PROMPT = """Voce e o FILE AGENT — Senior Sysadmin em arquivos Windows/Linux.
Suas regras sao absolutas. Voce protege os dados do usuario.

REGRAS OPERACIONAIS:
1. Imports: os, shutil, glob, pathlib, subprocess (todos top-level).
2. Caminhos: SEMPRE os.path.expanduser('~') (Desktop, Downloads, Documents).
3. Verifica antes de mover/copiar: os.path.exists(origem).
4. Colisao: se destino existe, sufixo _2/_3 (NUNCA sobrescrever silenciosamente).
5. print() detalhado: origem, destino, contagem, total bytes.
6. Abre o Explorer da pasta resultante no final.
7. UMA step com codigo Python valido completo.
8. JSON puro: {"steps":[{"step":1,"description":"...","code":"..."}]}

REGRAS DE SEGURANCA (BLINDADAS):
- NUNCA delete sem confirmacao do usuario na propria task.
- NUNCA mexer em C:\\Windows, C:\\Users, /, /etc, Program Files.
- Antes de operacao em massa (>500MB): shutil.disk_usage(dest) e abortar
  se livre < 2x do necessario. print() o motivo.
- try/except deve PRINTAR a excecao literal antes de continuar.
- Idempotencia: rodar 2x nao deve duplicar nem perder arquivos.
"""


def _safety_hint(op: Optional[str], destructive: bool,
                 has_confirm: bool, sensitive_path: Optional[str]) -> str:
    """Bloco extra com hints de seguranca para o LLM."""
    if not (op or destructive or sensitive_path):
        return ""

    parts = ["\n=== SKILLS E GATES PARA ESTA TAREFA ==="]
    if op:
        parts.append(f"Operacao: {op.upper()}")
    if destructive and not has_confirm:
        parts.append("⚠️ OPERACAO DESTRUTIVA SEM CONFIRMACAO EXPLICITA.")
        parts.append("Gere codigo que apenas LISTA o que seria deletado (DRY-RUN).")
        parts.append("print() a lista e print('Para confirmar, repita a tarefa com')")
        parts.append("print('a palavra `confirma` ou `tenho certeza`.')")
        parts.append("NAO chame os.remove/os.unlink/shutil.rmtree.")
    elif destructive and has_confirm:
        parts.append("✓ Confirmacao explicita detectada — operacao destrutiva liberada.")
        parts.append("Ainda assim, print() cada arquivo antes de deletar.")
    if sensitive_path:
        parts.append(f"⚠️ Path SENSIVEL mencionado ({sensitive_path}).")
        parts.append("BLOQUEAR: gere codigo que printe um erro e nao execute nada.")
    parts.append("=" * 45)
    return "\n".join(parts)


def _category_hint(task: str) -> str:
    """Se for organize, injeta o mapa de categorias."""
    t = task.lower()
    if "organiz" not in t and "arrum" not in t and "separa" not in t:
        return ""
    cat = json.dumps(EXTENSION_CATEGORIES, ensure_ascii=False)
    return f"\nCATEGORIAS PARA ORGANIZAR: {cat}\n"


# ───────────────────────────────────────────────────────────────────
#  Agent
# ───────────────────────────────────────────────────────────────────


class FileAgent(BaseAgent):
    """Agente sysadmin com skills + safety gates + validacao."""

    def __init__(self):
        super().__init__(name="FILE", system_prompt=BASE_PROMPT)

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)

        # Subagentes: PathResolver (pastas reais / sensiveis) e
        # OperationPlanner (operacao + modo executar/simular). O
        # SafetyAuditor confere o codigo gerado em _call_and_validate.
        from agents.subagents import PathResolver, OperationPlanner
        paths = PathResolver().run(task_text)
        sensitive = paths.data["sensitive"]
        opplan = OperationPlanner().run(task_text, sensitive)
        self._traces = [paths, opplan]
        op = opplan.data["op"]
        destructive = opplan.data["destructive"]
        has_confirm = opplan.data.get("confirmed", False)
        self._mode = opplan.data["mode"]
        self.logger.info(f"Subagentes: {paths.summary} | {opplan.summary}")

        # Gate de path sensivel: rejeita imediatamente sem chamar LLM
        if not opplan.ok:
            self.logger.error(opplan.summary)
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {
                "steps": [],
                "error": (f"Operacao destrutiva em path sensivel ({sensitive}) "
                          "foi bloqueada por seguranca. Especifique uma subpasta."),
                "agent": "FILE",
                "subagents": self._traces,
            }

        # So abrir uma pasta/arquivo nao precisa de LLM nem de script
        from core.paths import is_open_folder_request, extract_path
        if is_open_folder_request(task_text):
            path = extract_path(task_text)
            self.logger.info(f"Abrir caminho direto: {path}")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": [{"step": 1, "action": "open_path", "params": {"path": path},
                               "description": f"Abrir {path}"}],
                    "agent": "FILE", "subagents": self._traces}

        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)

        hints = _safety_hint(op, destructive, has_confirm, sensitive) \
              + _category_hint(task_text)
        if paths.data["folders"]:
            hints += "\nPASTAS RESOLVIDAS (use estes caminhos): " + ", ".join(paths.data["folders"])

        result = self._call_and_validate(task_text + ctx + hints,
                                         retry_feedback=None)
        if result["ok"]:
            return self._wrap_steps(result["steps"])

        self.logger.warning(f"Retry com feedback: {result['reason']}")
        result = self._call_and_validate(task_text + ctx + hints,
                                         retry_feedback=result["reason"])
        if result["ok"]:
            return self._wrap_steps(result["steps"])

        self.logger.error(f"Falhou apos 2 tentativas: {result['reason']}")
        self._metrics["total_plans"] += 1
        self._metrics["failed_plans"] += 1
        from agents.subagents import SafetyAuditor
        return {"steps": [], "error": result["reason"], "agent": "FILE",
                "subagents": getattr(self, "_traces", []) + [SafetyAuditor().trace(False, result["reason"][:120])]}

    # ── Internos ──────────────────────────────────────────────────

    def _call_and_validate(self, user_input: str,
                           retry_feedback: Optional[str]) -> dict:
        from agents.base_agent import brain_guide
        message = f"TAREFA: {user_input}{brain_guide('FILE', user_input)}\nJSON puro."
        if retry_feedback:
            message = (
                f"TAREFA: {user_input}\n\n"
                f"⚠️ TENTATIVA ANTERIOR FALHOU. MOTIVO:\n{retry_feedback}\n"
                "Corrija isso AGORA. JSON puro."
            )

        try:
            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=message,
                max_tokens=8000,
                effort=self.effort,
                agent=self.name,
            )
            plan = safe_parse(raw, self.model)
        except Exception as e:
            return {"ok": False, "reason": f"chamada LLM falhou: {e}"}

        steps_raw = plan.get("steps", [])
        if not steps_raw:
            return {"ok": False, "reason": "LLM nao retornou nenhum step"}

        steps = []
        for st in steps_raw:
            code = st.get("code", "")
            code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)

            # Validacao AST
            try:
                ast.parse(code)
            except SyntaxError as e:
                snippet = ""
                try:
                    snippet = code.split("\n")[(e.lineno or 1) - 1][:120]
                except Exception:
                    pass
                return {
                    "ok": False,
                    "reason": (f"SyntaxError linha {e.lineno}: {e.msg}. "
                               f"Linha: `{snippet}`"),
                }

            # Subagente SafetyAuditor: sem apagar em modo simulacao, sem
            # tocar em pastas do sistema (defesa em profundidade).
            from agents.subagents import SafetyAuditor
            audit = SafetyAuditor().run(code, getattr(self, "_mode", "executar"))
            self._last_audit = audit
            if not audit.ok:
                return {"ok": False, "reason": f"SafetyAuditor: {audit.summary}"}

            steps.append({
                "step": st.get("step", len(steps) + 1),
                "description": st.get("description", ""),
                "action": "run_python",
                "params": {"code": code,
                           "description": st.get("description", "")},
                "agent": "FILE",
            })

        return {"ok": True, "steps": steps, "reason": ""}

    def _wrap_steps(self, steps: list) -> dict:
        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1
        total_code = sum(len(s["params"]["code"]) for s in steps)
        self.logger.info(f"Plano: {len(steps)} step(s), {total_code} chars")
        traces = list(getattr(self, "_traces", []))
        if getattr(self, "_last_audit", None):
            traces.append(self._last_audit)
        return {"steps": steps, "agent": "FILE", "subagents": traces}
