"""
BrowserUIA — le e clica links no navegador do PROPRIO usuario (Edge/Chrome)
pela arvore de acessibilidade do Windows (UI Automation), sem Playwright.

Por que: sem Playwright o agente so enxergava pixels (print + Vision) e
errava links pequenos. Pelo UIA cada link vem com texto, URL e retangulo,
e o clique e feito por Invoke (sem adivinhar coordenada). Funciona no
navegador ja logado (Gmail, GitHub...).

A escolha do link (`pick`) e pura e testavel sem navegador.
Tudo aqui falha em silencio (retorna None / ok=False) para o chamador
cair na visao.
"""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

BROWSER_TITLES = ("microsoft edge", "microsoft​ edge", "google chrome", "brave", "opera", "mozilla firefox", "vivaldi")

_ORDINALS = {
    "primeir": 0, "1o": 0, "1º": 0, "segund": 1, "2o": 1, "2º": 1,
    "terceir": 2, "3o": 2, "3º": 2, "quart": 3, "quint": 4,
}
_STOP = {
    "clique", "clicar", "clica", "abra", "abrir", "abre", "entre", "entrar", "acesse", "acessar",
    "no", "na", "nos", "nas", "em", "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "link", "links", "item", "itens", "lista", "resultado", "resultados", "pagina", "site",
    "navegador", "dentro", "botao", "primeiro", "primeira", "segundo", "segunda", "terceiro",
    "terceira", "ultimo", "ultima", "pesquisa", "busca", "que", "aparece", "aparecer", "para", "pra",
    "e", "ou", "com", "sobre", "meu", "minha", "aba", "guia", "tela",
}
_MAIL_WORDS = ("email", "e-mail", "mensagem", "conversa", "mail")
# Hosts de busca: resultados sao links para OUTROS dominios
_SEARCH_HOSTS = ("google.", "bing.com", "duckduckgo.com", "search.yahoo")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


@dataclass
class Link:
    name: str
    url: str
    rect: tuple            # (left, top, right, bottom) em pixels fisicos
    kind: str = "link"     # link | row
    elem: object = field(default=None, repr=False, compare=False)


# ─── Escolha do alvo (pura) ─────────────────────────────────────────

def parse_target(desc: str, page_title: str = "", page_url: str = "") -> dict:
    """Extrai do pedido: ordinal, palavras-chave, texto entre aspas e se e e-mail."""
    d = _norm(re.sub(r"\(dentro da pagina do navegador\)", "", desc or "", flags=re.I))
    quoted = re.findall(r"[\"“']([^\"”']{2,60})[\"”']", desc or "")
    index = None
    if re.search(r"\bultim[oa]\b", d):
        index = -1
    else:
        for k, v in _ORDINALS.items():
            if re.search(rf"\b{re.escape(k)}", d):
                index = v
                break
    mail = any(w in d for w in _MAIL_WORDS)
    host = _host(page_url)
    # Numa pagina de busca o titulo repete a pesquisa: nao serve de contexto
    context = host if any(s in host for s in _SEARCH_HOSTS) else _norm(page_title) + " " + host
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9.\-]{1,}", d)
             if w not in _STOP and not w.isdigit()]
    # "primeiro link do gmail" dentro do Gmail: "gmail" e a pagina, nao o alvo
    words = [w for w in words if w not in context and w not in _MAIL_WORDS]
    return {"index": index, "words": words, "quoted": [_norm(q) for q in quoted], "mail": mail}


def _is_result(link: Link, page_url: str, doc_top: int, doc_h: int) -> bool:
    """Heuristica de 'resultado': fora do cabecalho e fora da navegacao do proprio site."""
    if not link.name or len(link.name.strip()) < 3:
        return False
    if link.rect[1] < doc_top + int(doc_h * 0.10):
        return False
    url, host, page_host = link.url, _host(link.url), _host(page_url)
    if url.startswith(("javascript:", "#")) or url.rstrip("/") == page_url.rstrip("/"):
        return False
    if any(s in page_host for s in _SEARCH_HOSTS):
        return bool(host) and not any(s in host for s in _SEARCH_HOSTS) and "googleusercontent" not in host
    if "youtube.com" in page_host:
        return "/watch" in url or "/shorts/" in url
    if "github.com" in page_host and "/search" in page_url:
        return bool(re.match(r"https://github\.com/[^/]+/[^/?#]+/?$", url))
    return True


