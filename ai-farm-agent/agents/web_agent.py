"""
WebAgent v16 — Rotinas completas + clique em resultados.
- Rotina YouTube com clique no primeiro vídeo
- Rotina Google com clique no primeiro resultado (h3)
- web_read em pesquisas
- Seletores múltiplos robustos
"""

import json, re
from agents.base_agent import BaseAgent

YT_SEARCH = "input#search, ytd-searchbox input, input[name=search_query], [aria-label=Pesquisar], [aria-label=Search]"
G_SEARCH = "textarea[name=q], input[name=q], [aria-label=Pesquisar], [aria-label=Search]"


def _s(step, action, params, desc):
    return {"step": step, "action": action, "params": params, "description": desc, "agent": "WEB"}


def _detect_web_routine(task):
    t = task.lower().strip()

    click_first = any(kw in t for kw in ["clique no primeiro", "clica no primeiro", "abra o primeiro", "primeiro resultado", "primeiro video", "primeiro vídeo"])

    for kw in ["pesquise no google", "pesquisa no google", "busque no google", "procure no google", "google sobre"]:
        if kw in t:
            query = t.split(kw)[-1].strip().strip('"\'')
            for stop in [", depois", ", e depois", " e clique", ", clique"]:
                if stop in query: query = query.split(stop)[0].strip()
            if not query:
                for w in ["sobre ", "o que é ", "o que e "]:
                    if w in t: query = t.split(w)[-1].strip(); break
            if click_first:
                return _google_search_click(query or "pesquisa")
            return _google_search(query or "pesquisa")

    for kw in ["youtube e pesquise", "youtube e procure", "youtube e busque",
               "pesquise no youtube", "procure no youtube", "youtube sobre",
               "procure videos sobre", "procure vídeos sobre",
               "pesquise por videos", "pesquise por vídeos"]:
        if kw in t:
            query = t.split(kw)[-1].strip().strip('"\'')
            for stop in [", depois", ", e depois", " e clique", ", clique"]:
                if stop in query: query = query.split(stop)[0].strip()
            if click_first:
                return _youtube_search_click(query or "videos")
            return _youtube_search(query or "videos")

    if "youtube" in t:
        for kw in ["pesquis", "procur", "busc"]:
            if kw in t:
                for w in ["pesquise ", "pesquise por ", "procure ", "busque ", "sobre ", "de ", "por "]:
                    if w in t:
                        query = t.split(w)[-1].strip()
                        for stop in [", depois", ", e depois", " e clique", ", clique"]:
                            if stop in query: query = query.split(stop)[0].strip()
                        query = query.replace("no youtube", "").replace("youtube", "").strip()
                        if "nova guia" in t or "nova aba" in t:
                            return _youtube_search_new_tab(query)
                        if click_first:
                            return _youtube_search_click(query)
                        return _youtube_search(query)
        if "abr" in t or "entr" in t or "acess" in t:
            return _youtube_open()

    if "google" in t and ("abr" in t or "entr" in t): return _google_open()

    urls = re.findall(r'https?://[^\s,]+|www\.[^\s,]+', t)
    if urls:
        url = urls[0]
        if not url.startswith("http"): url = "https://" + url
        return _open_url(url)

    sites = {
        "github": "https://github.com", "gmail": "https://mail.google.com",
        "whatsapp web": "https://web.whatsapp.com", "twitter": "https://x.com",
        "instagram": "https://instagram.com", "facebook": "https://facebook.com",
        "linkedin": "https://linkedin.com", "reddit": "https://reddit.com",
        "netflix": "https://netflix.com", "amazon": "https://amazon.com.br",
        "mercado livre": "https://mercadolivre.com.br", "chatgpt": "https://chat.openai.com",
        "claude": "https://claude.ai", "stackoverflow": "https://stackoverflow.com",
        "wikipedia": "https://pt.wikipedia.org",
    }
    for name, url in sites.items():
        if name in t: return _open_url(url)

    if "nova guia" in t or "nova aba" in t:
        for kw in ["pesquis", "procur", "busc"]:
            if kw in t:
                if "youtube" in t:
                    for w in ["pesquise ", "pesquise por ", "procure ", "busque ", "por "]:
                        if w in t:
                            query = t.split(w)[-1].strip()
                            for stop in [", depois", " e clique"]:
                                if stop in query: query = query.split(stop)[0].strip()
                            return _youtube_search_new_tab(query)
                for w in ["pesquise ", "procure ", "busque ", "por ", "sobre "]:
                    if w in t: return _google_search_new_tab(t.split(w)[-1].strip())
        return _new_tab()

    for kw in ["pesquise ", "pesquisa ", "procure ", "busque "]:
        if t.startswith(kw) or f" {kw}" in t:
            return _google_search(t.split(kw)[-1].strip())

    return None


