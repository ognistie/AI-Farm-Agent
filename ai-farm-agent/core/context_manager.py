"""
ContextManager v3 — Interpolação segura de contexto entre subtarefas.
MUDANÇAS v3:
- _sanitize_for_json(): escapa TODOS os caracteres problemáticos antes de interpolar
- Resolve "Invalid control character at line 1 column X"
- Trunca texto longo a 400 chars para evitar mensagens gigantes
- Gera summary automático quando texto > 400 chars
- Variáveis: output_text, output_summary, output_folder, output_path, output_files, output_url
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
_UNRESOLVED_VAR = re.compile(r'\{output_\w+_\d+\}')


def _clean_path(raw):
    p = raw.strip().replace("\\", "/")
    p = re.sub(r'[\s)\'",;:!?]+$', "", p)
    return p


def _extract_paths(text):
    found, seen = [], set()
    for m in _PATH_RE.finditer(text):
        p = _clean_path(m.group())
        if p and p not in seen: seen.add(p); found.append(p)
    return found


def _extract_urls(text):
    return re.findall(r'https?://[\w./\-?=&#%:@+]+', text)


def _sanitize_for_json(text):
    """Escapa texto para ser seguro dentro de string JSON.
    Remove caracteres de controle, escapa aspas e barras."""
    if not text:
        return ""
    # Remove caracteres de controle (0x00-0x1F exceto \n \r \t)
    clean = ""
    for ch in text:
        code = ord(ch)
        if code < 32:
            if ch == '\n': clean += "\\n"
            elif ch == '\r': clean += ""  # Remove \r
            elif ch == '\t': clean += " "  # Tab vira espaço
            else: clean += ""  # Remove outros controles
        elif ch == '"': clean += '\\"'
        elif ch == '\\': clean += '\\\\'
        else: clean += ch
    return clean


def _extract_text_content(step_results):
    """Extrai conteúdo textual útil dos resultados."""
    texts = []
    for r in step_results:
        r_str = str(r)
        clean = re.sub(r'^[🌐🐍✅❌⚠️📊📁📄⏳👁️📸⌨️🎯📦\s]+', '', r_str).strip()
        if len(clean) < 15: continue
        skip = ["ok", "digitou", "clicou", "aguard", "aberto", "focado",
                "enviado", "instalado", "failsafe", "timeout", "enter"]
        if any(s in clean.lower()[:30] for s in skip): continue
        texts.append(clean[:1500])
    return "\n".join(texts) if texts else ""


def _make_summary(text, max_len=400):
    """Cria resumo truncado do texto."""
    if not text or len(text) <= max_len:
        return text
    # Corta na última frase completa antes do limite
    truncated = text[:max_len]
    last_period = truncated.rfind('.')
    if last_period > max_len * 0.5:
        return truncated[:last_period + 1]
    return truncated + "..."


class ContextManager:
    def __init__(self):
        self._store = {}

    def extract(self, subtask_index, agent_name, step_results, engine_workspace, workspace_snapshot):
        idx = subtask_index + 1
        result = {
            "agent": agent_name, "files": [], "folder": None,
            "url": None, "primary_path": None,
            "text": "", "summary": "", "output": list(step_results),
        }

        all_text = " ".join(str(r) for r in step_results)
        delta = {k: v for k, v in engine_workspace.items() if k not in workspace_snapshot}
        ws_text = " ".join(str(v.get("result", "")) if isinstance(v, dict) else str(v) for v in delta.values())
        combined = f"{all_text} {ws_text}"

        # Caminhos
        seen = set()
        for p in _extract_paths(combined):
            if p in seen: continue
            seen.add(p)
            if os.path.isfile(p):
                result["files"].append(p)
                if not result["primary_path"]: result["primary_path"] = p
            elif os.path.isdir(p):
                if not result["folder"]: result["folder"] = p
                if not result["primary_path"]: result["primary_path"] = p

        if result["folder"] and not result["files"]:
            try:
                for f in os.listdir(result["folder"]):
                    full = os.path.join(result["folder"], f).replace("\\", "/")
                    if os.path.isfile(full): result["files"].append(full)
            except: pass

        # URLs
        urls = _extract_urls(combined)
        if urls: result["url"] = urls[-1]

        # Texto
        full_text = _extract_text_content(step_results)
        result["text"] = full_text
        result["summary"] = _make_summary(full_text, 400)

        # Fallback paths
        if not result["primary_path"]:
            for m in re.finditer(r'(?:✅|📁|📄|🐍|→)\s*([A-Za-z]:[/\\][\w/\\ .()\-]+)', combined):
                p = _clean_path(m.group(1))
                if os.path.exists(p):
                    if os.path.isdir(p):
                        result["folder"] = p; result["primary_path"] = p
                        try:
                            for f in os.listdir(p):
                                full = os.path.join(p, f).replace("\\", "/")
                                if os.path.isfile(full): result["files"].append(full)
                        except: pass
                    else:
                        result["files"].append(p); result["primary_path"] = p
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
            try: dep = int(dep_raw)
            except: dep = None

        if dep is None or dep not in self._store:
            return self._clean_unresolved(subtask)

        ctx = self._store[dep]

        # Valores sanitizados para JSON
        safe_text = _sanitize_for_json(ctx.get("summary") or ctx.get("text") or "")
        safe_full = _sanitize_for_json(ctx.get("text") or "")
        safe_folder = _sanitize_for_json(ctx.get("folder") or "")
        safe_path = _sanitize_for_json(ctx.get("primary_path") or "")
        safe_files = _sanitize_for_json(ctx["files"][0] if ctx["files"] else "")
        safe_all = _sanitize_for_json(";".join(ctx["files"]))
        safe_url = _sanitize_for_json(ctx.get("url") or "")
        safe_summary = _sanitize_for_json(ctx.get("summary") or "")

        replacements = {
            f"{{output_folder_{dep}}}": safe_folder,
            f"{{output_path_{dep}}}": safe_path,
            f"{{output_files_{dep}}}": safe_files,
            f"{{output_all_files_{dep}}}": safe_all,
            f"{{output_url_{dep}}}": safe_url,
            f"{{output_text_{dep}}}": safe_text,  # Usa summary se disponível
            f"{{output_summary_{dep}}}": safe_summary,
            # Variáveis genéricas que o Maestro pode inventar
            f"{{output_search_content}}": safe_text,
            f"{{output_content_{dep}}}": safe_text,
            f"{{output_result_{dep}}}": safe_text,
            f"{{output_search_{dep}}}": safe_text,
        }

        try:
            subtask_str = json.dumps(subtask, ensure_ascii=False)
            for var, val in replacements.items():
                subtask_str = subtask_str.replace(var, val)
            enriched = json.loads(subtask_str)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  [ContextManager] Erro na interpolação: {e}")
            # Fallback: tenta com texto mais agressivamente limpo
            try:
                for var, val in replacements.items():
                    ultra_clean = re.sub(r'[^\w\s.,;:!?áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ\-()]', '', val)
                    subtask_str = subtask_str.replace(var, ultra_clean[:200])
                enriched = json.loads(subtask_str)
            except:
                enriched = dict(subtask)

        enriched = self._auto_inject(enriched, dep, ctx)
        enriched = self._clean_unresolved(enriched)
        return enriched

    def _auto_inject(self, subtask, dep, ctx):
        params = dict(subtask.get("params", {}))
        if ctx.get("files") and "files" not in params: params["files"] = ctx["files"]
        if ctx.get("folder") and "source_folder" not in params: params["source_folder"] = ctx["folder"]
        if ctx.get("primary_path") and "source_path" not in params: params["source_path"] = ctx["primary_path"]
        if ctx.get("url") and "source_url" not in params: params["source_url"] = ctx["url"]
        if ctx.get("summary") and "source_text" not in params: params["source_text"] = ctx["summary"][:400]
        result = dict(subtask); result["params"] = params
        return result

    def _clean_unresolved(self, subtask):
        try:
            s = json.dumps(subtask, ensure_ascii=False)
            unresolved = _UNRESOLVED_VAR.findall(s)
            if unresolved:
                for var in unresolved:
                    print(f"  [ContextManager] Limpando variável não resolvida: {var}")
                    s = s.replace(var, "[conteudo indisponivel]")
                return json.loads(s)
        except: pass
        return subtask

    def get(self, idx): return self._store.get(idx, {})

    def summary(self):
        return {idx: {"agent": c.get("agent"), "files": len(c.get("files",[])),
                "folder": c.get("folder"), "url": c.get("url"),
                "text_len": len(c.get("text","")), "summary_len": len(c.get("summary",""))}
                for idx, c in self._store.items()}