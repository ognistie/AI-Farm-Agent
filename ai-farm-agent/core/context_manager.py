"""
ContextManager v1 — Passagem de contexto entre subtarefas.

Resolve o Gap 1: permite que o resultado de uma subtarefa (ex: caminho
dos arquivos criados pelo CODE) seja injetado automaticamente nos params
e na task description da subtarefa seguinte (ex: DESKTOP enviar via Teams).

VARIÁVEIS DISPONÍVEIS NOS PARAMS (N = índice da subtarefa dependida):
  {output_folder_N}     → pasta principal criada/usada pela subtarefa N
  {output_path_N}       → caminho principal (arquivo ou pasta)
  {output_files_N}      → primeiro arquivo criado pela subtarefa N
  {output_all_files_N}  → todos os arquivos, separados por ponto-e-vírgula
  {output_url_N}        → última URL visitada pela subtarefa N
"""

import os
import re
import json


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de extração de caminhos
# ──────────────────────────────────────────────────────────────────────────────

# Padrão para caminhos Windows com barra normal ou invertida
_PATH_RE = re.compile(
    r'[A-Za-z]:[/\\][\w/\\ .()\-]+'  # drive letter + resto
)

# Extensões conhecidas de arquivo (para distinguir arquivo de pasta)
_FILE_EXTS = {
    ".html", ".css", ".js", ".ts", ".py", ".json", ".md", ".txt",
    ".xlsx", ".csv", ".pdf", ".docx", ".pptx", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".mp4", ".mov", ".zip", ".exe",
}


def _clean_path(raw: str) -> str:
    """Normaliza e limpa um caminho extraído via regex."""
    p = raw.strip().replace("\\", "/")
    # Remove sufixos inválidos comuns (parênteses, espaços, pontuação)
    p = re.sub(r'[\s)\'",;:!?]+$', "", p)
    return p


def _is_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in _FILE_EXTS


def _extract_paths(text: str) -> list[str]:
    """Extrai todos os caminhos Windows válidos de um texto."""
    found = []
    seen = set()
    for match in _PATH_RE.finditer(text):
        p = _clean_path(match.group())
        if p and p not in seen:
            seen.add(p)
            found.append(p)
    return found


def _extract_urls(text: str) -> list[str]:
    """Extrai URLs http/https de um texto."""
    return re.findall(r'https?://[\w./\-?=&#%:@+]+', text)


# ──────────────────────────────────────────────────────────────────────────────
# ContextManager
# ──────────────────────────────────────────────────────────────────────────────

