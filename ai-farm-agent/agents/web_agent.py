"""
WebAgent v13 — Rotinas inteligentes + fallback browser nativo.
Sabe navegar como humano: Google, YouTube, sites, pesquisas.
Quando Playwright indisponível, abre no browser padrão do Windows.
"""

import json
import subprocess
from agents.base_agent import BaseAgent


# ═══════════════════════════════════════════════════════════════
#  ROTINAS WEB — passo a passo igual um humano faria
# ═══════════════════════════════════════════════════════════════

def _s(step, action, params, desc):
    return {"step": step, "action": action, "params": params, "description": desc, "agent": "WEB"}


def _detect_web_routine(task):
    """Detecta tarefas web conhecidas e retorna rotina hardcoded."""
    t = task.lower().strip()

    # ── GOOGLE: pesquisar ──
    for kw in ["pesquise no google", "pesquisa no google", "busque no google",
               "procure no google", "google sobre", "google o que"]:
        if kw in t:
            query = t.split(kw)[-1].strip().strip('"').strip("'")
            if not query:
                for w in ["sobre ", "o que é ", "o que e "]:
                    if w in t:
                        query = t.split(w)[-1].strip()
                        break
            return _google_search(query or "pesquisa")

    # ── YOUTUBE: pesquisar vídeos ──
    for kw in ["youtube e pesquise", "youtube e procure", "youtube e busque",
               "pesquise no youtube", "procure no youtube", "youtube sobre",
               "procure videos sobre", "procure vídeos sobre"]:
        if kw in t:
            query = t.split(kw)[-1].strip().strip('"').strip("'")
            if not query:
                for w in ["sobre ", "de ", "por "]:
                    if w in t:
                        query = t.split(w)[-1].strip()
                        break
            return _youtube_search(query or "videos")

    # YouTube: só abrir
    if "youtube" in t and ("abr" in t or "entr" in t or "acess" in t):
        for kw in ["pesquis", "procur", "busc"]:
            if kw in t:
                # Extrai o que pesquisar
                for w in ["pesquise ", "procure ", "busque ", "sobre ", "de "]:
                    if w in t:
                        query = t.split(w)[-1].strip()
                        return _youtube_search(query)
        return _youtube_open()

    # ── GOOGLE: só abrir ──
    if "google" in t and ("abr" in t or "entr" in t or "acess" in t):
        return _google_open()

    # ── ABRIR URL DIRETA ──
    for prefix in ["http://", "https://", "www."]:
        if prefix in t:
            import re
            urls = re.findall(r'https?://[^\s]+|www\.[^\s]+', t)
            if urls:
                url = urls[0]
                if not url.startswith("http"):
                    url = "https://" + url
                return _open_url(url)

    # ── ABRIR SITES CONHECIDOS ──
    sites = {
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "whatsapp web": "https://web.whatsapp.com",
        "twitter": "https://x.com",
        "x.com": "https://x.com",
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "linkedin": "https://linkedin.com",
        "reddit": "https://reddit.com",
        "spotify": "https://open.spotify.com",
        "netflix": "https://netflix.com",
        "amazon": "https://amazon.com.br",
        "mercado livre": "https://mercadolivre.com.br",
        "chatgpt": "https://chat.openai.com",
        "claude": "https://claude.ai",
        "stackoverflow": "https://stackoverflow.com",
        "wikipedia": "https://pt.wikipedia.org",
    }
    for name, url in sites.items():
        if name in t:
            return _open_url(url)

    # ── NOVA GUIA / NOVA ABA ──
    if "nova guia" in t or "nova aba" in t or "new tab" in t:
        # Verifica se tem algo para fazer na nova guia
        for kw in ["pesquis", "procur", "busc"]:
            if kw in t:
                if "youtube" in t:
                    query = t.split(kw)[-1].strip().replace("no youtube", "").replace("youtube", "").strip()
                    return _youtube_search_new_tab(query or "videos")
                if "google" in t:
                    query = t.split(kw)[-1].strip().replace("no google", "").replace("google", "").strip()
                    return _google_search_new_tab(query or "pesquisa")
        return _new_tab()

    # ── PESQUISA GENÉRICA (sem especificar onde) ──
    for kw in ["pesquise ", "pesquisa ", "procure ", "busque ", "busca "]:
        if t.startswith(kw) or f" {kw}" in t:
            query = t.split(kw)[-1].strip()
            return _google_search(query)

    return None


