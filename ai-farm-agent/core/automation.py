"""
AutomationEngine v7 — Universal. run_python para código dinâmico.
Workspace compartilhado entre passos. Auto-install de libs.
"""

import os, glob, shutil, subprocess, time, getpass, random, json, sys, traceback, re, math, csv, base64
import collections, pathlib, string
from datetime import datetime
import pyautogui, psutil
import pygetwindow as gw
from PIL import Image

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

BLOCKED_CMDS = ["rm -rf","rmdir /s","format c","del /f /s","shutdown","reg delete","diskpart","bcdedit"]
USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"

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
        for fn in [lambda:self.page.get_by_placeholder(field).first, lambda:self.page.get_by_role("textbox").first, lambda:self.page.get_by_role("searchbox").first]:
            try:
                loc=fn()
                if loc.is_visible(timeout=2000): loc.fill(text); return f"🌐 Digitou: '{text[:30]}'"
            except: pass
        try: self.page.fill(field, text, timeout=3000); return f"🌐 Digitou"
        except: return f"❌ '{field[:20]}'"

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


class AutomationEngine:
    def __init__(self):
        self.executed_steps = []
        self.dry_run = False
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
        }
        handler = MAP.get(action)
        if not handler:
            return {"success":False,"action":action,"result":f"Acao desconhecida: {action}","timestamp":ts}
        try:
            result = handler(params)
            ok = not (isinstance(result,str) and result.startswith("❌"))
            rec = {"success":ok,"action":action,"params":params,"result":result,"timestamp":ts,"dry_run":dry_run}
        except pyautogui.FailSafeException:
            sw,sh = pyautogui.size(); pyautogui.moveTo(sw//2,sh//2,duration=0.1)
            rec = {"success":False,"action":action,"params":params,"result":"FailSafe","timestamp":ts}
        except Exception as e:
            rec = {"success":False,"action":action,"params":params,"result":f"Erro: {e}","timestamp":ts}

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
    def _run_python(self, p):
        """Executa código Python com TODAS as libs padrão pré-carregadas."""
        code = p.get("code", "")
        desc = p.get("description", "código")
        if self.dry_run: return f"[SIM] {desc}"
        if not code: return "❌ Código vazio"

        code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)

        # Auto-install libs externas
        found = re.findall(r'^(?:import|from)\s+(\w+)', code, re.MULTILINE)
        stdlib = {"os","sys","json","time","datetime","pathlib","shutil","glob","re","math",
                  "csv","subprocess","io","base64","random","collections","string","traceback",
                  "getpass","hashlib","copy","tempfile","platform","typing","dataclasses",
                  "sqlite3","zipfile","configparser","itertools","functools","textwrap",
                  "contextlib","logging","calendar","statistics","uuid","pickle","struct",
                  "ctypes","threading","queue","heapq","operator","decimal","pprint"}
        for lib in found:
            if lib not in stdlib and lib not in sys.modules:
                try: __import__(lib)
                except ImportError:
                    print(f"  📦 Instalando {lib}...")
                    subprocess.run([sys.executable,"-m","pip","install",lib,"--break-system-packages","-q"],capture_output=True,timeout=60)

        # Globals com TUDO pré-importado
        g = {"__builtins__":__builtins__,"workspace":self.workspace,"BASE":BASE,"USERNAME":USERNAME,
             "os":os,"sys":sys,"json":json,"time":time,"datetime":datetime,
             "subprocess":subprocess,"shutil":shutil,"glob":glob,"re":re,
             "math":math,"csv":csv,"base64":base64,"pathlib":pathlib,
             "random":random,"collections":collections,"string":string,
             "traceback":traceback,"getpass":getpass}

        # Importa libs externas usadas no código
        for lib in found:
            if lib not in g:
                try: g[lib] = __import__(lib)
                except: pass

        # Executa
        import io as _io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = _io.StringIO(), _io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                exec(code, g)
            r = out.getvalue().strip() or "✅ OK"
            if err.getvalue().strip(): r += f"\n⚠️ {err.getvalue().strip()[:200]}"
            return f"🐍 {desc}\n{r[:500]}"
        except Exception as e:
            return f"❌ {desc}\n{traceback.format_exc().strip().split(chr(10))[-1]}"

    def _pip_install(self, p):
        """Instala biblioteca Python."""
        lib = p.get("library", "") or p.get("name", "")
        if self.dry_run: return f"[SIM] pip install {lib}"
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", lib, "--break-system-packages", "-q"],
                capture_output=True, text=True, timeout=60)
            if r.returncode == 0: return f"📦 {lib} instalado"
            return f"❌ Falha: {r.stderr[:200]}"
        except: return f"❌ Timeout instalando {lib}"

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
        if self.dry_run: return f"[SIM] {name}"
        if not name: return "❌ Nome vazio"
        pyautogui.press("win"); time.sleep(0.8)
        try:
            import pyperclip; pyperclip.copy(name); pyautogui.hotkey("ctrl","v")
        except: pyautogui.typewrite(name, interval=0.04) if name.isascii() else pyautogui.write(name)
        time.sleep(1.5); pyautogui.press("enter"); time.sleep(2)
        return f"✅ {name}"

    def _app_type(self, p):
        title, text = p.get("window_title",""), p.get("text","")
        if self.dry_run: return f"[SIM] Digitar em '{title}'"
        search = title.lower()
        for _ in range(8):
            try:
                for w in gw.getAllWindows():
                    if search in w.title.lower() and w.visible and w.title and not is_our_browser(w.title):
                        try:
                            if w.isMinimized: w.restore()
                            w.activate()
                        except:
                            try: import ctypes; ctypes.windll.user32.SetForegroundWindow(w._hWnd)
                            except: pass
                        time.sleep(0.4)
                        try: import pyperclip; pyperclip.copy(text); pyautogui.hotkey("ctrl","v")
                        except: pyautogui.write(text)
                        return f"✅ '{title[:25]}': {text[:40]}"
            except: pass
            time.sleep(0.4)
        return f"❌ Janela: '{title}'"

    # === FOCUS ===
    def _focus_window(self, p):
        title = p.get("title","")
        if self.dry_run: return f"[SIM] {title}"
        for _ in range(6):
            try:
                for w in gw.getAllWindows():
                    if title.lower() in w.title.lower() and w.visible and w.title and not is_our_browser(w.title):
                        try:
                            if w.isMinimized: w.restore()
                            w.activate()
                        except:
                            try: import ctypes; ctypes.windll.user32.SetForegroundWindow(w._hWnd)
                            except: pass
                        time.sleep(0.4); return f"🎯 {w.title[:40]}"
            except: pass
            time.sleep(0.4)
        return f"❌ '{title}'"

    # === VISION ===
    def _ensure_app_focus(self):
        """Garante que a janela ativa NÃO é o browser do AI Farm Agent."""
        try:
            active = gw.getActiveWindow()
            if active and is_our_browser(active.title):
                # Busca outra janela visível que não seja a nossa
                for w in gw.getAllWindows():
                    if w.visible and w.title.strip() and not is_our_browser(w.title):
                        try: w.activate(); time.sleep(0.3); return
                        except: pass
        except: pass

    def _vision_click(self, p):
        desc = p.get("description","")
        if self.dry_run: return f"[SIM] {desc}"
        if not self.vision: return "⚠️ Sem visão"

        self._ensure_app_focus()  # Garante foco no app certo

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

            if c < 0.15:
                if attempt == 0: time.sleep(1); continue
                return f"⚠️ Confiança muito baixa: {c:.0%}"

            # Clica
            human_move(x, y)
            time.sleep(0.15)
            pyautogui.click()
            time.sleep(0.4)
            return f"👁️ ({x},{y}) [{c:.0%}]"

        return f"❌ Falhou após 2 tentativas: {desc}"

    def _vision_type(self, p):
        desc, text = p.get("description",""), p.get("text","")
        if self.dry_run: return f"[SIM]"
        if not self.vision: return "⚠️ Sem visão"
        if not text: return "❌ Texto vazio"

        self._ensure_app_focus()  # Garante foco no app certo

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

            if c < 0.15:
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
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
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
        if os.path.dirname(d): os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.move(s,d); return f"→ {d}"

    def _copy_file(self, p):
        s,d = expand(p.get("source","")),expand(p.get("destination",""))
        if not os.path.exists(s): return f"❌ {s}"
        if os.path.dirname(d): os.makedirs(os.path.dirname(d),exist_ok=True)
        shutil.copytree(s,d) if os.path.isdir(s) else shutil.copy2(s,d); return f"→ {d}"

    def _create_folder(self, p):
        path = expand(p.get("path","")); os.makedirs(path,exist_ok=True); return f"📁 {path}"

    def _delete_file(self, p):
        path = expand(p.get("path",""))
        if not os.path.exists(path): return "❌"
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path); return "Deletado"

    def _read_file(self, p):
        path = expand(p.get("path",""))
        if not os.path.exists(path): return "❌"
        try:
            with open(path,"r",encoding="utf-8") as f: return f.read(5000)
        except: return "❌ Binário"

    def _write_file(self, p):
        path, content = expand(p.get("path","")), p.get("content","")
        if os.path.dirname(path): os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as f: f.write(content)
        return f"✅ {path} ({len(content)} chars)"

    def _find_files(self, p):
        path, pat = expand(p.get("path",".")), p.get("pattern","*")
        m = glob.glob(os.path.join(path,"**",pat),recursive=True)[:30]
        return "\n".join(f"📄 {f}" for f in m) if m else "Nenhum"

    # === CONTROL ===
    def _close_app(self, p):
        name = p.get("app_name","").lower()
        c = sum(1 for pr in psutil.process_iter(["name"]) if name in pr.info.get("name","").lower() and (pr.terminate() or True))
        return f"Fechado ({c})" if c else "Nenhum"

    def _run_command(self, p):
        cmd = p.get("command","")
        if not safe(cmd): return "⛔ Bloqueado"
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
            return f"$ {cmd}\n{r.stdout[:1500]}" + (f"\n⚠️ {r.stderr[:200]}" if r.stderr else "")
        except: return "Timeout"

    def _type_text(self, p):
        text = p.get("text","")
        focus_away(); time.sleep(0.15)
        try: import pyperclip; pyperclip.copy(text); pyautogui.hotkey("ctrl","v")
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

    def _wait(self, p):
        s = min(p.get("seconds",1),30); time.sleep(s); return f"⏳ {s}s"

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