"""
Observer — depois de cada etapa, anota na sessao o que ficou aberto.

E isso que permite o proximo pedido dizer "esse segundo video" ou
"aquela musica de baixo": a sessao guarda a aba/janela/projeto e os
itens que estavam visiveis. Falhar aqui nunca derruba a execucao.
"""

from __future__ import annotations

import os
from typing import Optional

from core.session import Session

OUR_TITLES = ("ai farm agent",)


def _visible_items(snap, limit: int = 25) -> list[str]:
    """Itens da area principal, numerados na ordem de leitura (sem anuncios)."""
    items, n = [], 0
    for e in snap.elements:
        if e.region != "principal" or e.ad or not e.name:
            continue
        if e.role not in ("link", "botao", "item", "linha", "aba"):
            continue
        n += 1
        items.append(f"{n}. {e.role} \"{e.name[:80]}\"")
        if n >= limit:
            break
    return items


def _domain(url: str) -> str:
    from urllib.parse import urlparse
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def observe_web(session: Session, expect_url: str = "") -> bool:
    """Anota a aba em foco. Com expect_url, so anota se for o MESMO site que o
    pedido abriu: nunca adotar uma aba do usuario (outro navegador em primeiro plano)."""
    from core import browser_uia as B
    win = B.browser_window()
    if win is None:
        return False
    snap = B.snapshot(win)
    if snap is None or not snap.url or snap.url.startswith(("about:", "edge://", "chrome://")):
        return False
    want = _domain(expect_url)
    if want and not ("google." in want and "google." in _domain(snap.url)) \
            and want not in _domain(snap.url) and _domain(snap.url) not in want:
        return False
    session.remember_web(win.handle, snap.url, snap.title, _visible_items(snap))
    return True


# Titulo esperado da janela por app (para nao adotar a janela errada)
APP_TITLES = {
    "notepad": ("bloco de notas", "notepad"), "bloco de notas": ("bloco de notas", "notepad"),
    "calculadora": ("calculadora", "calculator"), "word": ("word",), "excel": ("excel",),
    "vscode": ("visual studio code",), "paint": ("paint",), "explorer": ("explorador", "explorer"),
    "configuracoes": ("configura", "settings"), "powerpoint": ("powerpoint",),
    "obsidian": ("obsidian",), "terminal": ("prompt", "terminal", "powershell"),
    "spotify": ("spotify",), "teams": ("teams",), "whatsapp": ("whatsapp",), "outlook": ("outlook",),
}


def _foreground() -> Optional[tuple[int, str]]:
    try:
        import pygetwindow as gw
        w = gw.getActiveWindow()
        if w and w.title and not any(t in w.title.lower() for t in OUR_TITLES):
            return w._hWnd, w.title
    except Exception:
        pass
    return None


def _app_window(key: str) -> Optional[tuple[int, str]]:
    """Janela do app pedido: a da frente se o titulo bate; senao a mais acima que bate."""
    hints = APP_TITLES.get(key)
    fg = _foreground()
    if not hints:
        return fg
    if fg and any(h in fg[1].lower() for h in hints):
        return fg
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():          # ordem Z: de cima para baixo
            if w.visible and w.title and any(h in w.title.lower() for h in hints):
                return w._hWnd, w.title
    except Exception:
        pass
    return None


def observe(agent: str, params: dict, extracted: dict, session: Session) -> str:
    """Atualiza a sessao conforme o agente que acabou de rodar. Devolve um resumo para log."""
    try:
        cont = params.get("continue") or {}
        if agent == "WEB":
            expect = "" if cont.get("type") == "web" else (extracted.get("url") or params.get("url") or "")
            return "web: aba anotada" if observe_web(session, expect) else "web: aba não confirmada (não anotada)"

        if agent == "DESKTOP":
            from core.lexicon import get_lexicon
            key = cont.get("key") or get_lexicon().app_key(params.get("app") or "")
            fg = _foreground()
            if cont.get("type") == "app" and cont.get("hwnd"):
                hwnd, title = cont["hwnd"], (fg[1] if fg and fg[0] == cont["hwnd"] else cont.get("title", ""))
            else:
                win = _app_window(key)
                if not win:
                    return f"app '{key}': janela não confirmada (não anotada)"
                hwnd, title = win
            from core.browser_uia import is_browser_title
            if is_browser_title(title):
                observe_web(session)
                return "desktop abriu o navegador: aba anotada"
            text = (params.get("text") or params.get("message") or "").strip()
            prev = session.apps.get(key or "app", {}).get("last_text", "") if cont else ""
            if not key:
                from core.lexicon import get_lexicon
                key = get_lexicon().app_key(title.split(" - ")[-1]) or title.split(" - ")[-1]
            session.remember_app(key, hwnd, title,
                                 (prev + "\n" + text).strip() if text else prev)
            return f"app: {title[:40]}"

        if agent == "CODE":
            folder = cont.get("folder") if cont.get("type") == "code" else None
            folder = folder or extracted.get("folder")
            if not folder and extracted.get("primary_path"):
                folder = os.path.dirname(extracted["primary_path"])
            if folder and os.path.isdir(folder):
                files = extracted.get("files") or [os.path.join(folder, f) for f in os.listdir(folder)
                                                   if not f.startswith(".")]
                session.remember_code(folder, files)
                return f"code: {folder}"
            return ""

        if agent in ("FILE", "DATA"):
            path = extracted.get("folder") or extracted.get("primary_path")
            if path:
                session.remember_folder(path)
                return f"pasta: {path}"
    except Exception as e:
        return f"observer falhou: {e}"
    return ""
