"""
ContextManager v2 — Passagem de contexto entre subtarefas.

MUDANÇAS v2:
- NOVO: {output_text_N} → conteúdo textual extraído (web_read, prints, resultados)
- NOVO: limpa variáveis não resolvidas para evitar enviar "{output_X}" literal
- NOVO: extrai texto de resultados web_read e run_python
- Mantém toda a lógica v1 intacta

VARIÁVEIS DISPONÍVEIS:
  {output_folder_N}     → pasta principal
  {output_path_N}       → caminho principal (arquivo ou pasta)
  {output_files_N}      → primeiro arquivo
  {output_all_files_N}  → todos os arquivos separados por ;
  {output_url_N}        → última URL visitada
  {output_text_N}       → conteúdo textual extraído (pesquisa, leitura, resultado)
"""

import os
import re
import json


_PATH_RE = re.compile(r'[A-Za-z]:[/\\][\w/\\ .()\-]+')
_FILE_EXTS = {
    ".html", ".css", ".js", ".ts", ".py", ".json", ".md", ".txt",
    ".xlsx", ".csv", ".pdf", ".docx", ".pptx", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".mp4", ".mov", ".zip", ".exe",
}

# Padrão para detectar variáveis não resolvidas
_UNRESOLVED_VAR = re.compile(r'\{output_\w+_\d+\}')


def _clean_path(raw):
    p = raw.strip().replace("\\", "/")
    p = re.sub(r'[\s)\'",;:!?]+$', "", p)
    return p


def _is_file(path):
    _, ext = os.path.splitext(path)
    return ext.lower() in _FILE_EXTS


def _extract_paths(text):
    found = []
    seen = set()
    for match in _PATH_RE.finditer(text):
        p = _clean_path(match.group())
        if p and p not in seen:
            seen.add(p)
            found.append(p)
    return found


def _extract_urls(text):
    return re.findall(r'https?://[\w./\-?=&#%:@+]+', text)


def _extract_text_content(step_results):
    """Extrai conteúdo textual útil dos resultados das steps."""
    texts = []
    for r in step_results:
        r_str = str(r)
        # Remove prefixos de status (emojis, marcadores)
        clean = re.sub(r'^[🌐🐍✅❌⚠️📊📁📄⏳👁️📸⌨️🎯📦\s]+', '', r_str).strip()

        # Pula resultados curtos ou de status
        if len(clean) < 10:
            continue
        if any(skip in clean.lower() for skip in [
            "ok", "digitou", "clicou", "aguard", "aberto", "focado",
            "enviado", "instalado", "failsafe", "timeout"
        ]):
            continue

        # Conteúdo de web_read (começa com título da página)
        if "🌐" in r_str and len(clean) > 50:
            texts.append(clean[:1500])
            continue

        # Resultado de run_python com output
        if "🐍" in r_str and len(clean) > 30:
            texts.append(clean[:1500])
            continue

        # Qualquer resultado com conteúdo substancial
        if len(clean) > 50:
            texts.append(clean[:1000])

    return "\n".join(texts) if texts else ""


