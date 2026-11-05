"""
Abrir o que ja existe, sem modelo: a pasta ou o site do projeto da conversa, uma subpasta, a pasta
alterada em certo horario, ou trazer para a frente a janela de uma pasta.

Sem isto esses pedidos caiam em agentes que so sabem criar: o agente de codigo criava um projeto
novo para "verificar o site", e o de arquivos devolvia um plano vazio. Aqui so ha dois efeitos,
abrir algo que existe (open_path) e trazer uma janela para a frente (focus_window). Quando o alvo
nao e unico, a resposta e uma pergunta com as opcoes reais, nunca um palpite.
"""

from __future__ import annotations

import difflib
import os
import re
import time
from pathlib import Path
from typing import Optional

from core.lexicon import norm
from core.paths import EXECUTABLE_EXT, _ALIASES, known_folder

_OPEN = re.compile(r"\b(?:abr\w*|abre|mostr\w*|ver|veja|exib\w*|acess\w*|entr\w*|rod\w*|execut\w*|traz\w*|traga|"
                   r"volt\w*|clic\w*|cliqu\w*)\b")
_COMPOUND = re.compile(r"\b(?:e depois|e tambem|depois disso|em seguida)\b")
_PROJECT_FOLDER = re.compile(r"\bpasta\s+(?:d[oa]s?\s+)?(?:arquivos\s+)?(?:d[oa]\s+|desse\s+|deste\s+)?(?:projeto|site)\b|"
                             r"\bpasta\s+(?:que\s+)?(?:voce\s+)?(?:criou|gerou|fez)\b")
_SITE = re.compile(r"\b(?:site|pagina|projeto|resultado|index(?:\.html)?|html)\b")
_BROWSER = re.compile(r"\b(?:navegador|browser|chrome|edge|firefox|google)\b")
_RUN_SITE = re.compile(r"\b(?:rod\w*|execut\w*|ver|veja)\s+(?:o\s+)?(?:site|programa do site|resultado)\b")
_FRONT = re.compile(r"\b(?:traz\w*|traga|volt\w*|mostr\w*)\b.*\b(?:pra|para a|para)\s+(?:frente)\b|"
                    r"\bclic\w*\s+no\s+icone\b|\bbarra de tarefas\b")
_NESTED = re.compile(r"\bpasta\s+['\"]?(?P<child>[\w\-. ]{1,40}?)['\"]?\s+dentro\s+d[aoe]\s+(?:pasta\s+)?['\"]?"
                     r"(?P<parent>[\w\-. ]{1,40}?)['\"]?(?=\s+(?:n[ao]|em|d[aoe])\s|[,.!?]|$)")
_IN_FOLDER = re.compile(r"\b(?:dentro\s+d[aoe]|n[ao])\s+(?:pasta\s+)?['\"]?(?P<parent>[\w\-. ]{1,40}?)['\"]?"
                        r"(?=\s*,|\s+(?:a|o|que|n[ao]|em)\s|[.!?]|$)")
_AT_TIME = re.compile(r"\b(?:alterad|modificad|editad|mexid|salv)\w*\s+(?:as|a|em|por volta das)\s+"
                      r"(?P<h>\d{1,2})(?:\s*(?::|h|e)\s*(?P<m>\d{1,2}))?")
_ORDINAL = re.compile(r"\b(primeir|segund|terceir|quart|quint|ultim)\w*\s+pasta\b")
_FOLDER_WORD = re.compile(r"\bpasta\s+['\"]?(?P<name>[\w\-.]{2,40}(?:\s+[\w\-.]{2,40})?)['\"]?")
_STOP = {"na", "no", "da", "do", "de", "em", "area", "trabalho", "barra", "tarefas", "dentro", "que", "pra", "para"}
SIMILAR = 0.8
MAX_OPTIONS = 8