def pick(links: list[Link], desc: str, page_title: str = "", page_url: str = "",
         doc_rect: tuple = (0, 0, 1920, 1080)) -> Optional[Link]:
    """Escolhe o link pedido. None = nao ha certeza (chamador cai na visao)."""
    if not links:
        return None
    t = parse_target(desc, page_title, page_url)
    doc_top, doc_h = doc_rect[1], max(1, doc_rect[3] - doc_rect[1])
    ordered = sorted(links, key=lambda l: (l.rect[1], l.rect[0]))

    if t["mail"] or ("mail.google" in page_url and t["index"] is not None and not t["words"]):
        rows = [l for l in ordered if l.kind == "row" and l.name.strip()]
        if rows:
            i = t["index"] or 0
            return rows[i] if -len(rows) <= i < len(rows) else None

    cands = [l for l in ordered if l.kind == "link"]
    if t["quoted"] or t["words"]:
        scored = []
        for l in cands:
            hay = _norm(l.name) + " " + _host(l.url) + " " + _norm(l.url)
            if t["quoted"] and not all(q in _norm(l.name) for q in t["quoted"]):
                continue
            score = sum(1 for w in t["words"] if w in hay)
            if t["quoted"] or score:
                scored.append((score, l))
        if scored:
            best = max(s for s, _ in scored)
            top = [l for s, l in scored if s == best]
            i = t["index"] or 0
            return top[i] if -len(top) <= i < len(top) else None
        return None   # pediu algo especifico que nao esta na pagina

    if t["index"] is not None:
        results = [l for l in cands if _is_result(l, page_url, doc_top, doc_h)]
        i = t["index"]
        return results[i] if -len(results) <= i < len(results) else None
    return None


# ─── Acesso ao navegador (Windows) ──────────────────────────────────

def _desktop():
    from pywinauto import Desktop
    return Desktop(backend="uia")


def is_browser_title(title: str) -> bool:
    t = (title or "").lower()
    return any(b in t for b in BROWSER_TITLES)


def browser_window():
    """Janela de navegador em primeiro plano; senao a mais acima na pilha."""
    try:
        import pygetwindow as gw
        act = gw.getActiveWindow()
        d = _desktop()
        if act and is_browser_title(act.title):
            return d.window(handle=act._hWnd).wrapper_object()
        for w in d.windows():   # ordem Z: de cima para baixo
            if w.is_visible() and not w.is_minimized() and is_browser_title(w.window_text()):
                return w
    except Exception:
        return None
    return None


def _wake(win) -> None:
    """Chrome so monta a arvore completa quando um leitor de tela pede."""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        found = []
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def cb(h, _):
            buf = ctypes.create_unicode_buffer(64)
            u.GetClassNameW(h, buf, 64)
            if buf.value == "Chrome_RenderWidgetHostHWND":
                found.append(h)
            return True
        u.EnumChildWindows(win.handle, proc(cb), 0)
        for h in found:
            u.SendMessageW(h, 0x003D, 0, -4)   # WM_GETOBJECT, OBJID_CLIENT
    except Exception:
        pass


def _document(win, wait: float = 4.0):
    end = time.time() + wait
    while True:
        try:
            docs = [d for d in win.descendants(control_type="Document")
                    if d.rectangle().width() > 200]
            if docs:
                return max(docs, key=lambda d: d.rectangle().width() * d.rectangle().height())
        except Exception:
            pass
        if time.time() > end:
            return None
        _wake(win)
        time.sleep(0.5)


def _value(elem) -> str:
    try:
        return elem.iface_value.CurrentValue or ""
    except Exception:
        return ""


def current_url(win) -> str:
    """URL da barra de endereco: primeiro Edit da barra de ferramentas cujo valor parece URL.
    (No Edge o nome do campo e a propria URL; no Chrome e 'Barra de enderecos'.)"""
    try:
        wr = win.rectangle()
        for e in win.descendants(control_type="Edit"):
            if e.rectangle().top > wr.top + 160:
                continue   # campo dentro da pagina, nao da barra
            v = (_value(e) or "").strip()
            if re.match(r"^(https?|file|edge|chrome)://", v):
                return v
            if re.match(r"^[\w\-]+(\.[\w\-]+)+(/|$)", v):
                return "https://" + v
    except Exception:
        pass
    return ""


_BLOCK_MARKS = ("trafego incomum", "unusual traffic", "nao sou um robo", "i'm not a robot",
                "verify you are human", "verifique se voce e humano", "captcha")


