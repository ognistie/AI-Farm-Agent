"""
AutomationEngine v8 — Universal. run_python para código dinâmico.
Workspace compartilhado entre passos. Auto-install de libs.

v8: auto-installer usa AST em vez de regex multiline.
    O regex pegava imports DENTRO de strings (ex: o creator script do
    CodeAgent que tem `main_py = '''from database...'''` no meio do código),
    o que fazia o pip tentar instalar `database`, `utils`, etc — modulos
    locais do projeto que estavam sendo CRIADOS, nao deps externas.
"""

import os, glob, shutil, subprocess, time, getpass, random, json, sys, traceback, re, math, csv, base64
import ast as _ast
import collections, pathlib, string
from datetime import datetime
import pyautogui, psutil
import pygetwindow as gw
from PIL import Image

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

BLOCKED_CMDS = ["rm -rf","rmdir /s","format c","del /f /s","shutdown","reg delete","diskpart","bcdedit"]
# Prefixos que os handlers usam para sinalizar falha. Antes so "❌" contava:
# "⚠️ Confiança muito baixa", "⛔ Bloqueado" e "Timeout" viravam sucesso e
# a tarefa ia para a memoria como rota que funcionou.
FAILURE_PREFIXES = ("❌", "⛔", "⚠️", "Timeout", "Erro")
# Abaixo disso o palpite de coordenada da visao e chute: melhor falhar e cair no retry.
MIN_VISION_CONFIDENCE = 0.5

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"

def _brain_hints(agent: str, goal: str) -> str:
    """Playbooks, licoes e termos do Obsidian para os pilotos (so referencia; falha nunca bloqueia)."""
    try:
        from core.brain import get_brain
        return get_brain().context_for(agent, goal, compact=True)
    except Exception:
        return ""


def expand(p):
    if not p: return p
    p = p.replace("~",BASE).replace("$HOME",BASE).replace("%USERPROFILE%",BASE)
    return os.path.expandvars(p).replace("\\","/")

def safe(cmd):
    return not any(b in cmd.lower().strip() for b in BLOCKED_CMDS)