def _plain(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", norm(text or "")).strip()


def _base_in(text: str) -> Optional[str]:
    """Pasta conhecida citada ("area de trabalho", "documentos")."""
    n = norm(text)
    for alias in sorted(_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", n):
            return known_folder(_ALIASES[alias])
    return None


def _children(folder: str) -> list:
    try:
        return sorted((e for e in os.scandir(folder) if e.is_dir() and not e.name.startswith(".")),
                      key=lambda e: e.name.lower())
    except OSError:
        return []


def _match_child(folder: str, spoken: str) -> tuple:
    """-> (caminho, opcoes). Caminho so quando um unico filho corresponde ao nome falado."""
    wanted = _plain(spoken)
    children = _children(folder)
    exact = [e.path for e in children if _plain(e.name) == wanted]
    if len(exact) == 1:
        return exact[0], []
    close = [e.path for e in children if difflib.SequenceMatcher(None, _plain(e.name), wanted).ratio() >= SIMILAR]
    if len(close) == 1:
        return close[0], []
    return None, [e.name for e in children][:MAX_OPTIONS]


def _locate_folder(spoken: str, text: str, session) -> Optional[str]:
    """Uma pasta pelo nome: a ultima da conversa, ou filha da pasta conhecida citada (padrao: Area de Trabalho)."""
    wanted = _plain(spoken)
    if not wanted:
        return None
    last = getattr(session, "folder", None) if session is not None else None
    if last and os.path.isdir(last) and _plain(os.path.basename(last)) == wanted:
        return last
    for base in [b for b in (_base_in(text), known_folder("Desktop"), known_folder("Documents")) if b]:
        path, _ = _match_child(base, spoken)
        if path:
            return path
    return None


def _project_folder(session) -> Optional[str]:
    code = getattr(session, "code", None) if session is not None else None
    folder = (code or {}).get("folder") if isinstance(code, dict) else None
    return folder if folder and os.path.isdir(folder) else None


def _site_page(folder: str) -> Optional[str]:
    index = os.path.join(folder, "index.html")
    if os.path.isfile(index):
        return index
    pages = sorted(p for p in Path(folder).rglob("*.htm*") if p.is_file())
    return str(pages[0]) if pages else None


def _ask(question: str) -> dict:
    return {"needs_clarification": True, "question": question}


def _options(prefix: str, names: list) -> str:
    return prefix + (" Tem: " + ", ".join(names) + "." if names else " Essa pasta não tem subpastas.")


def _plan(task: str, existing: dict, what: str) -> dict:
    return {"analysis": f"{what} (direto, sem IA)", "skills": [], "fast_path": "abrir",
            "subtasks": [{"agent": "DESKTOP", "task": what, "original_task": task, "params": {"existing": existing}}]}


def _open(task: str, path: str, what: str) -> dict:
    return _plan(task, {"action": "open_path", "path": path}, what)


def _windows_titled(name: str) -> list:
    """Janelas visiveis cujo titulo e o nome pedido (o Explorer usa o nome da pasta como titulo)."""
    try:
        import pygetwindow as gw
        from core.automation import is_our_browser
    except Exception:
        return []
    wanted = _plain(name)
    found = []
    for window in gw.getAllWindows():
        title = window.title or ""
        if window.visible and title and not is_our_browser(title) and _plain(title.split(" - ")[0]) == wanted:
            found.append((window._hWnd, title))
    return found


def _by_time(parent: str, hour: int, minute: Optional[int]) -> tuple:
    hits, listing = [], []
    for entry in _children(parent):
        try:
            stamp = time.localtime(entry.stat().st_mtime)
        except OSError:
            continue
        listing.append(f"{entry.name} ({stamp.tm_hour:02d}:{stamp.tm_min:02d})")
        if stamp.tm_hour == hour and (minute is None or stamp.tm_min == minute):
            hits.append(entry.path)
    return hits, listing[:MAX_OPTIONS]


def existing_plan(task: str, session=None) -> Optional[dict]:
    """Plano direto para abrir algo que existe, uma pergunta com opcoes reais, ou None (segue o fluxo normal)."""
    n = norm(task or "")
    if not _OPEN.search(n) or _COMPOUND.search(n):
        return None
    project = _project_folder(session)

    # 1. O site do projeto no navegador ("abrir o site no navegador", "rodar o site")
    if (_SITE.search(n) and _BROWSER.search(n)) or _RUN_SITE.search(n):
        if project:
            page = _site_page(project)
            if page:
                return _open(task, page, f"abrir {os.path.basename(page)} do projeto no navegador")
            if _RUN_SITE.search(n) or _SITE.search(n):
                return _ask("O projeto desta conversa não tem página HTML para abrir no navegador.")
        elif re.search(r"\b(?:projeto|site)\b", n):
            return _ask("Ainda não há um projeto criado nesta conversa. Qual pasta ou endereço devo abrir?")
        return None

    # 2. A pasta do projeto ("abrir a pasta dos arquivos do projeto")
    if _PROJECT_FOLDER.search(n):
        if project:
            return _open(task, project, f"abrir a pasta do projeto {os.path.basename(project)}")
        return _ask("Ainda não criei nenhum projeto nesta conversa. Qual pasta devo abrir?")

    # 3. Trazer a janela de uma pasta para a frente ("clica no icone da pasta trabalhos na barra de tarefas")
    named = _FOLDER_WORD.search(n)
    if _FRONT.search(n) and named:
        name = " ".join(w for w in named.group("name").split() if w not in _STOP)
        windows = _windows_titled(name)
        if len(windows) == 1:
            hwnd, title = windows[0]
            return _plan(task, {"action": "focus_window", "title": title, "hwnd": hwnd}, f"trazer {title} para a frente")
        folder = _locate_folder(name, n, session)
        if folder and not windows:
            return _open(task, folder, f"abrir a pasta {os.path.basename(folder)}")
        if len(windows) > 1:
            return _ask(f"Há {len(windows)} janelas chamadas {name}. Qual delas?")
        return None

    # 4. Pasta alterada em certo horario, dentro de outra ("a que foi alterada as 16:30")
    at = _AT_TIME.search(n)
    inside = _IN_FOLDER.search(n)
    if at and inside:
        parent = _locate_folder(inside.group("parent"), n, session)
        if not parent:
            return None
        hour, minute = int(at.group("h")), int(at.group("m")) if at.group("m") else None
        hits, listing = _by_time(parent, hour, minute)
        if len(hits) == 1:
            return _open(task, hits[0], f"abrir a pasta {os.path.basename(hits[0])}")
        stamp = f"{hour:02d}:{minute:02d}" if minute is not None else f"{hour}h"
        return _ask(_options(f"Nenhuma pasta única alterada às {stamp} em {os.path.basename(parent)}.", listing)
                    if not hits else f"Mais de uma pasta foi alterada às {stamp}. Qual: "
                    + ", ".join(os.path.basename(h) for h in hits) + "?")

    # 5. Subpasta ("a pasta docs dentro da pasta trabalhos na area de trabalho")
    nested = _NESTED.search(n)
    if nested:
        parent = _locate_folder(nested.group("parent"), n, session)
        if not parent:
            return None
        child, options = _match_child(parent, nested.group("child"))
        if child:
            return _open(task, child, f"abrir a pasta {os.path.basename(child)}")
        return _ask(_options(f"Não achei a pasta {nested.group('child').strip()} dentro de {os.path.basename(parent)}.",
                             options))

    # 6. "A segunda pasta dentro de X": a ordem que a pessoa ve depende da tela, entao pergunta
    if _ORDINAL.search(n) and inside:
        parent = _locate_folder(inside.group("parent"), n, session)
        if parent:
            return _ask(_options(f"A ordem das pastas depende de como estão organizadas na tela. Qual pasta dentro de "
                                 f"{os.path.basename(parent)}?", [e.name for e in _children(parent)][:MAX_OPTIONS]))
    return None


def existing_steps(existing: dict) -> list:
    """Passos do plano, conferidos de novo aqui: o parametro pode vir de outro lugar que nao este modulo."""
    action = existing.get("action")
    if action == "open_path":
        path = str(existing.get("path") or "")
        if not os.path.exists(path) or os.path.splitext(path)[1].lower() in EXECUTABLE_EXT:
            return []
        return [{"step": 1, "action": "open_path", "params": {"path": path},
                 "description": f"Abrir {os.path.basename(path) or path}", "agent": "DESKTOP"}]
    if action == "focus_window" and isinstance(existing.get("title"), str) and existing["title"]:
        params = {"title": existing["title"]}
        if existing.get("hwnd"):
            params["hwnd"] = existing["hwnd"]
        return [{"step": 1, "action": "focus_window", "params": params,
                 "description": f"Trazer {existing['title'][:50]} para a frente", "agent": "DESKTOP"}]
    return []