def blocked_reason(url: str, text: str = "") -> str:
    """Pagina de verificacao anti-robo: o agente NAO tenta resolver, avisa o usuario."""
    u, t = (url or "").lower(), _norm(text)[:3000]
    if "google.com/sorry" in u or "/recaptcha/" in u or any(m in t for m in _BLOCK_MARKS):
        return ("⛔ O site pediu verificação humana (CAPTCHA / tráfego incomum). "
                "Resolva no navegador e peça de novo.")
    return ""


def page_title(win) -> str:
    t = win.window_text() if win else ""
    return re.split(r" [-–—] (?:[^-–—]*[-–—] )?(?:Microsoft|Google Chrome|Brave|Opera|Mozilla|Vivaldi)", t)[0].strip()


def links(win, limit: int = 400, rows: bool = False) -> tuple[list[Link], tuple]:
    """Links visiveis do documento ativo (+ linhas de lista/tabela se rows=True)."""
    doc = _document(win)
    if doc is None:
        return [], (0, 0, 0, 0)
    r = doc.rectangle()
    drect = (r.left, r.top, r.right, r.bottom)
    out: list[Link] = []
    types = ["Hyperlink"] + (["DataItem", "ListItem"] if rows else [])
    for ct in types:
        try:
            elems = doc.descendants(control_type=ct)
        except Exception:
            continue
        for e in elems[:limit]:
            try:
                er = e.rectangle()
            except Exception:
                continue
            if er.width() <= 0 or er.height() <= 0 or er.top < r.top or er.bottom > r.bottom:
                continue   # fora da area visivel da pagina
            name = (e.window_text() or "").strip()
            out.append(Link(name=name[:200], url=_value(e) if ct == "Hyperlink" else "",
                            rect=(er.left, er.top, er.right, er.bottom),
                            kind="link" if ct == "Hyperlink" else "row", elem=e))
    return out, drect


# Controles com que da para interagir, e o nome curto que o piloto ve
INTERACTIVE = {
    "Hyperlink": "link", "Button": "botao", "SplitButton": "botao", "Edit": "campo",
    "ComboBox": "lista", "CheckBox": "caixa", "RadioButton": "opcao", "MenuItem": "menu",
    "TabItem": "aba", "ListItem": "item", "DataItem": "linha", "TreeItem": "item",
}


REGIONS = ("cabecalho", "principal", "lateral esquerda", "lateral direita")
_AD_URL = re.compile(r"googleadservices|doubleclick|/aclk\?|/pagead/|adservice|[?&](?:ad|gclid)=|click\d*\.mercadolivre", re.I)
_AD_NAME = re.compile(r"\b(patrocinad[oa]|an[uú]ncio|sponsored|\bad\b)\b", re.I)


def region_of(rect: tuple, doc: tuple) -> str:
    """Regiao pela geometria: menus e trilhos laterais nao se misturam com o conteudo."""
    left, top, right, bottom = doc
    w, h = max(1, right - left), max(1, bottom - top)
    if rect[3] <= top + min(90, int(h * 0.11)):
        return "cabecalho"
    if rect[2] <= left + int(w * 0.20):
        return "lateral esquerda"
    if rect[0] >= left + int(w * 0.72):
        return "lateral direita"
    return "principal"


@dataclass
class Element:
    id: int
    role: str
    name: str
    url: str = ""
    value: str = ""
    rect: tuple = (0, 0, 0, 0)
    elem: object = field(default=None, repr=False, compare=False)
    region: str = "principal"
    ad: bool = False

    def line(self) -> str:
        s = f"[{self.id}] {self.role} \"{self.name[:90]}\""
        if self.ad:
            s += " [ANUNCIO]"
        if self.url:
            s += f" -> {self.url[:90]}"
        if self.value and self.role in ("campo", "lista"):
            s += f" = \"{self.value[:40]}\""
        return s