def human_move(x, y):
    sw, sh = pyautogui.size()
    x, y = max(10, min(int(x), sw-10)), max(10, min(int(y), sh-10))
    try: pyautogui.moveTo(x, y, duration=random.uniform(0.2,0.4), tween=pyautogui.easeOutQuad)
    except: pyautogui.moveTo(sw//2, sh//2, duration=0.1)

def is_our_browser(title):
    t = title.lower()
    return "127.0.0.1" in t or "ai farm" in t or "localhost:5000" in t

_UNTITLED = ("sem título", "sem titulo", "untitled", "novo documento", "documento1", "new tab", "nova guia")


# Office: "Pasta1 - Excel", "Book2 - Excel", "Documento1 - Word" (nunca "Pasta1.xlsx - Excel")
_OFFICE_NEW = re.compile(r"^(?:pasta|book|documento|document)\d+(?:\s+-\s+|$)")


def _is_untitled(title: str) -> bool:
    t = (title or "").lstrip("*• ").lower()
    return any(t.startswith(u) for u in _UNTITLED) or bool(_OFFICE_NEW.match(t))


def _window_title(hwnd) -> str:
    try:
        import ctypes
        u = ctypes.windll.user32
        n = u.GetWindowTextLengthW(int(hwnd))
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(int(hwnd), buf, n + 1)
        return buf.value
    except Exception:
        return ""


def _norm_name(name: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", (name or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


# Nome falado -> programa (abre direto, sem digitar no menu Iniciar)
_KNOWN_EXE = {
    "bloco de notas": "notepad.exe", "notepad": "notepad.exe",
    "calculadora": "calc.exe", "calculator": "calc.exe",
    "paint": "mspaint.exe", "explorador de arquivos": "explorer.exe", "explorer": "explorer.exe",
    "excel": "excel", "microsoft excel": "excel", "word": "winword", "microsoft word": "winword",
    "powerpoint": "powerpnt", "outlook": "outlook",
    "visual studio code": "code", "vs code": "code", "vscode": "code",
    "configuracoes": "ms-settings:", "configuracoes do windows": "ms-settings:", "settings": "ms-settings:",
    "prompt de comando": "cmd.exe", "terminal": "wt.exe", "gerenciador de tarefas": "taskmgr.exe",
}


# Nome de app digitado na busca do Iniciar: caminho, argumento ("cmd /c", "-Command") ou
# simbolo de shell transformaria a busca num comando.
_UNSAFE_APP_NAME = re.compile(r"[\\/:*?\"<>|&^%;`$]|\s[-/]\w|\.(?:exe|bat|cmd|ps1|vbs|js|msi|lnk)\b", re.I)


def _is_blank_doc(title: str) -> bool:
    """Documento novo E sem alteracoes: '*Sem titulo' e texto nao salvo do usuario."""
    return _is_untitled(title) and not (title or "").lstrip().startswith("*")


def _same_doc(a: str, b: str) -> bool:
    """Mesmo documento? Ignora o '*' de nao salvo e o sufixo do app."""
    norm = lambda s: (s or "").lstrip("*• ").split(" - ")[0].strip().lower()
    return bool(norm(a)) and norm(a) == norm(b)


def _is_front(hwnd) -> bool:
    """A janela (ou uma janela dela, ex.: dialogo) esta em primeiro plano?"""
    try:
        import ctypes
        u = ctypes.windll.user32
        fg = u.GetForegroundWindow()
        if not fg:
            return False
        root = lambda h: u.GetAncestor(h, 3) or h          # GA_ROOTOWNER
        return int(fg) == int(hwnd) or root(fg) == root(int(hwnd))
    except Exception:
        return False


def _bring_to_front(hwnd) -> bool:
    """Traz a janela para frente e CONFERE. O Windows nega o foco a quem esta em segundo
    plano (ex.: conversa por voz com o usuario em outro app); por isso anexa a fila de
    entrada da janela da frente antes de pedir o foco. Devolve se ficou mesmo na frente."""
    try:
        import ctypes
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        h = int(hwnd)
        if not u.IsWindow(h):
            return False
        if u.IsIconic(h):
            u.ShowWindow(h, 9)                              # SW_RESTORE
        for _ in range(3):
            if _is_front(h):
                return True
            fg = u.GetForegroundWindow()
            me = k.GetCurrentThreadId()
            other = u.GetWindowThreadProcessId(fg, None) if fg else 0
            attached = bool(other and other != me and u.AttachThreadInput(me, other, True))
            try:
                u.BringWindowToTop(h)
                u.SetForegroundWindow(h)
            finally:
                if attached:
                    u.AttachThreadInput(me, other, False)
            for _ in range(8):
                if _is_front(h):
                    return True
                time.sleep(0.05)
        return _is_front(h)
    except Exception:
        return False


def _activate_hwnd(hwnd):
    """Traz para frente a janela guardada na conversa. Devolve o titulo ou None (fechou)."""
    if not hwnd:
        return None
    try:
        import ctypes
        h = int(hwnd)
        if not ctypes.windll.user32.IsWindow(h):
            return None
        _bring_to_front(h)
        time.sleep(0.15)
        return _window_title(h) or "janela"
    except Exception:
        return None


def _paste_front(hwnd, text: str) -> bool:
    """Cola o texto SO se a janela certa esta na frente (senao o Ctrl+V cairia em outro app)."""
    if not _bring_to_front(hwnd):
        return False
    if re.search(r'\b(cmd|powershell|terminal|command prompt)\b', _window_title(hwnd), re.I):
        return False
    time.sleep(0.1)
    if not _is_front(hwnd):
        return False
    try:
        from core.clipboard import paste_text
        paste_text(text)
    except Exception:
        pyautogui.write(text)
    return True


_NO_FOCUS = ("⛔ O Windows não deixou trazer a janela '{t}' para frente. "
             "Nada foi digitado (para não escrever em outro app).")


def focus_away():
    try:
        active = gw.getActiveWindow()
        if active and is_our_browser(active.title):
            for w in gw.getAllWindows():
                if w.visible and w.title and not is_our_browser(w.title) and w.title.strip():
                    try: w.activate(); time.sleep(0.3); return True
                    except: pass
    except: pass
    return False


class BrowserController:
    def __init__(self):
        self.pw=None; self.browser=None; self.page=None; self._started=False

    def start(self):
        if self._started: return True
        try:
            from playwright.sync_api import sync_playwright
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=False, args=["--start-maximized"])
            self.page = self.browser.new_context(no_viewport=True).new_page()
            self._started = True; return True
        except Exception as e: print(f"  ⚠️ Playwright: {e}"); return False

    def ensure(self):
        if not self._started: self.start()
        return bool(self.page)

    def goto(self, url):
        if not self.ensure(): return "⚠️ Browser indisponível"
        if not url.startswith("http"): url = "https://"+url
        self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(1); return f"🌐 {self.page.title()}"

    def click_el(self, text):
        if not self.ensure(): return "⚠️"
        for fn in [lambda:self.page.get_by_text(text,exact=False).first, lambda:self.page.get_by_role("link",name=text).first, lambda:self.page.get_by_role("button",name=text).first]:
            try:
                loc=fn()
                if loc.is_visible(timeout=2000): loc.click(); return f"🌐 Clicou: '{text[:30]}'"
            except: pass
        try: self.page.click(text, timeout=3000); return f"🌐 Clicou"
        except: return f"❌ '{text[:30]}'"

    def type_in(self, field, text):
        if not self.ensure(): return "⚠️"
        # Tenta múltiplos seletores (field pode ter alternativas separadas por vírgula)
        selectors = [s.strip() for s in field.split(",")]
        for sel in selectors:
            for fn in [
                lambda: self.page.locator(sel).first,
                lambda: self.page.get_by_placeholder(sel).first,
                lambda: self.page.get_by_role("searchbox").first,
                lambda: self.page.get_by_role("textbox").first,
            ]:
                try:
                    loc = fn()
                    if loc.is_visible(timeout=2000):
                        loc.click(); time.sleep(0.3)
                        loc.fill(text)
                        return f"🌐 Digitou: '{text[:30]}'"
                except: pass
        # Fallback: tenta clicar na área de busca e digitar via teclado
        try:
            self.page.keyboard.press("Tab")
            time.sleep(0.2)
            self.page.keyboard.type(text, delay=50)
            return f"🌐 Digitou (keyboard): '{text[:30]}'"
        except: pass
        return f"❌ '{field[:20]}'"

    def press(self, key):
        if not self.ensure(): return "⚠️"
        self.page.keyboard.press(key); return f"🌐 {key}"

    def shot(self, path):
        if not self.ensure(): return None
        self.page.screenshot(path=path, full_page=False); return path

    def text(self): return self.page.inner_text("body")[:2000] if self.ensure() else ""
    def title(self): return self.page.title() if self.ensure() else ""

    def new_tab(self, url="about:blank"):
        if not self.ensure(): return "⚠️"
        self.page = self.browser.contexts[0].new_page()
        if url != "about:blank": self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return f"🌐 Nova aba"


# ── Prontidao de janela (espera adaptativa) ───────────────────────────
def _process_matches(hwnd, exe):
    try:
        import ctypes
        from ctypes import wintypes
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        return psutil.Process(pid.value).name().casefold() == exe.casefold()
    except Exception:
        return False


def _app_windows(name):
    """Janelas visiveis do app: pelo processo quando conhecido, senao pelo titulo."""
    exe = _KNOWN_EXE.get(_norm_name(name))
    hints = _title_hints(name)
    matches = []
    for window in gw.getAllWindows():
        if not window.visible or not window.title or is_our_browser(window.title):
            continue
        identity = _process_matches(window._hWnd, exe) if exe and exe.endswith('.exe') else any(h in window.title.lower() for h in hints)
        if identity:
            matches.append(window._hWnd)
    return matches


def _resolve_app_window(name, known=()):
    """Find an app even when Windows denied foreground activation; never guess a document.
    `known`: windows that existed before opening; a single new one is what was just opened."""
    matches = _app_windows(name)
    front, _ = _fg_state()
    if front in matches:
        return front
    new = [hwnd for hwnd in matches if hwnd not in known]
    if len(new) == 1:
        return new[0]
    return matches[0] if len(matches) == 1 else None


def _opened_without_focus(name, known, started):
    """O Windows pode abrir o app sem dar o primeiro plano a ele. Sem isto a espera ia ate o fim
    (12 s) com a janela ja aberta atras. Janela nova na frente segue a espera normal de pronta."""
    first_seen = []

    def check():
        found = set(_app_windows(name))
        new = found - set(known)
        now = time.time()
        if new:
            if _fg_state()[0] in new:
                return False
            first_seen.append(now)
            return now - first_seen[0] >= OPENED_SETTLE_S
        return bool(found) and now - started >= REUSED_WINDOW_S    # abriu aba na janela que ja existia
    return check


def _title_hints(name: str) -> tuple:
    """Trechos de titulo que identificam a janela do app ('Bloco de Notas' -> 'bloco de notas',
    'notepad'; 'Microsoft Teams' -> 'microsoft teams', 'teams')."""
    n = (name or "").strip().lower()
    if not n:
        return ()
    hints = {n}
    try:
        from core.observer import APP_TITLES
        known = set(APP_TITLES.get(_norm_name(n), ()))
    except Exception:
        known = set()
    hints |= known
    last = n.split()[-1]
    if not known and len(last) > 3:
        hints.add(last)              # "Microsoft Teams" -> "teams" (app fora da tabela)
    return tuple(sorted(hints))


# As rotinas pedem "aguardar N s" depois de abrir algo. N e o TETO: a espera
# acaba assim que a janela nova esta pronta. Sem mudanca de janela, espera N.
READY_MIN_S = 0.3        # nunca menos que isso (o app ainda pinta a janela)
READY_STABLE_S = 0.4     # titulo parado por esse tempo = carregou
READY_SETTLED_S = 1.0    # app que nunca fica "ocioso" (WhatsApp, apps UWP): estavel e respondendo basta
OPENED_SETTLE_S = 0.6    # janela nova atras: tempo para o foco ainda chegar
REUSED_WINDOW_S = 3.0    # nenhuma janela nova: o app reaproveitou a que ja estava aberta


def _fg_state():
    """(hwnd, titulo) da janela em primeiro plano."""
    try:
        import ctypes
        u = ctypes.windll.user32
        h = u.GetForegroundWindow()
        n = u.GetWindowTextLengthW(h)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, buf, n + 1)
        return int(h or 0), buf.value
    except Exception:
        return 0, ""