class ContextManager:
    def __init__(self):
        self._store = {}

    def extract(self, subtask_index, agent_name, step_results, engine_workspace, workspace_snapshot):
        idx = subtask_index + 1

        result = {
            "agent": agent_name,
            "files": [],
            "folder": None,
            "url": None,
            "primary_path": None,
            "text": "",  # NOVO v2
            "output": list(step_results),
        }

        all_text = " ".join(str(r) for r in step_results)

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
        seen_paths = set()
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

        # --- NOVO v2: Extrai conteúdo textual ---
        result["text"] = _extract_text_content(step_results)

        # --- Fallback paths ---
        if not result["primary_path"]:
            icon_pattern = re.compile(r'(?:✅|📁|📄|🐍|→)\s*([A-Za-z]:[/\\][\w/\\ .()\-]+)')
            for m in icon_pattern.finditer(combined):
                p = _clean_path(m.group(1))
                if os.path.exists(p):
                    if os.path.isdir(p):
                        result["folder"] = p
                        result["primary_path"] = p
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
        if result["folder"]: _log.append(f"pasta={result['folder']}")
        if result["files"]: _log.append(f"arquivos={len(result['files'])}")
        if result["url"]: _log.append(f"url={result['url']}")
        if result["text"]: _log.append(f"texto={len(result['text'])} chars")
        print(f"  [ContextManager] Sub {idx} ({agent_name}): {', '.join(_log) or 'sem saídas detectadas'}")

        return result

    def prepare_subtask(self, subtask, subtask_index):
        dep_raw = subtask.get("depends_on")

        dep = None
        if dep_raw is not None:
            try:
                dep = int(dep_raw)
            except (ValueError, TypeError):
                dep = None

        if dep is None or dep not in self._store:
            # NOVO v2: limpa variáveis não resolvidas mesmo sem depends_on
            return self._clean_unresolved(subtask)

        ctx = self._store[dep]

        # Monta tabela de substituições (inclui output_text)
        replacements = {
            f"{{output_folder_{dep}}}":    ctx.get("folder") or "",
            f"{{output_path_{dep}}}":      ctx.get("primary_path") or "",
            f"{{output_files_{dep}}}":     ctx["files"][0] if ctx["files"] else "",
            f"{{output_all_files_{dep}}}": ";".join(ctx["files"]),
            f"{{output_url_{dep}}}":       ctx.get("url") or "",
            f"{{output_text_{dep}}}":      ctx.get("text") or "",
        }

        # Também tenta variáveis genéricas que o Maestro possa inventar
        generic_replacements = {
            f"{{output_search_content}}":  ctx.get("text") or "",
            f"{{output_content_{dep}}}":   ctx.get("text") or "",
            f"{{output_result_{dep}}}":    ctx.get("text") or "",
            f"{{output_search_{dep}}}":    ctx.get("text") or "",
        }
        replacements.update(generic_replacements)

        try:
            subtask_str = json.dumps(subtask, ensure_ascii=False)
            for var, val in replacements.items():
                safe_val = val.replace("\\", "/").replace('"', '\\"') if val else ""
                # Trunca texto longo para não estourar mensagem
                if len(safe_val) > 500:
                    safe_val = safe_val[:500] + "..."
                subtask_str = subtask_str.replace(var, safe_val)
            enriched = json.loads(subtask_str)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  [ContextManager] Erro na interpolação: {e}")
            enriched = dict(subtask)

        enriched = self._auto_inject(enriched, dep, ctx)

        # NOVO v2: limpa variáveis que ainda não foram resolvidas
        enriched = self._clean_unresolved(enriched)

        return enriched

    def _auto_inject(self, subtask, dep, ctx):
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
        # NOVO v2: injeta texto se disponível
        if ctx.get("text") and "source_text" not in injected:
            text = ctx["text"]
            if len(text) > 500:
                text = text[:500] + "..."
            injected["source_text"] = text

        result = dict(subtask)
        result["params"] = injected

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

    def _clean_unresolved(self, subtask):
        """Remove variáveis {output_X_N} não resolvidas para evitar enviar literal."""
        try:
            subtask_str = json.dumps(subtask, ensure_ascii=False)
            unresolved = _UNRESOLVED_VAR.findall(subtask_str)
            if unresolved:
                for var in unresolved:
                    print(f"  [ContextManager] Limpando variável não resolvida: {var}")
                    subtask_str = subtask_str.replace(var, "[conteúdo não disponível]")
                return json.loads(subtask_str)
        except Exception:
            pass
        return subtask

    def get(self, idx):
        return self._store.get(idx, {})

    def summary(self):
        return {
            idx: {
                "agent": ctx.get("agent"),
                "files": len(ctx.get("files", [])),
                "folder": ctx.get("folder"),
                "url": ctx.get("url"),
                "text_len": len(ctx.get("text", "")),
                "primary_path": ctx.get("primary_path"),
            }
            for idx, ctx in self._store.items()
        }