"""
VisionEngine v10 — Visão computacional corrigida.
- Minimiza TODOS os browsers/janelas do AI Farm Agent
- Instrui a IA a IGNORAR a barra de tarefas
- Coordenadas retornadas são validadas
- Nunca restaura browser automaticamente (server controla isso)
"""

import os, io, json, base64, time
import pyautogui
from PIL import Image
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYS = """Você analisa screenshots de computador Windows PT-BR com PRECISÃO CIRÚRGICA.

REGRAS CRÍTICAS:
1. JSON puro, sem markdown, sem texto extra
2. Coordenadas = centro EXATO do elemento em pixels da imagem
3. IGNORE COMPLETAMENTE a barra de tarefas do Windows (barra escura na parte INFERIOR da tela com ícones pequenos)
4. Se o elemento pedido está DENTRO de um aplicativo, as coordenadas devem ser DENTRO da janela do app, NUNCA na taskbar
5. O campo de mensagem em apps de chat (Teams, WhatsApp) fica na PARTE INFERIOR da JANELA DO APP (não da tela)
6. Botões de navegação em apps (Chat, Equipes, etc) ficam na BARRA LATERAL ESQUERDA DENTRO DO APP

DIFERENÇA IMPORTANTE:
- Barra de tarefas do WINDOWS = faixa escura no fundo da TELA com ícones minúsculos (IGNORE)
- Barra lateral do APP = coluna de ícones/textos dentro da JANELA do aplicativo (USE ESTA)

Quando procurar um botão como "Chat" no Teams:
- NÃO clique no ícone do Teams na barra de tarefas do Windows
- CLIQUE no texto/ícone "Chat" DENTRO da janela do Microsoft Teams"""


class VisionEngine:
    def __init__(self):
        self.model = "claude-sonnet-4-20250514"
        self.screen_w, self.screen_h = pyautogui.size()
        self.last_img = None
        self._hidden_windows = []

    def take_screenshot(self):
        """Minimiza TODAS as janelas do AI Farm Agent antes de capturar."""
        self._hidden_windows = []
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if w.visible and w.title:
                    t = w.title.lower()
                    if "127.0.0.1" in t or "ai farm" in t or "localhost:5000" in t or "localhost" in t:
                        try:
                            self._hidden_windows.append(w)
                            w.minimize()
                        except: pass
            if self._hidden_windows:
                time.sleep(0.5)  # espera todas minimizarem
        except: pass

        img = pyautogui.screenshot()
        self.last_img = img

        # Reduz para 1280px max
        mx = 1280
        if img.width > mx or img.height > mx:
            r = min(mx / img.width, mx / img.height)
            resized = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
        else:
            resized, r = img, 1.0

        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode(), img, r

    def restore_browser(self):
        """Restaura janelas minimizadas."""
        for w in self._hidden_windows:
            try: w.restore()
            except: pass
        self._hidden_windows = []

    def find_element(self, desc):
        b64, orig, r = self.take_screenshot()
        img_w, img_h = int(orig.width * r), int(orig.height * r)

        # Calcula zona proibida (taskbar)
        taskbar_y = img_h - int(50 * r)

        prompt = f"""Encontre este elemento na tela: {desc}

Imagem: {img_w}x{img_h}px
ZONA PROIBIDA: NÃO retorne coordenadas com Y > {taskbar_y} (isso é a barra de tarefas do Windows, NÃO é parte do app)

Se o elemento é um botão/ícone DENTRO de um aplicativo:
- As coordenadas devem estar DENTRO da janela do app
- A barra lateral de apps como Teams fica no LADO ESQUERDO da janela, com Y entre 100 e 600 aproximadamente

JSON: {{"found":true/false,"x":int,"y":int,"width":int,"height":int,"confidence":0.0-1.0,"element_text":"...","context":"onde o elemento está"}}
Se não encontrar: {{"found":false,"reason":"...","screen_description":"o que vejo na tela"}}"""

        res = self._call(prompt, b64)

        if res.get("found") and r != 1.0:
            for k in ["x", "y", "width", "height"]:
                if res.get(k): res[k] = int(res[k] / r)

        # Validação: rejeita coordenadas na taskbar
        if res.get("found"):
            real_y = res.get("y", 0)
            if real_y > self.screen_h - 60:
                res["found"] = False
                res["reason"] = f"Coordenada Y={real_y} está na barra de tarefas. Elemento errado."

        return res

    def analyze_screen(self):
        b64, orig, r = self.take_screenshot()
        prompt = f"""Descreva a tela ({int(orig.width*r)}x{int(orig.height*r)}px).
JSON: {{"active_window":"...","screen_description":"...","visible_elements":[{{"type":"...","text":"...","x":int,"y":int}}]}}
Max 10 elementos. Ignore a barra de tarefas do Windows."""
        res = self._call(prompt, b64)
        if r != 1.0:
            for e in res.get("visible_elements", []):
                if e.get("x"): e["x"] = int(e["x"] / r)
                if e.get("y"): e["y"] = int(e["y"] / r)
        return res

    def smart_action(self, goal):
        b64, orig, r = self.take_screenshot()
        prompt = f"""Objetivo: {goal}
JSON: {{"action":"click/type/hotkey/none","x":int,"y":int,"text_to_type":"","keys":[],"confidence":0.0-1.0,"reasoning":"..."}}
NUNCA retorne coordenadas na barra de tarefas (últimos 50px da tela)."""
        res = self._call(prompt, b64)
        if r != 1.0:
            if res.get("x"): res["x"] = int(res["x"] / r)
            if res.get("y"): res["y"] = int(res["y"] / r)
        return res

    def verify_state(self, expected):
        b64, _, _ = self.take_screenshot()
        prompt = f"""Verificar: {expected}
JSON: {{"verified":true/false,"match_confidence":0.0-1.0,"actual_state":"..."}}"""
        return self._call(prompt, b64)

    def _call(self, prompt, b64):
        for attempt in range(3):
            try:
                resp = client.messages.create(
                    model=self.model, max_tokens=2048, system=SYS,
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                        {"type": "text", "text": prompt}
                    ]}])
                raw = resp.content[0].text.strip()
                if raw.startswith("```"): raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"): raw = raw[:-3]
                return json.loads(raw.strip())
            except json.JSONDecodeError:
                if attempt < 2: continue
                return {"error": True, "message": "JSON inválido"}
            except Exception as e:
                if attempt < 2: time.sleep(1); continue
                return {"error": True, "message": str(e)}