def _responsive(hwnd: int) -> bool:
    """Janela visivel, de outro processo e respondendo (sem exigir 'ocioso')."""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        if not hwnd or not u.IsWindowVisible(hwnd) or u.IsHungAppWindow(hwnd):
            return False
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value != os.getpid()
    except Exception:
        return False


def _window_ready(hwnd: int) -> bool:
    """Janela visivel, respondendo, de outro processo, e com o app ocioso para entrada."""
    try:
        import ctypes
        from ctypes import wintypes
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        if not hwnd or not u.IsWindowVisible(hwnd) or u.IsHungAppWindow(hwnd):
            return False
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            return False                       # a propria janela do AI Farm Agent nao conta
        hp = k.OpenProcess(0x00100000 | 0x1000, False, pid.value)   # SYNCHRONIZE | QUERY_LIMITED
        if not hp:
            return True                        # sem acesso (app elevado): nao bloqueia
        try:
            # 0 = ocioso; WAIT_FAILED (app sem fila de mensagens) tambem conta como pronto
            return u.WaitForInputIdle(hp, 0) in (0, 0xFFFFFFFF)
        finally:
            k.CloseHandle(hp)
    except Exception:
        return False


class AutomationEngine:
    def __init__(self):
        self.executed_steps = []
        self.dry_run = False
        # Janela em primeiro plano ANTES da ultima acao (base da espera adaptativa)
        self._fg_before = None
        self._expect = None      # titulos aceitos depois de abrir um app ("obsidian", "bloco de notas")
        self.should_stop = None
        self._target_hwnd = None
        self.vision = None
        self.browser = BrowserController()
        self.workspace = {}  # Contexto compartilhado entre passos
        try:
            from core.vision import VisionEngine
            self.vision = VisionEngine()
            print("  Visao ativada")
        except Exception as e: print(f"  Visao: {e}")

        # Interaction Layer (UIA + Vision)
        self.il = None
        try:
            from core.interaction_layer import InteractionLayer
            self.il = InteractionLayer(self.vision)
            print("  UIA + InteractionLayer ativados")
        except Exception as e: print(f"  InteractionLayer: {e}")

        # Retry Engine
        self.retry = None
        try:
            from core.retry_engine import RetryEngine
            self.retry = RetryEngine(self.il)
        except: pass

    def execute(self, action, params, dry_run=False):
        self.dry_run = dry_run
        ts = datetime.now().isoformat()
        start_time = time.time()
        MAP = {
            "run_python":self._run_python, "pip_install":self._pip_install,
            "excel_write":self._excel_write, "app_search":self._app_search, "app_type":self._app_type,
            "list_files":self._list_files,"move_file":self._move_file,"copy_file":self._copy_file,
            "create_folder":self._create_folder,"delete_file":self._delete_file,
            "read_file":self._read_file,"write_file":self._write_file,"find_files":self._find_files,
            "open_app":self._app_search,"close_app":self._close_app,"focus_window":self._focus_window,
            "run_command":self._run_command,"type_text":self._type_text,"hotkey":self._hotkey,
            "click":self._click,"screenshot":self._screenshot,"wait":self._wait,
            "vision_click":self._vision_click,"vision_type":self._vision_type,
            "vision_analyze":self._vision_analyze,"vision_verify":self._vision_verify,"vision_smart":self._vision_smart,
            "web_goto":self._web_goto,"web_click":self._web_click,"web_type":self._web_type,
            "web_key":self._web_key,"web_screenshot":self._web_screenshot,"web_read":self._web_read,"web_new_tab":self._web_new_tab,
            # Novas acoes v2
            "uia_click":self._uia_click,"uia_type":self._uia_type,
            "wait_for_window":self._wait_for_window,"wait_for_element":self._wait_for_element,
            "browser_click":self._browser_click,"browser_read":self._browser_read,"browser_task":self._browser_task,
            "edit_project":self._edit_project,"revert_project":self._revert_project,
            "blank_document":self._blank_document,"app_task":self._app_task,"open_path":self._open_path,
            "create_project":self._create_project,"create_workbook":self._create_workbook,
            "open_url":self._open_url,
        }
        handler = MAP.get(action)
        if not handler:
            return {"success":False,"status":"rejected","verified":False,"action":action,"result":f"Acao desconhecida: {action}","timestamp":ts}
        if not isinstance(params, dict):
            return {"success":False,"status":"rejected","verified":False,"action":action,"result":"Parametros devem ser um objeto.","timestamp":ts}
        self.last_say = ""               # frase final do piloto (vira a resposta ao usuario)
        # Central invariant: simulation cannot invoke ANY handler (including reads/captures).
        if dry_run:
            rec = {"success":True,"status":"simulated","verified":False,"action":action,
                   "params":params,"result":f"[SIM] {action}","timestamp":ts,"dry_run":True}
            self.executed_steps.append(rec)
            return rec
        if callable(getattr(self, "should_stop", None)) and self.should_stop():
            return {"success":False,"status":"cancelled","verified":False,"action":action,
                    "result":"Cancelado antes da acao.","timestamp":ts}
        if action in ('run_python', 'run_command', 'pip_install'):
            return {"success":False,"status":"rejected","verified":False,"action":action,
                    "result":"Execucao arbitraria desativada. Use ferramentas declarativas.","timestamp":ts}
        from core.action_policy import authorize
        denied = authorize(getattr(self, 'current_agent', ''), getattr(self, 'authorized_task', ''), action, params)
        if denied:
            return {"success":False,"status":"rejected","verified":False,"action":action,"result":denied,"timestamp":ts}
        if action != "wait" and not dry_run:
            self._fg_before = _fg_state()
            self._expect = None          # o app esperado vale so ate a proxima acao
        try:
            result = handler(params)
            if isinstance(result, dict):
                rec = {**result, "success": result.get("success") is True,
                       "verified": result.get("verified") is True and result.get("success") is True}
            else:
                ok = not (isinstance(result,str) and result.lstrip().startswith(FAILURE_PREFIXES))
                rec = {"success":ok,"result":result,"verified":False}
            rec.update(action=action, params=params, timestamp=ts, dry_run=False)
            rec.setdefault("status", "succeeded" if rec["success"] else "failed")
        except pyautogui.FailSafeException:
            rec = {"success":False,"action":action,"params":params,"result":"FailSafe","timestamp":ts}
        except Exception as e:
            rec = {"success":False,"action":action,"params":params,"result":f"Erro: {e}","timestamp":ts}
        rec.setdefault("status", "failed")
        rec.setdefault("verified", False)

        # Log da acao
        duration = int((time.time() - start_time) * 1000)
        try:
            from core.action_logger import log_action
            log_action("ENGINE", action, params, rec, duration_ms=duration)
        except: pass

        self.executed_steps.append(rec)
        self.workspace[f"step_{len(self.executed_steps)}"] = rec
        return rec

    # === UIA (novo v2) ===
    def _uia_click(self, p):
        app_name = p.get("app_name", "")
        element = p.get("element", "")
        if self.dry_run: return f"[SIM] UIA click: {element}"
        if self.il:
            result = self.il.click_element(app_name, element)
            if result.get("success"):
                return f"✅ UIA click: {element} [{result.get('method','')}]"
            # Se UIA falhou e tem vision, ja tentou internamente
            return f"❌ {element}: {result.get('error','')}"
        return "❌ InteractionLayer nao disponivel"

    def _uia_type(self, p):
        app_name = p.get("app_name", "")
        field = p.get("field", "")
        text = p.get("text", "")
        if self.dry_run: return f"[SIM] UIA type: {text[:30]}"
        if self.il:
            result = self.il.type_in_field(app_name, field, text)
            if result.get("success"):
                return f"✅ UIA type: '{text[:30]}' [{result.get('method','')}]"
            return f"❌ {field}: {result.get('error','')}"
        return "❌ InteractionLayer nao disponivel"

    def _wait_for_window(self, p):
        title = p.get("title", "")
        timeout = p.get("timeout", 15)
        if self.dry_run: return f"[SIM] Aguardar: {title}"
        try:
            from core.wait_engine import wait_for_window
            result = wait_for_window(title, timeout)
            if result.get("success"):
                return f"✅ {title} apareceu ({result.get('elapsed',0)}s)"
            return f"❌ {result.get('error','Timeout')}"
        except:
            # Fallback: wait fixo
            time.sleep(min(timeout, 5))
            return f"⏳ Wait fixo {min(timeout,5)}s (wait_engine indisponivel)"

    def _wait_for_element(self, p):
        app_name = p.get("app_name", "")
        element = p.get("element", "")
        timeout = p.get("timeout", 10)
        if self.dry_run: return f"[SIM] Aguardar elemento: {element}"
        try:
            from core.wait_engine import wait_for_element
            result = wait_for_element(app_name, element, timeout)
            if result.get("success"):
                return f"✅ {element} visivel ({result.get('elapsed',0)}s)"
            return f"❌ {result.get('error','Timeout')}"
        except:
            time.sleep(min(timeout, 3))
            return f"⏳ Wait fixo"

    # === RUN PYTHON — o coração universal ===
    def _create_project(self, p):
        from core.artifact_builder import build_project
        return build_project(p.get('manifest'))

    def _open_url(self, p):
        from urllib.parse import urlsplit
        import webbrowser
        url = p.get('url', '')
        if not isinstance(url, str) or any(char.isspace() for char in url):
            return '⛔ URL invalida.'
        try:
            parsed = urlsplit(url)
        except ValueError:
            return '⛔ URL invalida.'
        if url != 'about:blank' and (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password):
            return '⛔ Apenas URLs HTTP/HTTPS sem credenciais sao permitidas.'
        opened = webbrowser.open_new_tab(url)
        return {'success': bool(opened), 'verified': False, 'result': 'Abertura solicitada: ' + url,
                'artifacts': {'url': url}}

    def _create_workbook(self, p):
        from core.artifact_builder import build_workbook
        return build_workbook(p.get('manifest'))

    def _run_python(self, p):
        """Same-user managed worker; no code executes in the desktop process."""
        if self.dry_run:
            return "[SIM] Python"
        code = p.get("code", "")
        if not isinstance(code, str) or not code.strip():
            return {"success": False, "status": "rejected", "result": "Codigo vazio.", "verified": False}
        from core.process_runner import run_python
        import uuid
        directory = pathlib.Path(__file__).resolve().parent.parent / "memory" / "executions" / uuid.uuid4().hex
        directory.mkdir(parents=True, exist_ok=False)
        cwd = str(directory)
        serializable = {}
        for key, value in self.workspace.items():
            try:
                json.dumps(value, allow_nan=False)
                serializable[key] = value
            except (TypeError, ValueError):
                continue
        result = run_python(code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME),
                            workspace=serializable, cwd=cwd,
                            should_stop=getattr(self, "should_stop", None))
        if result["success"]:
            self.workspace.update(result.pop("workspace", {}))
        result["result"] = f"🐍 {p.get('description', 'codigo')}\n" + result["result"]
        return result

    def _pip_install(self, p):
        return {"success": False, "status": "rejected", "verified": False,
                "result": "Instalacao durante tarefas desativada. Instale dependencias pelo ambiente do projeto."}

    # === SMART ACTIONS ===
    def _excel_write(self, p):
        data = p.get("data", []); filepath = expand(p.get("filepath", "")); sheet = p.get("sheet_name", "Planilha1")
        if self.dry_run: return f"[SIM] Excel: {len(data)} linhas"
        if not data: return "❌ Dados vazios"
        if not filepath: filepath = os.path.join(BASE, "Desktop", f"planilha_{datetime.now().strftime('%H%M%S')}.xlsx")
        try:
            import openpyxl
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = sheet
            for row in data: ws.append([str(c) for c in row])
            for col in ws.columns:
                mx = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = max(mx+2, 10)
            if os.path.dirname(filepath): os.makedirs(os.path.dirname(filepath), exist_ok=True)
            wb.save(filepath)
            subprocess.Popen(f'start "" "{filepath}"', shell=True); time.sleep(2)
            return f"📊 {filepath} ({len(data)} linhas)"
        except ImportError:
            return "❌ openpyxl não instalado. Use pip_install primeiro."

    def _app_search(self, p):
        name = p.get("name","") or p.get("app_name","")
        if not name: return "❌ Nome vazio"
        # Apps conhecidos abrem pelo programa (rapido e sem depender do menu Iniciar)
        exe = _KNOWN_EXE.get(_norm_name(name)) or _KNOWN_EXE.get(_norm_name(name).removesuffix(".exe"))
        if not exe and _UNSAFE_APP_NAME.search(name):
            # a busca do Iniciar + Enter EXECUTA o que for digitado: so nome de app, nunca comando/caminho
            return f"⛔ '{name[:40]}' não parece nome de aplicativo (tem caminho, argumento ou símbolo de comando)."
        if self.dry_run: return f"[SIM] {name}"
        before = _fg_state()
        self._expect = _title_hints(name)
        if exe:
            try:
                known = _app_windows(name)
                subprocess.Popen(["cmd", "/c", "start", "", exe], creationflags=0x08000000)
                self._await_ready(before, 12.0, early=_opened_without_focus(name, known, time.time()))
                hwnd, title = _fg_state()
                if not any(hint in title.lower() for hint in self._expect):
                    hwnd = _resolve_app_window(name, known)
                    if not hwnd:
                        return f'❌ Janela do aplicativo {name} nao confirmada ou ambigua.'
                    _activate_hwnd(hwnd)
                self._target_hwnd = hwnd
                return f"✅ {name}"
            except Exception:
                pass                     # cai na busca do menu Iniciar
        pyautogui.press("win"); time.sleep(0.8)
        try:
            from core.clipboard import paste_text; paste_text(name)
        except: pyautogui.typewrite(name, interval=0.04) if name.isascii() else pyautogui.write(name)
        time.sleep(1.5); before = _fg_state(); pyautogui.press("enter")
        self._await_ready(before, 12.0)
        hwnd, title = _fg_state()
        if not any(hint in title.lower() for hint in self._expect):
            hwnd = _resolve_app_window(name)
            if not hwnd:
                return f'❌ Janela do aplicativo {name} nao confirmada.'
            _activate_hwnd(hwnd)
        self._target_hwnd = hwnd
        return f"✅ {name}"

    def _app_type(self, p):
        title, text = p.get("window_title",""), p.get("text","")
        if self.dry_run: return f"[SIM] Digitar em '{title}'"
        # Janela da conversa (handle): o titulo muda ("*Sem titulo"), o handle nao
        got = _activate_hwnd(p.get("hwnd"))
        if got:
            # Mesma janela, mas a ABA ativa pode ser outro documento do usuario
            expect = p.get("expect_title")
            if expect and not _same_doc(got, expect):
                return (f"⛔ A aba ativa mudou para '{got[:40]}' (a conversa usava '{expect[:40]}'). "
                        "Não vou escrever no documento errado.")
            if not _paste_front(p.get("hwnd"), text):
                return _NO_FOCUS.format(t=got[:40])
            return f"✅ '{got[:25]}': {text[:40]}"
        # Documento em branco garantido por blank_document: digita NELE
        doc = getattr(self, "_doc_hwnd", None)
        if p.get("require_untitled") and doc:
            got = _activate_hwnd(doc)
            if got and _is_untitled(got):
                if not _paste_front(doc, text):
                    return _NO_FOCUS.format(t=got[:40])
                self._doc_hwnd = None
                return f"✅ '{got[:25]}': {text[:40]}"
        search = title.lower()
        for _ in range(8):
            try:
                for w in gw.getAllWindows():
                    if search in w.title.lower() and w.visible and w.title and not is_our_browser(w.title):
                        if p.get("require_untitled") and not _is_blank_doc(w.title):
                            continue   # nunca digitar num documento que o usuario ja tinha aberto
                        if not _paste_front(w._hWnd, text):
                            return _NO_FOCUS.format(t=w.title[:40])
                        return f"✅ '{title[:25]}': {text[:40]}"
            except: pass
            time.sleep(0.4)
        return f"❌ Janela: '{title}'"

    def _blank_document(self, p):
        """Garante um documento NOVO e sem alteracoes NA JANELA DO APP antes de digitar.
        O Bloco de Notas do Win11 (com abas) reabre o ultimo documento; e a janela da
        frente logo apos abrir pode nem ser o app. Por isso: acha a janela pelo titulo,
        traz para frente e, se a aba ativa nao for nova, abre uma (Ctrl+N)."""
        if self.dry_run: return "[SIM] Documento em branco"
        from core.observer import _app_window
        key = p.get("app", "notepad")
        found = None
        for _ in range(12):
            found = _app_window(key)
            if found:
                break
            time.sleep(0.5)
        if not found:
            return f"❌ A janela do {key} não abriu"
        hwnd = found[0]
        if not _is_blank_doc(found[1]):
            # Ja existe uma janela DESTE app em branco? usa ela (nada de Ctrl+N a mais)
            suffix = found[1].rsplit(" - ", 1)[-1].strip().lower()
            try:
                blank = next((w for w in gw.getAllWindows()
                              if w.title.rsplit(" - ", 1)[-1].strip().lower() == suffix
                              and _is_blank_doc(w.title)), None)
            except Exception:
                blank = None
            if blank is not None:
                hwnd = blank._hWnd
        title = _activate_hwnd(hwnd) or _window_title(hwnd) or found[1]
        if not _is_blank_doc(title) and " - " not in title and key in ("excel", "word", "powerpoint"):
            # Tela inicial do Office ("Excel", sem documento): Esc fecha a tela e abre o
            # documento em branco (o Ctrl+N nessa tela nem sempre funciona)
            _activate_hwnd(hwnd)
            pyautogui.press("escape")
            for _ in range(10):
                time.sleep(0.3)
                again = _app_window(key)
                if again and _is_blank_doc(again[1]):
                    hwnd, title = again
                    break
        for attempt in range(2):
            if _is_blank_doc(title):
                break
            # O Windows pode negar o foco (outro app na frente): reativa antes de cada Ctrl+N
            _activate_hwnd(hwnd)
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "n")
            time.sleep(1.0)
            # Win11: aba nova na mesma janela; versoes antigas: janela nova
            title = _window_title(hwnd)
            if not _is_blank_doc(title):
                again = _app_window(key)
                if again and _is_blank_doc(again[1]):
                    hwnd, title = again
                    _activate_hwnd(hwnd)
        if not _is_blank_doc(title):
            return (f"⛔ Não consegui um documento em branco (ativo: '{title[:40]}'). "
                    "Não vou digitar em documento existente.")
        self._doc_hwnd = hwnd
        return f"✅ Documento em branco: {title[:40]}"

    # === FOCUS ===
    def _focus_window(self, p):
        title = p.get("title","")
        if self.dry_run: return f"[SIM] {title}"
        got = _activate_hwnd(p.get("hwnd"))
        if got and _is_front(p.get('hwnd')):
            self._target_hwnd = p['hwnd']
            return f"🎯 {got[:40]}"
        if not title:
            return '⛔ Focar exige titulo ou handle confirmado.'
        # Apps pesados (Obsidian, Teams, Spotify) levam alguns segundos para criar a janela
        try:
            limit = min(float(p.get("timeout", 8)), 20.0)
        except (TypeError, ValueError):
            limit = 8.0
        end, seen = time.time() + limit, ""
        while time.time() < end:
            try:
                for w in gw.getAllWindows():
                    if title.lower() in w.title.lower() and w.visible and w.title and not is_our_browser(w.title):
                        seen = w.title
                        if _bring_to_front(w._hWnd):
                            self._target_hwnd = w._hWnd
                            time.sleep(0.2)
                            return f"🎯 {w.title[:40]}"
            except Exception:
                pass
            stop = getattr(self, "should_stop", None)
            if stop and stop():
                break
            time.sleep(0.4)
        if seen:
            return _NO_FOCUS.format(t=seen[:40]).replace("Nada foi digitado (para não escrever em outro app).",
                                                        "A janela existe, mas ficou atrás.")
        return f"❌ A janela '{title}' não apareceu em {limit:.0f}s"

    # === VISION ===
    def _ensure_app_focus(self):
        """Fail closed: never guess an unrelated foreground window."""
        hwnd = getattr(self, '_target_hwnd', None)
        return bool(hwnd and _bring_to_front(hwnd) and _is_front(hwnd))

    def _vision_click(self, p):
        desc = p.get("description","")
        if self.dry_run: return f"[SIM] {desc}"
        if not self.vision: return "⚠️ Sem visão"

        if p.get('hwnd'):
            self._target_hwnd = p['hwnd']
        if not self._ensure_app_focus():
            return '⛔ Janela alvo nao confirmada para visao.'

        # Tenta até 2 vezes
        for attempt in range(2):
            r = self.vision.find_element(desc)
            if r.get("error") or not r.get("found"):
                if attempt == 0:
                    time.sleep(1)  # espera e tenta de novo
                    continue
                return f"❌ {desc}: {r.get('reason', r.get('message','não encontrado'))}"

            x, y, c = r.get("x",0), r.get("y",0), r.get("confidence",0)

            # PROTEÇÃO: se Y está na zona da taskbar (últimos 50px), rejeita
            sw, sh = pyautogui.size()
            if y > sh - 60:
                if attempt == 0:
                    time.sleep(1); continue
                return f"⚠️ Coordenada na taskbar ({x},{y}) — elemento errado"

            if c < MIN_VISION_CONFIDENCE:
                if attempt == 0: time.sleep(1); continue
                return f"⚠️ Confiança muito baixa: {c:.0%}"

            # Clica
            human_move(x, y)
            time.sleep(0.15)
            pyautogui.click()
            time.sleep(0.4)
            return f"👁️ ({x},{y}) [{c:.0%}]"

        return f"❌ Falhou após 2 tentativas: {desc}"

    # === NAVEGADOR DO USUARIO (UIA) ===
    def _browser_click(self, p):
        """Clica num link da pagina aberta: UIA (texto/URL reais) -> visao conferida."""
        desc = p.get("description", "") or p.get("target", "")
        if self.dry_run: return f"[SIM] Clicar no navegador: {desc}"
        if not desc: return "❌ Descrição do link vazia"
        try:
            from core import browser_uia
        except Exception as e:
            return self._vision_click({"description": desc}) + f" (UIA indisponível: {e})"
        try:
            r = browser_uia.click(desc)
        except Exception as e:
            r = {"ok": False, "error": str(e)}
        if r.get("ok"):
            return f"✅ Link '{r.get('name','')[:60]}' → {r.get('url','')[:90]} [UIA {r.get('method','')}]"
        if r.get("blocked"):
            return r["error"]
        # Visao como ultimo recurso, mas CONFERIDA: sem mudanca de pagina = falha
        win = browser_uia.browser_window()
        before = browser_uia._signature(win) if win else None
        vdesc = desc if "navegador" in desc else desc + " (dentro da pagina do navegador)"
        res = self._vision_click({"description": vdesc})
        if res.startswith("👁️") and win is not None:
            if browser_uia.wait_change(win, before):
                return f"{res} → página mudou (visão; UIA: {r.get('error','')[:60]})"
            return f"⚠️ Clique por visão sem efeito na página: {desc[:60]}"
        return res

    def _browser_task(self, p):
        """Objetivo livre em qualquer site: o piloto le a pagina, age e confere, turno a turno."""
        goal = p.get("goal") or p.get("task", "")
        if self.dry_run: return f"[SIM] Piloto do navegador: {goal}"
        if not goal: return "❌ Objetivo vazio"
        try:
            from core.browser_pilot import BrowserPilot, format_result
        except Exception as e:
            return f"⚠️ Piloto do navegador indisponível: {e}"
        hints = _brain_hints("WEB", goal)
        pilot = BrowserPilot(vision_click=self._vision_click,
                             should_stop=getattr(self, "should_stop", None),
                             on_progress=getattr(self, "on_progress", None))
        r = pilot.run(goal, p.get("start_url", ""), hints, resume=p.get("resume"))
        self.last_say = r.get("say", "")
        return format_result(r)

    def _app_task(self, p):
        """Objetivo livre dentro de uma janela de app ja aberta (piloto de apps)."""
        goal = p.get("goal", "")
        if self.dry_run: return f"[SIM] Piloto do app: {goal}"
        if not goal: return "❌ Objetivo vazio"
        from core.app_pilot import AppPilot
        from core.browser_pilot import format_result
        hwnd, title = p.get("hwnd"), p.get("title", "")
        if not hwnd and p.get("app"):
            # App recem-aberto pela rotina: acha a janela pelo titulo esperado
            from core.observer import _app_window
            for _ in range(12):
                found = _app_window(p["app"])
                if found:
                    hwnd, title = found
                    break
                time.sleep(0.5)
            if not hwnd:
                return f"❌ Não achei a janela do {p['app']} para continuar"
        pilot = AppPilot(vision_click=self._vision_click,
                         should_stop=getattr(self, "should_stop", None),
                         on_progress=getattr(self, "on_progress", None))
        r = pilot.run(goal, hwnd, title, hints=_brain_hints("DESKTOP", goal))
        self.last_say = r.get("say", "")
        return format_result(r)

    def _browser_read(self, p):
        """Le titulo, URL, texto e links da pagina aberta no navegador do usuario."""
        if self.dry_run: return "[SIM] Ler página do navegador"
        try:
            from core import browser_uia
            r = browser_uia.read(max_chars=int(p.get("max_chars", 1500)))
        except Exception as e:
            return f"⚠️ Leitura do navegador indisponível: {e}"
        if not r.get("ok"):
            return f"⚠️ {r.get('error','')}"
        if r.get("blocked"):
            return r["blocked"]
        links = "\n".join(f"- {l['name']}: {l['url']}" for l in r["links"][:10])
        return f"🌐 {r['title']}\n{r['url']}\n{r['text']}" + (f"\nLinks:\n{links}" if links else "")

    def _open_path(self, p):
        """Abre pasta/arquivo direto (sem digitar no menu Iniciar). Nunca executa programas."""
        from core.paths import resolve_path, is_network_path, EXECUTABLE_EXT
        raw = p.get("path", "")
        if re.match(r"^ms-settings:[\w-]*$", raw.strip()):
            # Paginas das Configuracoes do Windows (esquema fixo e seguro)
            if self.dry_run: return f"[SIM] Abrir {raw}"
            os.startfile(raw.strip()); time.sleep(1.2)
            return f"⚙️ Configurações do Windows abertas ({raw.strip()})"
        from core.obsidian_vaults import URI_PATTERN
        if re.match(URI_PATTERN, raw.strip()):
            if self.dry_run: return f"[SIM] Abrir {raw}"
            os.startfile(raw.strip())
            return "📓 Cofre do Obsidian solicitado"
        if re.match(r"^https?://", raw.strip()):
            if self.dry_run: return f"[SIM] Abrir {raw}"
            import webbrowser; webbrowser.open(raw.strip()); return f"🌐 {raw.strip()}"
        path = resolve_path(raw)
        if not path: return "❌ Caminho vazio"
        if is_network_path(raw) or is_network_path(path):
            # antes de os.path.exists: so consultar o caminho ja autentica no servidor remoto
            return "⛔ Não abro caminhos de rede (\\\\servidor\\...) por aqui."
        if not os.path.exists(path): return f"❌ Caminho não existe: {path}"
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in EXECUTABLE_EXT:
            return f"⛔ Não abro executáveis/scripts por aqui: {os.path.basename(path)}"
        if self.dry_run: return f"[SIM] Abrir {path}"
        os.startfile(path)
        time.sleep(1)
        return f"📂 {path}"

    def _vision_type(self, p):
        desc, text = p.get("description",""), p.get("text","")
        if self.dry_run: return f"[SIM]"
        if not self.vision: return "⚠️ Sem visão"
        if not text: return "❌ Texto vazio"

        if not self._ensure_app_focus():
            return '⛔ Janela alvo nao confirmada para digitacao.'

        for attempt in range(2):
            r = self.vision.find_element(desc)
            if r.get("error") or not r.get("found"):
                if attempt == 0: time.sleep(1); continue
                return f"❌ {desc}"

            x, y, c = r.get("x",0), r.get("y",0), r.get("confidence",0)

            # PROTEÇÃO taskbar
            sw, sh = pyautogui.size()
            if y > sh - 60:
                if attempt == 0: time.sleep(1); continue
                return f"⚠️ Campo na taskbar ({x},{y})"

            if c < MIN_VISION_CONFIDENCE:
                if attempt == 0: time.sleep(1); continue
                return f"⚠️ Confiança: {c:.0%}"

            # Clica no campo e digita
            human_move(x, y)
            time.sleep(0.15)
            pyautogui.click()
            time.sleep(0.2)
            pyautogui.click()  # duplo clique para garantir foco no campo
            time.sleep(0.3)

            # Digita via clipboard (mais confiável)
            try:
                from core.clipboard import paste_text
                paste_text(text)
            except:
                # Fallback: digita caractere por caractere
                for ch in text:
                    try: pyautogui.press(ch) if len(ch)==1 and ch.isascii() else None
                    except: pass
                    time.sleep(0.03)

            time.sleep(0.3)
            return f"👁️ ({x},{y}): '{text[:40]}' [{c:.0%}]"

        return f"❌ Falhou após 2 tentativas: {desc}"

    def _vision_analyze(self, p):
        if not self.vision: return "⚠️"
        r = self.vision.analyze_screen(); self.vision.restore_browser()
        return f"👁️ {r.get('screen_description','')}" if not r.get("error") else f"❌"

    def _vision_verify(self, p):
        if not self.vision: return "⚠️"
        r = self.vision.verify_state(p.get("expected","")); self.vision.restore_browser()
        return f"{'✅' if r.get('verified') else '❌'} {r.get('actual_state','')}" if not r.get("error") else "❌"

    def _vision_smart(self, p):
        if not self.vision: return "⚠️"
        r = self.vision.smart_action(p.get("goal",""))
        if r.get("error") or r.get("action")=="none": self.vision.restore_browser(); return f"❌"
        a,x,y = r.get("action"),r.get("x",0),r.get("y",0)
        try:
            if a=="click": human_move(x,y); pyautogui.click()
            elif a=="type": human_move(x,y); pyautogui.click(); time.sleep(0.2); pyautogui.write(r.get("text_to_type",""))
            return f"👁️ {a} ({x},{y})"
        except: return "❌"

    # === FILES ===
    def _list_files(self, p):
        path = expand(p.get("path","."))
        if not os.path.exists(path): return f"❌ {path}"
        items = []
        for i in os.listdir(path):
            f = os.path.join(path,i); t = "📁" if os.path.isdir(f) else "📄"
            try: s = self._fmt(os.path.getsize(f))
            except: s = "?"
            items.append(f"{t} {i} ({s})")
        return "\n".join(items[:50]) if items else "Vazio"

    def _move_file(self, p):
        s,d = expand(p.get("source","")),expand(p.get("destination",""))
        if not os.path.exists(s): return f"❌ {s}"
        if os.path.lexists(d): return f"⛔ Destino ja existe: {d}"
        if os.path.dirname(d): os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.move(s,d)
        ok = os.path.exists(d) and not os.path.exists(s)
        return {"success": ok, "verified": ok, "result": f"→ {d}",
                "evidence": {"verifier": "filesystem", "source_absent": not os.path.exists(s), "destination": d}}

    def _copy_file(self, p):
        s,d = expand(p.get("source","")),expand(p.get("destination",""))
        if not os.path.exists(s): return f"❌ {s}"
        if os.path.lexists(d): return f"⛔ Destino ja existe: {d}"
        if os.path.dirname(d): os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.copytree(s,d) if os.path.isdir(s) else shutil.copy2(s,d)
        # Existence is observed, but content equality of a directory is not assumed.
        return {"success": os.path.exists(d), "verified": False, "result": f"→ {d}",
                "evidence": {"verifier": "filesystem", "destination": d}}

    def _create_folder(self, p):
        path = expand(p.get("path","")); os.makedirs(path,exist_ok=True)
        return {"success": os.path.isdir(path), "verified": os.path.isdir(path), "result": f"📁 {path}",
                "evidence": {"verifier": "filesystem", "directory": path}}

    def _delete_file(self, p):
        path = expand(p.get("path",""))
        if not os.path.exists(path): return "❌"
        from send2trash import send2trash
        send2trash(path)
        return {"success": not os.path.exists(path), "verified": not os.path.exists(path),
                "result": "Enviado para a lixeira.", "evidence": {"verifier": "filesystem_absence", "path": path}}

    def _read_file(self, p):
        path = expand(p.get("path",""))
        if not os.path.exists(path): return "❌"
        try:
            with open(path,"r",encoding="utf-8") as f: return f.read(5000)
        except: return "❌ Binário"

    def _write_file(self, p):
        path, content = expand(p.get("path","")), p.get("content","")
        if self.dry_run: return f"[SIM] Gravar {path} ({len(content)} chars)"
        if os.path.dirname(path): os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as f: f.write(content)
        return f"✅ {path} ({len(content)} chars)"

    # === PROJETO EXISTENTE (continuacao da conversa) ===
    def _edit_project(self, p):
        """Grava as alteracoes de um projeto guardando ANTES a versao anterior
        (projeto/.ai_versions/<data>/), para 'desfaz' voltar."""
        from core.project_versions import apply_edit
        folder, files = p.get("folder", ""), p.get("files") or []
        if self.dry_run:
            return f"[SIM] Editaria {len(files)} arquivo(s) em {folder}: " + \
                   ", ".join(f.get("path", "") for f in files)[:200]
        r = apply_edit(folder, files, expected_hashes=p.get('expected_hashes'))
        if not r["ok"]:
            return f"❌ {r['error']}"
        paths = [str(pathlib.Path(folder) / rel) for rel in r['changed']]
        return {"success": True, "verified": r.get('verified', False),
                "result": f"Projeto alterado e conteudo conferido. Versao anterior preservada.\nPasta: {folder}",
                "artifacts": {"folder": folder, "files": paths},
                "evidence": {"verifier": "filesystem", "scope": "artifact_content", "files": paths}}

    def _revert_project(self, p):
        from core.project_versions import revert_last
        folder = p.get("folder", "")
        if self.dry_run: return f"[SIM] Voltar a versão anterior de {folder}"
        r = revert_last(folder)
        if not r["ok"]:
            return f"❌ {r['error']}"
        return {"success": True, "verified": False,
                "result": f"Versao anterior restaurada ({', '.join(r['restored'])})\nPasta: {folder}"}

    def _find_files(self, p):
        path, pat = expand(p.get("path",".")), p.get("pattern","*")
        m = glob.glob(os.path.join(path,"**",pat),recursive=True)[:30]
        return "\n".join(f"📄 {f}" for f in m) if m else "Nenhum"

    # === CONTROL ===
    def _close_app(self, p):
        name = str(p.get('app_name') or '').strip().lower()
        if not name:
            return '⛔ Aplicativo alvo ausente.'
        window = gw.getActiveWindow()
        if not window or name not in (window.title or '').lower():
            return '⛔ A janela ativa nao corresponde ao aplicativo solicitado.'
        if not _bring_to_front(window._hWnd) or not _is_front(window._hWnd):
            return '⛔ Nao foi possivel confirmar a janela alvo.'
        pyautogui.hotkey('alt', 'f4')  # preserve native save/confirmation dialogs; never terminate processes
        return {'success': True, 'verified': False, 'result': 'Fechamento solicitado; confirme eventuais dialogos do aplicativo.'}

    def _run_command(self, p):
        command = p.get("command", "")
        if not isinstance(command, str) or not command.strip() or not safe(command):
            return {"success": False, "status": "rejected", "verified": False, "result": "Comando bloqueado ou vazio."}
        from core.process_runner import run_command
        return run_command(command, timeout=30, should_stop=getattr(self, "should_stop", None))

    def _type_text(self, p):
        text = p.get("text","")
        hwnd = p.get('hwnd') or getattr(self, '_doc_hwnd', None) or getattr(self, '_target_hwnd', None)
        if not hwnd or not _bring_to_front(hwnd) or not _is_front(hwnd):
            return '⛔ Digitar exige uma janela alvo confirmada.'
        if re.search(r'\b(cmd|powershell|terminal|command prompt)\b', _window_title(hwnd), re.I):
            return '⛔ Execucao de comandos por digitacao desativada.'
        try: from core.clipboard import paste_text; paste_text(text)
        except: pyautogui.write(text)
        return f"Digitado: {text[:60]}"

    def _hotkey(self, p):
        keys = p.get("keys",[])
        if isinstance(keys,str): keys = [k.strip() for k in keys.split("+")] if "+" in keys else [keys]
        try: pyautogui.hotkey(*keys); return f"⌨️ {'+'.join(keys)}"
        except Exception as e: return f"❌ {e}"

    def _click(self, p):
        try: x,y = int(p.get("x",0)),int(p.get("y",0))
        except: return "❌"
        sw,sh = pyautogui.size()
        if x<=0 or y<=0 or x>=sw or y>=sh: return f"❌ ({x},{y})"
        try: human_move(x,y); pyautogui.click(); return f"({x},{y})"
        except: return "❌ FailSafe"

    def _screenshot(self, p):
        fp = os.path.join("captures",f"ss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot().save(fp); return f"📸 {fp}"

    def _await_ready(self, baseline, max_s: float, min_s: float = READY_MIN_S, early=None):
        """Espera a janela que a acao anterior trouxe para frente ficar pronta (no maximo
        max_s). Devolve (segundos, pronta?). Sem janela nova, espera o tempo todo.
        Depois de abrir um app, so conta a janela DELE (o menu Iniciar fechando devolve a
        frente para outra janela por um instante; antes isso encerrava a espera cedo)."""
        expect = getattr(self, "_expect", None)
        t0 = time.time()
        last, since = None, t0
        while True:
            el = time.time() - t0
            if el >= max_s:
                return el, False
            cur = _fg_state()
            if cur != last:
                last, since = cur, time.time()
            changed = baseline is not None and cur != baseline and cur[1].strip()
            if changed and expect:
                changed = any(h in cur[1].lower() for h in expect)
            stable = time.time() - since
            if changed and el >= min_s and (
                    (stable >= READY_STABLE_S and _window_ready(cur[0]))
                    or (stable >= READY_SETTLED_S and _responsive(cur[0]))):
                return el, True
            stop = getattr(self, "should_stop", None)
            if stop and stop():
                return el, False
            if early is not None and early():
                return el, True
            time.sleep(0.1)

    def _wait(self, p):
        try:
            s = min(float(p.get("seconds", 1)), 30.0)
        except (TypeError, ValueError):
            s = 1.0
        if self.dry_run:
            return f"[SIM] ⏳ {s}s"
        if p.get("fixed") or self._fg_before is None:
            time.sleep(s); return f"⏳ {s}s"
        took, ready = self._await_ready(self._fg_before, s)
        return f"⏳ {took:.1f}s (pronto)" if ready else f"⏳ {s}s"

    # === WEB ===
    def _web_goto(self, p): return self.browser.goto(p.get("url",""))
    def _web_click(self, p): return self.browser.click_el(p.get("target","") or p.get("description",""))
    def _web_type(self, p): return self.browser.type_in(p.get("field","") or p.get("description",""), p.get("text",""))
    def _web_key(self, p): return self.browser.press(p.get("key","Enter"))
    def _web_screenshot(self, p):
        fp = os.path.join("captures",f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        return f"📸 {fp}" if self.browser.shot(fp) else "❌"
    def _web_read(self, p): return f"🌐 {self.browser.title()}\n{self.browser.text()[:500]}"
    def _web_new_tab(self, p): return self.browser.new_tab(p.get("url","about:blank"))

    @staticmethod
    def _fmt(b):
        for u in ["B","KB","MB","GB"]:
            if b < 1024: return f"{b:.0f}{u}"
            b /= 1024
        return f"{b:.0f}TB"