def _google_open():
    return [_s(1,"web_goto",{"url":"https://www.google.com"},"Abrir Google"), _s(2,"wait",{"seconds":1.5},"Aguardar")]

def _google_search(q):
    return [_s(1,"web_goto",{"url":"https://www.google.com"},"Abrir Google"), _s(2,"wait",{"seconds":1.5},"Aguardar"),
            _s(3,"web_type",{"field":G_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":2},"Aguardar"), _s(6,"web_read",{},"Ler conteudo")]

def _google_search_click(q):
    return [_s(1,"web_goto",{"url":"https://www.google.com"},"Abrir Google"), _s(2,"wait",{"seconds":1.5},"Aguardar"),
            _s(3,"web_type",{"field":G_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":2},"Aguardar"),
            _s(6,"web_click",{"target":"h3"},"Clicar primeiro resultado"), _s(7,"wait",{"seconds":2},"Aguardar"),
            _s(8,"web_read",{},"Ler")]

def _google_search_new_tab(q):
    return [_s(1,"web_new_tab",{"url":"https://www.google.com"},"Nova guia Google"), _s(2,"wait",{"seconds":1.5},"Aguardar"),
            _s(3,"web_type",{"field":G_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":2},"Aguardar"), _s(6,"web_read",{},"Ler")]

def _youtube_open():
    return [_s(1,"web_goto",{"url":"https://www.youtube.com"},"Abrir YouTube"), _s(2,"wait",{"seconds":2},"Aguardar")]

def _youtube_search(q):
    return [_s(1,"web_goto",{"url":"https://www.youtube.com"},"Abrir YouTube"), _s(2,"wait",{"seconds":2},"Aguardar"),
            _s(3,"web_type",{"field":YT_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":2},"Aguardar")]

def _youtube_search_click(q):
    return [_s(1,"web_goto",{"url":"https://www.youtube.com"},"Abrir YouTube"), _s(2,"wait",{"seconds":2},"Aguardar"),
            _s(3,"web_type",{"field":YT_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":3},"Aguardar"),
            _s(6,"web_click",{"target":"ytd-video-renderer a#video-title, ytd-video-renderer a, ytd-rich-item-renderer a"},"Clicar primeiro video"),
            _s(7,"wait",{"seconds":2},"Aguardar video")]

def _youtube_search_new_tab(q):
    return [_s(1,"web_new_tab",{"url":"https://www.youtube.com"},"Nova guia YouTube"), _s(2,"wait",{"seconds":2},"Aguardar"),
            _s(3,"web_type",{"field":YT_SEARCH,"text":q},f"Digitar: {q[:40]}"), _s(4,"web_key",{"key":"Enter"},"Pesquisar"),
            _s(5,"wait",{"seconds":2},"Aguardar")]

def _open_url(url):
    return [_s(1,"web_goto",{"url":url},f"Abrir {url[:50]}"), _s(2,"wait",{"seconds":2},"Aguardar")]

def _new_tab():
    return [_s(1,"web_new_tab",{"url":"about:blank"},"Nova guia"), _s(2,"wait",{"seconds":1},"Aguardar")]


def _native_fallback(steps):
    native = []; n = 0
    for step in steps:
        a = step.get("action",""); p = step.get("params",{})
        if a == "web_goto":
            n+=1; url = p.get("url","")
            native.append(_s(n,"run_python",{"code":f'import subprocess; subprocess.Popen(\'start "" "{url}"\', shell=True); print("OK")',"description":f"Abrir {url[:50]}"},f"Abrir {url[:50]}"))
        elif a == "web_new_tab":
            n+=1; url = p.get("url","about:blank")
            if url != "about:blank":
                native.append(_s(n,"run_python",{"code":f'import subprocess; subprocess.Popen(\'start "" "{url}"\', shell=True); print("OK")',"description":"Nova guia"},f"Nova guia"))
            else: native.append(_s(n,"hotkey",{"keys":["ctrl","t"]},"Nova guia"))
        elif a == "wait": n+=1; s=dict(step); s["step"]=n; native.append(s)
        elif a == "web_type":
            n+=1; native.append(_s(n,"wait",{"seconds":2},"Aguardar"))
            n+=1; native.append(_s(n,"type_text",{"text":p.get("text","")},f"Digitar: {p.get('text','')[:40]}"))
        elif a == "web_key":
            n+=1; native.append(_s(n,"hotkey",{"keys":[p.get("key","Enter").lower()]},f"{p.get('key','Enter')}"))
        elif a in ("web_read","web_click"): pass
    return native if native else None


SYSTEM_PROMPT = (
    "Voce e o WEB AGENT — especialista em navegacao web.\n"
    "ACOES: web_goto(url) | web_type(field, text) | web_click(target)\n"
    "       web_key(key) | web_read() | web_new_tab(url) | wait(seconds)\n\n"
    "SELETORES:\n"
    "- YouTube busca: 'input#search, ytd-searchbox input'\n"
    "- YouTube primeiro video: 'ytd-video-renderer a#video-title'\n"
    "- Google busca: 'textarea[name=q]'\n"
    "- Google primeiro resultado: 'h3'\n"
    "- use web_read() para capturar conteudo\n"
    "- Maximo 8 passos. JSON puro. NUNCA invente termos.\n\n"
    '{"steps":[{"step":1,"description":"...","action":"...","params":{}}]}'
)


class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="WEB", system_prompt=SYSTEM_PROMPT)
        self._pw = None

    def _has_playwright(self):
        if self._pw is None:
            try: import playwright; self._pw = True
            except ImportError: self._pw = False; self.logger.warning("Sem Playwright")
        return self._pw

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)
        routine = _detect_web_routine(task_text)
        if routine:
            if self._has_playwright():
                self.logger.info(f"Rotina: {len(routine)} steps")
                return {"steps": routine, "agent": "WEB"}
            native = _native_fallback(routine)
            if native:
                self.logger.info(f"Nativo: {len(native)} steps")
                return {"steps": native, "agent": "WEB"}

        self.logger.info("LLM fallback")
        ctx = "\nCONTEXTO: " + json.dumps(context) if context else ""
        try:
            raw = self._client.message(model=self.model, system=self.system_prompt,
                user_content=f"TAREFA: {task_text}{ctx}\nJSON puro.", max_tokens=2000)
            from core.json_validator import safe_parse
            plan = safe_parse(raw, self.model)
            steps = plan.get("steps", [])
            for st in steps: st["agent"] = "WEB"
            if not self._has_playwright() and steps:
                native = _native_fallback(steps)
                if native: return {"steps": native, "agent": "WEB"}
            self._metrics["total_plans"] += 1; self._metrics["successful_plans"] += 1
            return {"steps": steps, "agent": "WEB"}
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1; self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "WEB"}