# ═══ ROTINAS ESPECÍFICAS ═══

def _google_open():
    return [
        _s(1, "web_goto", {"url": "https://www.google.com"}, "Abrir Google"),
        _s(2, "wait", {"seconds": 1.5}, "Aguardar carregamento"),
    ]

def _google_search(query):
    return [
        _s(1, "web_goto", {"url": "https://www.google.com"}, "Abrir Google"),
        _s(2, "wait", {"seconds": 1.5}, "Aguardar carregamento"),
        _s(3, "web_type", {"field": "textarea[name=q]", "text": query}, f"Digitar: {query[:40]}"),
        _s(4, "web_key", {"key": "Enter"}, "Pesquisar"),
        _s(5, "wait", {"seconds": 2}, "Aguardar resultados"),
    ]

def _google_search_new_tab(query):
    return [
        _s(1, "web_new_tab", {"url": "https://www.google.com"}, "Nova guia — Google"),
        _s(2, "wait", {"seconds": 1.5}, "Aguardar carregamento"),
        _s(3, "web_type", {"field": "textarea[name=q]", "text": query}, f"Digitar: {query[:40]}"),
        _s(4, "web_key", {"key": "Enter"}, "Pesquisar"),
        _s(5, "wait", {"seconds": 2}, "Aguardar resultados"),
    ]

def _youtube_open():
    return [
        _s(1, "web_goto", {"url": "https://www.youtube.com"}, "Abrir YouTube"),
        _s(2, "wait", {"seconds": 2}, "Aguardar carregamento"),
    ]

def _youtube_search(query):
    return [
        _s(1, "web_goto", {"url": "https://www.youtube.com"}, "Abrir YouTube"),
        _s(2, "wait", {"seconds": 2}, "Aguardar carregamento"),
        _s(3, "web_type", {"field": "input#search", "text": query}, f"Digitar: {query[:40]}"),
        _s(4, "web_key", {"key": "Enter"}, "Pesquisar"),
        _s(5, "wait", {"seconds": 2}, "Aguardar resultados"),
    ]

def _youtube_search_new_tab(query):
    return [
        _s(1, "web_new_tab", {"url": "https://www.youtube.com"}, "Nova guia — YouTube"),
        _s(2, "wait", {"seconds": 2}, "Aguardar carregamento"),
        _s(3, "web_type", {"field": "input#search", "text": query}, f"Digitar: {query[:40]}"),
        _s(4, "web_key", {"key": "Enter"}, "Pesquisar"),
        _s(5, "wait", {"seconds": 2}, "Aguardar resultados"),
    ]

def _open_url(url):
    return [
        _s(1, "web_goto", {"url": url}, f"Abrir {url[:50]}"),
        _s(2, "wait", {"seconds": 2}, "Aguardar carregamento"),
    ]

def _new_tab():
    return [
        _s(1, "web_new_tab", {"url": "about:blank"}, "Abrir nova guia"),
        _s(2, "wait", {"seconds": 1}, "Aguardar"),
    ]


# ═══════════════════════════════════════════════════════════════
#  FALLBACK: abre no browser nativo do Windows
# ═══════════════════════════════════════════════════════════════