@dataclass
class Snapshot:
    title: str
    url: str
    elements: list
    text: str
    below: int              # elementos interativos abaixo da area visivel
    blocked: str = ""
    win: object = field(default=None, repr=False)
    main_texts: list = field(default_factory=list)   # [(top, left, texto)] da regiao principal

    def render(self, max_text: int = 1800) -> str:
        """Regiao principal em ORDEM DE LEITURA, com os textos entre os elementos:
        preco, data e 'Patrocinado' ficam junto do card a que pertencem."""
        lines = [f"TITULO: {self.title}", f"URL: {self.url}",
                 "PAGINA VISIVEL por regiao (elementos numerados = clicaveis; linhas com '·' = texto):"]
        for region in REGIONS:
            group = [(e.rect[1], e.rect[0], e.line()) for e in self.elements if e.region == region]
            if region == "principal":
                names = {e.name for e in self.elements}
                budget, texts = max_text, []
                for top, left, t in self.main_texts:
                    if t in names or budget <= 0:
                        continue
                    t = t[:160]
                    budget -= len(t)
                    texts.append((top, left, "   · " + t))
                group = sorted(group + texts, key=lambda x: (x[0], x[1]))
            if group:
                lines.append(f"-- {region.upper()} --")
                lines += [g[2] for g in group]
        if self.below:
            lines.append("(a pagina continua abaixo: use scroll para ver mais)")
        if self.text and not self.main_texts:
            lines.append("TEXTO DA PAGINA (trecho):\n" + self.text[:max_text])
        return "\n".join(lines)


def _find_visible(doc):
    """Uma unica consulta UIA em lote: controles interativos + textos NAO fora da tela.
    Percorrer a arvore elemento a elemento levava ~6 s na Wikipedia; assim ~0,3 s."""
    from pywinauto.uia_defines import IUIA
    u = IUIA()
    iuia, dll = u.iuia, u.UIA_dll
    cr = iuia.CreateCacheRequest()
    for pid in (dll.UIA_NamePropertyId, dll.UIA_ControlTypePropertyId,
                dll.UIA_BoundingRectanglePropertyId, dll.UIA_ValueValuePropertyId):
        cr.AddProperty(pid)
    ids = {getattr(dll, f"UIA_{ct}ControlTypeId"): ct for ct in list(INTERACTIVE) + ["Text", "Image"]}
    kinds = iuia.CreateOrConditionFromArray(
        [iuia.CreatePropertyCondition(dll.UIA_ControlTypePropertyId, i) for i in ids])
    onscreen = iuia.CreatePropertyCondition(dll.UIA_IsOffscreenPropertyId, False)
    arr = doc.element_info.element.FindAllBuildCache(
        dll.TreeScope_Descendants, iuia.CreateAndCondition(kinds, onscreen), cr)
    out = []
    for k in range(arr.Length):
        e = arr.GetElement(k)
        try:
            rc = e.CachedBoundingRectangle
            try:
                val = e.GetCachedPropertyValue(dll.UIA_ValueValuePropertyId) or ""
            except Exception:
                val = ""
            out.append((ids.get(e.CachedControlType, ""), e.CachedName or "",
                        str(val) if isinstance(val, str) else "",
                        (rc.left, rc.top, rc.right, rc.bottom), e))
        except Exception:
            continue
    return out


def _scroll_left(doc) -> bool:
    """Ainda ha pagina abaixo? (ScrollPattern do documento)."""
    try:
        sp = doc.iface_scroll
        return sp.CurrentVerticallyScrollable and sp.CurrentVerticalScrollPercent < 99
    except Exception:
        return False


def wrap(raw_elem):
    """Elemento UIA cru -> wrapper pywinauto (invoke, click_input, set_focus...)."""
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto.uia_element_info import UIAElementInfo
    return UIAWrapper(UIAElementInfo(raw_elem))


