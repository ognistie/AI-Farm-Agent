"""
Subagentes — 3 ajudantes por agente, cada um com um papel fixo:

    1. ENTENDER  — le o pedido e os params do Maestro, extrai o que importa
    2. MONTAR    — produz o insumo da execucao (rota, texto, esquema...)
    3. CONFERIR  — revisa o que foi proposto/executado antes de seguir

Principio (ai-agent-engineer): a menor autonomia que resolve. Todos sao
deterministicos (custo zero de tokens), exceto o Builder do CodeAgent, que
e a propria chamada ao modelo. Nenhum subagente amplia permissoes: eles
normalizam entradas, montam passos e REPROVAM o que estiver errado.

Cada execucao gera um rastro (`Trace`) que o agente devolve em
`plan["subagents"]` — o controller registra no log e no plano do Obsidian.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Trace:
    name: str
    role: str            # entender | montar | conferir
    ok: bool = True
    summary: str = ""
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("data", None)
        return d


class Subagent:
    name = "Subagent"
    parent = ""
    role = "entender"
    description = ""

    def trace(self, ok: bool = True, summary: str = "", **data: Any) -> Trace:
        return Trace(self.name, self.role, ok, summary, data)


# ═══════════════════════════════════════════════════════════════════
#  WEB
# ═══════════════════════════════════════════════════════════════════

_SEARCH = re.compile(r"\b(pesquis\w*|procur\w*|busc\w*|busqu\w*|search)\b", re.IGNORECASE)
_READ = re.compile(r"\b(ler|leia|resum\w*|extra\w*|copi\w*\s+o\s+conteudo|o que diz)\b", re.IGNORECASE)


class QueryBuilder(Subagent):
    name, parent, role = "QueryBuilder", "WEB", "entender"
    description = "Descobre a intencao (pesquisar, abrir, ler), o site e o termo de busca."

    def run(self, task: str, params: Optional[dict] = None) -> Trace:
        from agents.web_agent import extract_query
        params = params or {}
        t = (task or "").lower()
        url = (params.get("url") or "").strip()
        query = (params.get("query") or "").strip() or extract_query(task)
        site = "youtube" if ("youtube" in t or "youtube" in url.lower()) else "google"
        intent = ("search" if (params.get("query") or _SEARCH.search(t))
                  else "read" if _READ.search(t) else "open")
        click_first = any(k in t for k in ("primeiro resultado", "primeiro video", "primeiro vídeo",
                                            "abra o primeiro", "clique no primeiro", "clica no primeiro"))
        ok = intent != "search" or bool(query)
        summary = f"intencao={intent} site={site}" + (f" termo='{query}'" if query else "")
        return self.trace(ok, summary if ok else "pesquisa sem termo", intent=intent, site=site,
                          query=query, url=url, click_first=click_first,
                          new_tab=("nova aba" in t or "nova guia" in t))


class Navigator(Subagent):
    name, parent, role = "Navigator", "WEB", "montar"
    description = "Monta a rota: URL de resultados, site conhecido ou fallback nativo sem Playwright."

    def run(self, task: str, params: Optional[dict], has_playwright: bool) -> Trace:
        from agents.web_agent import _detect_web_routine, _native_fallback
        steps = _detect_web_routine(task, params, playwright=has_playwright)
        if not steps:
            return self.trace(False, "sem rotina pronta; o LLM monta os passos", steps=None)
        mode = "playwright"
        if not has_playwright:
            steps = _native_fallback(steps) or steps
            mode = "navegador padrao"
        return self.trace(True, f"{len(steps)} passos ({mode})", steps=steps)


_INJECTION = re.compile(
    r"(ignore (all |as )?(previous|anteriores)|ignore as instru|desconsidere as instru|"
    r"you are now|system prompt|voce agora e|execute o comando|run this command)",
    re.IGNORECASE,
)


class ContentGuard(Subagent):
    name, parent, role = "ContentGuard", "WEB", "conferir"
    description = "Revisa o que foi lido da web: corta excesso e marca tentativas de prompt injection."
    MAX_CHARS = 2500

    def review(self, action: str, result: dict) -> Trace:
        if action not in ("web_read", "browser_read") or not isinstance(result.get("result"), str):
            return self.trace(True, "nada a revisar")
        text = result["result"]
        flagged = bool(_INJECTION.search(text))
        if flagged:
            text = "[CONTEUDO NAO CONFIAVEL — possivel prompt injection removido]\n" + _INJECTION.sub("[removido]", text)
        if len(text) > self.MAX_CHARS:
            text = text[: self.MAX_CHARS] + "…"
        result["result"] = text
        return self.trace(not flagged, "INJECTION_DETECTED" if flagged else "conteudo ok")


# ═══════════════════════════════════════════════════════════════════
#  DESKTOP
# ═══════════════════════════════════════════════════════════════════

APP_ALIASES = {
    "notepad": ("bloco de notas", "notepad", "bloco notas", "notas"),
    "word": ("word", "microsoft word", "documento do word"),
    "excel": ("excel", "microsoft excel"),
    "teams": ("teams", "microsoft teams"),
    "whatsapp": ("whatsapp", "whats", "zap"),
    "outlook": ("outlook", "e-mail do outlook"),
    "vscode": ("vs code", "vscode", "visual studio code"),
    "paint": ("paint",),
    "calculadora": ("calculadora", "calculator"),
    "spotify": ("spotify",),
    "explorer": ("explorer", "explorador", "explorador de arquivos"),
}


class AppResolver(Subagent):
    name, parent, role = "AppResolver", "DESKTOP", "entender"
    description = "Identifica o aplicativo (apelidos incluidos) e se existe rotina pronta para ele."

    def run(self, task: str, params: Optional[dict] = None) -> Trace:
        params = params or {}
        raw = (params.get("app") or "").lower().strip()
        app = next((k for k, names in APP_ALIASES.items() if raw in names or raw == k), raw)
        if not app:
            t = (task or "").lower()
            app = next((k for k, names in APP_ALIASES.items() if any(n in t for n in names)), "")
        return self.trace(True, f"app={app or '?'}", app=app)


class ContentComposer(Subagent):
    name, parent, role = "ContentComposer", "DESKTOP", "montar"
    description = "Prepara o texto a digitar: quebras de linha reais, espacos, limite de tamanho."
    MAX_CHARS = 6000

    def run(self, params: Optional[dict]) -> Trace:
        params = dict(params or {})
        for key in ("text", "message"):
            val = params.get(key)
            if isinstance(val, str) and val:
                val = val.replace("\\n", "\n").replace("\r\n", "\n").strip()
                val = re.sub(r"[ \t]+\n", "\n", val)
                params[key] = val[: self.MAX_CHARS]
        text = params.get("text") or params.get("message") or ""
        lines = text.count("\n") + 1 if text else 0
        return self.trace(True, f"texto: {len(text)} chars, {lines} linha(s)" if text else "sem texto",
                          params=params)


class ScreenGuard(Subagent):
    name, parent, role = "ScreenGuard", "DESKTOP", "conferir"
    description = "Revisa os passos: espera apos abrir app, cliques nunca na barra de tarefas, limite de passos."
    MAX_STEPS = 20

    def run(self, steps: list) -> Trace:
        fixed, fixes, problems = [], 0, []
        for i, st in enumerate(steps):
            fixed.append(st)
            if st.get("action") in ("app_search", "open_app"):
                nxt = steps[i + 1] if i + 1 < len(steps) else None
                if not nxt or nxt.get("action") not in ("wait", "wait_for_window"):
                    fixed.append({"action": "wait", "params": {"seconds": 3},
                                  "description": "Aguardar app abrir", "agent": "DESKTOP"})
                    fixes += 1
            desc = str((st.get("params") or {}).get("description", "")).lower()
            if st.get("action", "").startswith("vision_") and "barra de tarefas" in desc:
                problems.append(f"clique na barra de tarefas: '{desc[:40]}'")
        if len(fixed) > self.MAX_STEPS:
            problems.append(f"{len(fixed)} passos (max {self.MAX_STEPS})")
        for n, st in enumerate(fixed, 1):
            st["step"] = n
        summary = "; ".join(problems) if problems else (f"{fixes} espera(s) adicionada(s)" if fixes else "ok")
        return self.trace(not problems, summary, steps=fixed)


# ═══════════════════════════════════════════════════════════════════
#  CODE
# ═══════════════════════════════════════════════════════════════════

class Architect(Subagent):
    name, parent, role = "Architect", "CODE", "entender"
    description = "Classifica o projeto (tipo, complexidade, stack, tema) e, se multi-arquivo, desenha o esqueleto."

    PLANNER_TARGETS = {"python_cli", "rest_api", "fullstack_web", "python_gui",
                       "python_game", "python_data", "python_bot", "interactive_site"}

    def run(self, analysis_text: str, task_text: str) -> Trace:
        from agents.code_skills import analyze
        from agents.code_planner import make_plan, format_plan_for_generator
        skills = analyze(analysis_text)
        plan_hint, files = "", 0
        if skills["project_type"] in self.PLANNER_TARGETS:
            planner = make_plan(task_text, skills)
            if planner["ok"]:
                plan_hint = format_plan_for_generator(planner["plan"])
                files = len(planner["plan"].get("files", []))
        summary = f"{skills['project_type']} / {skills['complexity']} / tema '{skills['topic']}'"
        if files:
            summary += f" / esqueleto com {files} arquivos"
        return self.trace(True, summary, skills=skills, plan_hint=plan_hint)


class Builder(Subagent):
    name, parent, role = "Builder", "CODE", "montar"
    description = "Gera o codigo completo com o modelo (unico subagente que usa LLM)."

    def record(self, attempt: int, ok: bool, reason: str = "") -> Trace:
        return self.trace(ok, f"tentativa {attempt}" + ("" if ok else f": {reason[:80]}"))


class Reviewer(Subagent):
    name, parent, role = "Reviewer", "CODE", "conferir"
    description = "Valida sintaxe, estrutura, qualidade e tema do codigo antes de executar."

    def run(self, code: str, project_type: str, topic: str, task: str) -> Trace:
        from agents.code_validators import validate_all
        v = validate_all(code, project_type, topic, task=task)
        return self.trace(v["ok"], "aprovado" if v["ok"] else v["reason"][:120], result=v)


# ═══════════════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════════════

class SchemaDesigner(Subagent):
    name, parent, role = "SchemaDesigner", "DATA", "entender"
    description = "Descobre o tipo de planilha e sugere colunas iniciais."

    def run(self, task: str) -> Trace:
        from agents.data_agent import _detect_spreadsheet_type, SPREADSHEET_TYPES
        stype = _detect_spreadsheet_type(task)
        cols = SPREADSHEET_TYPES[stype]["columns"] if stype else []
        return self.trace(True, f"tipo={stype or 'generico'}" + (f", {len(cols)} colunas" if cols else ""),
                          stype=stype, columns=cols)


class FormulaChartDesigner(Subagent):
    name, parent, role = "FormulaChartDesigner", "DATA", "montar"
    description = "Decide formulas (SUM, AVERAGE...) e grafico conforme o pedido e o tipo."

    def run(self, task: str, stype: Optional[str]) -> Trace:
        from agents.data_agent import _needs_chart, _needs_formulas, SPREADSHEET_TYPES
        chart = _needs_chart(task)
        formulas = _needs_formulas(task)
        if stype and not formulas:
            formulas = list(SPREADSHEET_TYPES[stype].get("suggests_formulas", []))
        return self.trace(True, f"grafico={'sim' if chart else 'nao'} formulas={formulas or '-'}",
                          chart=chart, formulas=formulas)


class SheetReviewer(Subagent):
    name, parent, role = "SheetReviewer", "DATA", "conferir"
    description = "Revisa o codigo da planilha: sintaxe, salva .xlsx, nao sobrescreve, abre no Excel."

    def run(self, code: str) -> Trace:
        try:
            ast.parse(code)
        except SyntaxError as e:
            return self.trace(False, f"SyntaxError linha {e.lineno}: {e.msg}")
        if ".xlsx" not in code:
            return self.trace(False, "codigo nao salva nenhum arquivo .xlsx")
        if ".save(" not in code:
            return self.trace(False, "codigo nao chama wb.save()")
        warnings = []
        if "exists" not in code:
            warnings.append("nao checa se o arquivo ja existe (risco de sobrescrever)")
        if "start" not in code and "startfile" not in code:
            warnings.append("nao abre a planilha ao final")
        return self.trace(True, "aprovado" + (f" (avisos: {'; '.join(warnings)})" if warnings else ""),
                          warnings=warnings)


# ═══════════════════════════════════════════════════════════════════
#  FILE
# ═══════════════════════════════════════════════════════════════════

_HOME = os.path.expanduser("~").replace("\\", "/")
KNOWN_FOLDERS = {
    "downloads": "Downloads", "download": "Downloads",
    "documentos": "Documents", "documents": "Documents",
    "area de trabalho": "Desktop", "área de trabalho": "Desktop", "desktop": "Desktop",
    "imagens": "Pictures", "fotos": "Pictures", "pictures": "Pictures",
    "videos": "Videos", "vídeos": "Videos", "musicas": "Music", "músicas": "Music",
}


class PathResolver(Subagent):
    name, parent, role = "PathResolver", "FILE", "entender"
    description = "Traduz pastas conhecidas (Downloads, Documentos...) para caminhos reais e detecta caminhos sensiveis."

    def run(self, task: str) -> Trace:
        from agents.file_agent import _mentions_sensitive_path
        t = (task or "").lower()
        folders = sorted({f"{_HOME}/{v}" for k, v in KNOWN_FOLDERS.items() if re.search(rf"\b{k}\b", t)})
        sensitive = _mentions_sensitive_path(task)
        summary = ", ".join(folders) if folders else "nenhuma pasta conhecida citada"
        if sensitive:
            summary += f" | SENSIVEL: {sensitive}"
        return self.trace(True, summary, folders=folders, sensitive=sensitive)


class OperationPlanner(Subagent):
    name, parent, role = "OperationPlanner", "FILE", "montar"
    description = "Classifica a operacao e decide o modo: executar ou so simular (destrutiva sem confirmacao)."

    def run(self, task: str, sensitive: Optional[str]) -> Trace:
        from agents.file_agent import _detect_operation, _is_destructive, _has_explicit_confirmation
        op = _detect_operation(task)
        destructive = _is_destructive(op)
        confirmed = _has_explicit_confirmation(task)
        if destructive and sensitive:
            return self.trace(False, f"operacao destrutiva em caminho sensivel ({sensitive}) bloqueada",
                              op=op, mode="bloqueado", destructive=True)
        mode = "simular" if destructive and not confirmed else "executar"
        return self.trace(True, f"op={op or '?'} modo={mode}", op=op, mode=mode, destructive=destructive,
                          confirmed=confirmed)


_DESTRUCTIVE_CALLS = re.compile(r"\b(shutil\.rmtree|os\.remove|os\.unlink|os\.rmdir|\.unlink\(|\.rmdir\()")
_SENSITIVE_IN_CODE = ("C:/Windows", "C:\\\\Windows", "Program Files", "System32", "/etc", "/var")


def _sensitive_paths_in_use(tree: ast.AST) -> list:
    """Caminhos de sistema USADOS no codigo. Citar o caminho numa lista de bloqueio
    ou numa comparacao de protecao (`if p.startswith("C:/Windows")`, `PROIBIDAS = [...]`)
    e o codigo se defendendo — antes isso reprovava o plano (falso positivo)."""
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        hit = next((sp for sp in _SENSITIVE_IN_CODE if sp.replace("\\\\", "\\") in node.value
                    or sp in node.value), None)
        if not hit:
            continue
        parent = parents.get(node)
        defensive = isinstance(parent, (ast.List, ast.Tuple, ast.Set, ast.Compare)) or (
            isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute)
            and parent.func.attr in ("startswith", "endswith", "lower", "upper", "find", "count"))
        if not defensive:
            found.append(hit)
    return found


class SafetyAuditor(Subagent):
    name, parent, role = "SafetyAuditor", "FILE", "conferir"
    description = "Audita o codigo gerado: sem apagar em modo simulacao, sem tocar em pastas do sistema."

    def run(self, code: str, mode: str) -> Trace:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return self.trace(False, f"SyntaxError linha {e.lineno}: {e.msg}")
        destructive = bool(_DESTRUCTIVE_CALLS.search(code))
        if destructive or "shutil.move" in code:
            used = _sensitive_paths_in_use(tree)
            if used:
                return self.trace(False, f"codigo mexe em caminho do sistema ({used[0]})")
        if mode == "simular" and destructive:
            return self.trace(False, "pedido sem confirmacao: o codigo deve so LISTAR, mas apaga arquivos")
        if "print" not in code:
            return self.trace(True, "aprovado (aviso: sem resumo impresso)")
        return self.trace(True, "aprovado")


# Registro para documentacao (vault) e testes
REGISTRY = {
    "WEB": [QueryBuilder, Navigator, ContentGuard],
    "DESKTOP": [AppResolver, ContentComposer, ScreenGuard],
    "CODE": [Architect, Builder, Reviewer],
    "DATA": [SchemaDesigner, FormulaChartDesigner, SheetReviewer],
    "FILE": [PathResolver, OperationPlanner, SafetyAuditor],
}


def summarize(traces: list) -> str:
    """'QueryBuilder ✓ intencao=search · Navigator ✓ 3 passos · ...'"""
    return " · ".join(f"{t.name} {'✓' if t.ok else '✗'} {t.summary}".strip() for t in traces)