class ContextManager:
    """
    Gerencia o contexto global entre subtarefas de uma execução.

    Uso típico em server.py:
        ctx = ContextManager()

        # Antes da subtarefa N:
        ws_snapshot = engine.workspace.copy()
        subtask = ctx.prepare_subtask(subtask, si)

        # Depois da subtarefa N:
        ctx.extract(si, agent_name, sub_results, engine.workspace, ws_snapshot)
    """

    def __init__(self):
        # índice 1-based → dict com dados extraídos
        self._store: dict[int, dict] = {}

    # ── Extração ──────────────────────────────────────────────────────────────

    def extract(
        self,
        subtask_index: int,
        agent_name: str,
        step_results: list[str],
        engine_workspace: dict,
        workspace_snapshot: dict,
    ) -> dict:
        """
        Extrai informações estruturadas dos resultados de uma subtarefa concluída.

        Args:
            subtask_index:    Índice 0-based da subtarefa concluída.
            agent_name:       Nome do agente (CODE, DESKTOP, WEB, etc.).
            step_results:     Lista de strings de resultado de cada step.
            engine_workspace: workspace atual do AutomationEngine.
            workspace_snapshot: cópia do workspace ANTES desta subtarefa iniciar
                                (para extrair apenas o delta desta subtarefa).

        Returns:
            dict com: agent, files, folder, url, primary_path, output
        """
        idx = subtask_index + 1  # 1-based

        result = {
            "agent": agent_name,
            "files": [],
            "folder": None,
            "url": None,
            "primary_path": None,
            "output": list(step_results),
        }

        # Texto consolidado dos results desta subtarefa
        all_text = " ".join(str(r) for r in step_results)

        # Delta do workspace desta subtarefa (apenas steps novos)
        delta_workspace = {
            k: v for k, v in engine_workspace.items()
            if k not in workspace_snapshot
        }
        ws_text = " ".join(
            str(v.get("result", "")) if isinstance(v, dict) else str(v)
            for v in delta_workspace.values()
        )

        combined = f"{all_text} {ws_text}"

        # --- Extrai caminhos ---
        seen_paths: set[str] = set()
        for raw_path in _extract_paths(combined):
            p = raw_path
            if p in seen_paths:
                continue
            seen_paths.add(p)

            if os.path.isfile(p):
                result["files"].append(p)
                if not result["primary_path"]:
                    result["primary_path"] = p

            elif os.path.isdir(p):
                if not result["folder"]:
                    result["folder"] = p
                    if not result["primary_path"]:
                        result["primary_path"] = p

        # Se temos pasta mas zero arquivos individuais → lista o conteúdo da pasta
        if result["folder"] and not result["files"]:
            try:
                for fname in os.listdir(result["folder"]):
                    full = os.path.join(result["folder"], fname).replace("\\", "/")
                    if os.path.isfile(full):
                        result["files"].append(full)
            except OSError:
                pass

        # --- Extrai URLs ---
        urls = _extract_urls(combined)
        if urls:
            result["url"] = urls[-1]

        # --- Fallback: se não achou pasta/arquivo, tenta inferir do resultado do run_python ---
        # O CodeAgent frequentemente printa "✅ Criado: C:/..." ou "📁 C:/..."
        if not result["primary_path"]:
            icon_pattern = re.compile(r'(?:✅|📁|📄|🐍|→)\s*([A-Za-z]:[/\\][\w/\\ .()\-]+)')
            for m in icon_pattern.finditer(combined):
                p = _clean_path(m.group(1))
                if os.path.exists(p):
                    if os.path.isdir(p):
                        result["folder"] = p
                        result["primary_path"] = p
                        # Lista arquivos dentro
                        try:
                            for fname in os.listdir(p):
                                full = os.path.join(p, fname).replace("\\", "/")
                                if os.path.isfile(full):
                                    result["files"].append(full)
                        except OSError:
                            pass
                    else:
                        result["files"].append(p)
                        result["primary_path"] = p
                    break

        self._store[idx] = result

        _log = []
        if result["folder"]:
            _log.append(f"pasta={result['folder']}")
        if result["files"]:
            _log.append(f"arquivos={len(result['files'])}")
        if result["url"]:
            _log.append(f"url={result['url']}")
        print(f"  [ContextManager] Sub {idx} ({agent_name}): {', '.join(_log) or 'sem saídas detectadas'}")

        return result

    # ── Preparação da subtarefa seguinte ─────────────────────────────────────

    def prepare_subtask(self, subtask: dict, subtask_index: int) -> dict:
        """
        Prepara uma subtarefa antes de executá-la:
        1. Interpola variáveis de contexto nos params e task.
        2. Injeta automaticamente outputs da subtarefa dependida nos params.

        Args:
            subtask:       Dict da subtarefa gerado pelo Maestro.
            subtask_index: Índice 0-based desta subtarefa (a que vai executar).

        Returns:
            Subtarefa enriquecida (cópia, não modifica o original).
        """
        dep_raw = subtask.get("depends_on")

        # depends_on pode ser int, string "1", ou None
        dep: int | None = None
        if dep_raw is not None:
            try:
                dep = int(dep_raw)
            except (ValueError, TypeError):
                dep = None

        if dep is None or dep not in self._store:
            return subtask

        ctx = self._store[dep]

        # Monta tabela de substituições
        replacements = {
            f"{{output_folder_{dep}}}":    ctx.get("folder") or "",
            f"{{output_path_{dep}}}":      ctx.get("primary_path") or "",
            f"{{output_files_{dep}}}":     ctx["files"][0] if ctx["files"] else "",
            f"{{output_all_files_{dep}}}": ";".join(ctx["files"]),
            f"{{output_url_{dep}}}":       ctx.get("url") or "",
        }

        # Serializa subtarefa, substitui e desserializa
        try:
            subtask_str = json.dumps(subtask, ensure_ascii=False)
            for var, val in replacements.items():
                # Normaliza barras para JSON seguro
                safe_val = val.replace("\\", "/")
                subtask_str = subtask_str.replace(var, safe_val)
            enriched: dict = json.loads(subtask_str)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  [ContextManager] Erro na interpolação: {e}")
            enriched = dict(subtask)

        # Injeta outputs nos params automaticamente (campos extras)
        enriched = self._auto_inject(enriched, dep, ctx)

        return enriched

    def _auto_inject(self, subtask: dict, dep: int, ctx: dict) -> dict:
        """
        Injeta automaticamente os outputs do contexto nos params da subtarefa,
        mas SOMENTE se os campos não foram explicitamente definidos.
        Evita sobrescrever intenções do Maestro.
        """
        params = subtask.get("params", {})
        injected = dict(params)

        if ctx.get("files") and "files" not in injected:
            injected["files"] = ctx["files"]

        if ctx.get("folder") and "source_folder" not in injected:
            injected["source_folder"] = ctx["folder"]

        if ctx.get("primary_path") and "source_path" not in injected:
            injected["source_path"] = ctx["primary_path"]

        if ctx.get("url") and "source_url" not in injected:
            injected["source_url"] = ctx["url"]

        result = dict(subtask)
        result["params"] = injected

        # Também enriquece o texto da task se ainda tem variáveis não resolvidas
        task_str = result.get("task", "")
        for field, val in [
            ("pasta", ctx.get("folder") or ""),
            ("arquivo", ctx["files"][0] if ctx["files"] else ""),
            ("url", ctx.get("url") or ""),
        ]:
            if val and f"{{{field}}}" in task_str:
                task_str = task_str.replace(f"{{{field}}}", val)
        result["task"] = task_str

        return result

    # ── Acesso ao store ───────────────────────────────────────────────────────

    def get(self, idx: int) -> dict:
        """Retorna contexto extraído da subtarefa N (1-based)."""
        return self._store.get(idx, {})

    def summary(self) -> dict:
        """Retorna resumo de todos os contextos extraídos (para debug/log)."""
        return {
            idx: {
                "agent": ctx.get("agent"),
                "files": len(ctx.get("files", [])),
                "folder": ctx.get("folder"),
                "url": ctx.get("url"),
                "primary_path": ctx.get("primary_path"),
            }
            for idx, ctx in self._store.items()
        }