def _native_browser_fallback(steps):
    """Converte steps de Playwright para abrir no browser padrão do Windows."""
    native_steps = []
    n = 0
    for step in steps:
        action = step.get("action", "")
        params = step.get("params", {})

        if action == "web_goto":
            n += 1
            url = params.get("url", "")
            native_steps.append(_s(n, "run_python", {
                "code": f'import subprocess; subprocess.Popen(\'start "" "{url}"\', shell=True); print("Aberto: {url[:50]}")',
                "description": f"Abrir {url[:50]} no browser padrão"
            }, f"Abrir {url[:50]}"))
        elif action == "web_new_tab":
            n += 1
            url = params.get("url", "about:blank")
            if url and url != "about:blank":
                native_steps.append(_s(n, "run_python", {
                    "code": f'import subprocess; subprocess.Popen(\'start "" "{url}"\', shell=True); print("Nova guia: {url[:50]}")',
                    "description": f"Nova guia: {url[:50]}"
                }, f"Nova guia: {url[:50]}"))
            else:
                native_steps.append(_s(n, "hotkey", {"keys": ["ctrl", "t"]}, "Nova guia (Ctrl+T)"))
        elif action == "wait":
            n += 1
            native_steps.append(step.copy())
            native_steps[-1]["step"] = n
        elif action == "web_type":
            n += 1
            text = params.get("text", "")
            # Espera extra para o browser carregar, depois digita
            native_steps.append(_s(n, "wait", {"seconds": 2}, "Aguardar browser"))
            n += 1
            native_steps.append(_s(n, "type_text", {"text": text}, f"Digitar: {text[:40]}"))
        elif action == "web_key":
            n += 1
            key = params.get("key", "Enter").lower()
            native_steps.append(_s(n, "hotkey", {"keys": [key]}, f"Pressionar {key}"))

    return native_steps if native_steps else None


# ═══════════════════════════════════════════════════════════════
#  WEB AGENT
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "Voce e o WEB AGENT — especialista em navegação web.\n"
    "ACOES: web_goto(url) | web_type(field, text) | web_click(target)\n"
    "       web_key(key) | web_read() | web_new_tab(url) | wait(seconds)\n\n"
    "REGRAS:\n"
    "- SEMPRE wait(1.5) apos web_goto\n"
    "- Para Google: field='textarea[name=q]'\n"
    "- Para YouTube: field='input#search'\n"
    "- Maximo 8 passos. JSON puro.\n\n"
    'FORMATO: {"steps":[{"step":1,"description":"...","action":"...","params":{}}]}'
)


class WebAgent(BaseAgent):
    """Agente web com rotinas inteligentes e fallback nativo."""

    def __init__(self):
        super().__init__(name="WEB", system_prompt=SYSTEM_PROMPT)
        self._playwright_available = None  # Cache do check

    def _check_playwright(self):
        """Verifica se Playwright está disponível (cacheia resultado)."""
        if self._playwright_available is None:
            try:
                import playwright
                self._playwright_available = True
            except ImportError:
                self._playwright_available = False
                self.logger.warning("Playwright não instalado — usando browser nativo")
        return self._playwright_available

    def plan(self, task, context=None):
        """Gera plano: rotina hardcoded → LLM → fallback nativo."""
        task_text = self._extract_task_text(task)

        # 1. Tenta rotina hardcoded ($0, sem LLM)
        routine = _detect_web_routine(task_text)
        if routine:
            has_pw = self._check_playwright()
            if has_pw:
                self.logger.info(f"Rotina web: {len(routine)} steps (Playwright)")
                return {"steps": routine, "agent": "WEB"}
            else:
                # Converte para browser nativo
                native = _native_browser_fallback(routine)
                if native:
                    self.logger.info(f"Rotina web: {len(native)} steps (browser nativo)")
                    return {"steps": native, "agent": "WEB"}

        # 2. LLM fallback
        self.logger.info("LLM fallback ($)")
        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)

        try:
            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=f"TAREFA: {task_text}{ctx}\nJSON puro.",
                max_tokens=2000,
            )
            from core.json_validator import safe_parse
            plan = safe_parse(raw, self.model)

            steps = plan.get("steps", [])
            for st in steps:
                st["agent"] = "WEB"

            # Se Playwright indisponível, converte steps do LLM também
            if not self._check_playwright() and steps:
                native = _native_browser_fallback(steps)
                if native:
                    self.logger.info(f"LLM → nativo: {len(native)} steps")
                    return {"steps": native, "agent": "WEB"}

            self.logger.info(f"Plano LLM: {len(steps)} steps")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": steps, "agent": "WEB"}

        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "WEB"}