def snapshot(win=None, max_elems: int = 160, text_chars: int = 1500) -> Optional[Snapshot]:
    """Retrato numerado da pagina: o que da para clicar/digitar + trecho do texto.
    Os ids valem so para ESTE retrato (a pagina muda a cada acao)."""
    win = win or browser_window()
    if win is None:
        return None
    doc = _document(win)
    url = current_url(win)
    title = page_title(win)
    if doc is None:
        return Snapshot(title, url, [], "", 0, blocked_reason(url, title), win)
    r = doc.rectangle()
    try:
        found = _find_visible(doc)
    except Exception:
        found = []
    drect = (r.left, r.top, r.right, r.bottom)
    items, texts, main_texts, seen = [], [], [], set()
    for ct, name, value, rect, raw in found:
        name = re.sub(r"\s+", " ", name).strip()
        if ct in ("Text", "Image"):   # imagem com legenda: preco, nota, alt do produto
            if name and len(texts) < 400:
                texts.append(name)
                if region_of(rect, drect) == "principal" and r.top <= rect[1] < r.bottom:
                    main_texts.append((rect[1], rect[0], name))
            continue
        role = INTERACTIVE.get(ct)
        if not role or rect[2] - rect[0] <= 1 or rect[3] - rect[1] <= 1:
            continue
        if rect[3] <= r.top or rect[1] >= r.bottom or rect[2] <= r.left or rect[0] >= r.right:
            continue
        link = value if ct == "Hyperlink" else ""
        val = value if ct in ("Edit", "ComboBox") else ""
        if not name and not link and ct not in ("Edit", "ComboBox"):
            continue
        key = (name, link) if role in ("link", "item", "linha") else (role, name, link)
        if key in seen:
            continue
        seen.add(key)
        items.append((rect[1], rect[0], role, name, link, val, rect, raw))
    # Um item de lista que so embrulha um link/botao de mesmo nome e ruido
    other_names = {i[3] for i in items if i[2] != "item"}
    items = [i for i in items if not (i[2] == "item" and i[3] in other_names)]
    order = {g: k for k, g in enumerate(REGIONS)}
    # Numeracao segue a leitura: regiao, depois de cima para baixo -> "segundo
    # resultado" e o segundo da regiao principal, nao o segundo item da tela.
    items.sort(key=lambda x: (order[region_of(x[6], drect)], x[0], x[1]))
    elements = [Element(n + 1, role, name, link, val, rect, raw, region_of(rect, drect),
                        bool(_AD_URL.search(link) or _AD_NAME.search(name)))
                for n, (_, _, role, name, link, val, rect, raw) in enumerate(items[:max_elems])]
    below = max(0, len(items) - max_elems) + (1 if _scroll_left(doc) else 0)
    text = "\n".join(texts)[:text_chars]
    return Snapshot(title, url, elements, text, below,
                    blocked_reason(url, title + " " + text[:600]), win, main_texts[:250])


def read(max_chars: int = 1500, max_links: int = 15) -> dict:
    """Titulo, URL, texto visivel e principais links da pagina aberta."""
    win = browser_window()
    if win is None:
        return {"ok": False, "error": "nenhum navegador aberto"}
    doc = _document(win)
    text = ""
    if doc is not None:
        try:
            text = doc.iface_text.DocumentRange.GetText(max_chars * 2)
        except Exception:
            try:
                text = "\n".join(t.window_text() for t in doc.descendants(control_type="Text")[:200])
            except Exception:
                text = ""
    found, _ = links(win)
    seen, top = set(), []
    for l in found:
        if l.name and l.url.startswith("http") and l.url not in seen:
            seen.add(l.url)
            top.append({"name": l.name[:80], "url": l.url})
        if len(top) >= max_links:
            break
    url = current_url(win)
    return {"ok": True, "title": page_title(win), "url": url,
            "text": re.sub(r"\n{3,}", "\n\n", text or "").strip()[:max_chars], "links": top,
            "blocked": blocked_reason(url, text)}


def _signature(win) -> tuple:
    try:
        return (win.window_text(), current_url(win))
    except Exception:
        return ("", "")


def wait_change(win, before: tuple, timeout: float = 5.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(0.4)
        top = browser_window() or win
        if _signature(top) != before:
            return True
    return False


def click(desc: str) -> dict:
    """Acha o link pedido e clica por Invoke; confere se a pagina mudou."""
    win = browser_window()
    if win is None:
        return {"ok": False, "error": "nenhum navegador aberto"}
    try:
        win.set_focus()
    except Exception:
        pass
    url = current_url(win)
    title = page_title(win)
    blocked = blocked_reason(url, title)
    if blocked:
        return {"ok": False, "blocked": True, "error": blocked}
    t = parse_target(desc, title, url)
    found, drect = links(win, rows=t["mail"] or "mail.google" in url)
    target = pick(found, desc, title, url, drect)
    if target is None:
        if any("sorry/index" in l.url for l in found):
            return {"ok": False, "blocked": True, "error": blocked_reason("https://google.com/sorry")}
        return {"ok": False, "error": f"nenhum link corresponde a '{desc[:60]}' ({len(found)} links lidos)"}
    before = _signature(win)
    method = "invoke"
    try:
        if target.kind == "link":
            target.elem.invoke()
        else:
            raise RuntimeError("linha: clique direto")
    except Exception:
        method = "click"
        try:
            target.elem.click_input()
        except Exception as e:
            return {"ok": False, "error": f"falha ao clicar: {e}"}
    changed = wait_change(win, before)
    if not changed and method == "invoke":
        try:
            target.elem.click_input()
            method = "click"
            changed = wait_change(win, before, 3.0)
        except Exception:
            pass
    return {"ok": changed, "method": method, "name": target.name, "url": target.url,
            "error": "" if changed else "clique feito mas a pagina nao mudou"}
