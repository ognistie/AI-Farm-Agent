"""
VisionEngine v12 — OCR local antes da API Vision; zoom em resolucao cheia.
- find_element() tenta EasyOCR local primeiro (custo zero)
- Se OCR achar texto matching, retorna direto (economia ~60% chamadas Vision)
- So cai para Sonnet Vision quando OCR falhar/baixa confianca
- Minimiza janelas do AI Farm Agent para nao se ver na propria tela
- Coordenadas validadas para nao apontar para a taskbar
"""

import os, io, json, base64, time
import pyautogui
from PIL import Image
from core.ai_client import get_client
from core.config import get_config
from core.ocr_local import find_text_on_screen, read_screen_text

SYS = """Você localiza elementos em screenshots de Windows (PT-BR) para um clique de mouse.

REGRAS:
1. JSON puro, sem markdown, sem texto extra.
2. Coordenadas = CENTRO do elemento, em pixels DESTA imagem.
3. Ignore a barra de tarefas do Windows (faixa no fundo da tela com ícones pequenos) e a
   janela do próprio "AI Farm Agent". O alvo está DENTRO da janela do app/site citado.
4. Links e resultados de busca: mire no TEXTO do link (título azul/sublinhado), não no
   ícone, na URL cinza nem no espaço vazio ao lado. "Primeiro resultado" = primeiro
   resultado orgânico da página, abaixo da caixa de busca, ignorando anúncios ("Patrocinado").
5. Listas (e-mails, conversas, vídeos): "primeiro item" = linha mais alta da lista principal.
6. Em apps com barra lateral (Teams, WhatsApp), a barra lateral é a DO APP, não a do Windows.
7. confidence: 0.9+ só se o texto/ícone é inequívoco; <0.5 se está chutando.
   Se não achar, found=false e diga o que vê. Nunca invente coordenada."""


class VisionEngine:
    def __init__(self):
        self.model = get_config().get_model("vision")
        self.effort = get_config().get_effort("vision")
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
        # ─── OCR LOCAL FIRST ──────────────────────────────────────────
        # Se o `desc` parece com texto literal (botao "Enviar", aba "Chat",
        # etc.), tentamos resolver via EasyOCR sem custo. Apenas se falhar
        # ou retornar confianca baixa, caimos para a API Vision (Sonnet).
        # Economia tipica: 60% das chamadas que so precisavam ver texto.
        ocr_target = self._extract_ocr_target(desc)
        if ocr_target:
            try:
                hit = find_text_on_screen(ocr_target)
                if hit.get("found") and hit.get("confidence", 0) >= 0.6:
                    cx, cy = hit["center"]
                    # Valida que nao caiu na taskbar
                    if cy < self.screen_h - 60:
                        return {
                            "found": True,
                            "x": cx, "y": cy,
                            "width": hit["bbox"][2] - hit["bbox"][0],
                            "height": hit["bbox"][3] - hit["bbox"][1],
                            "confidence": hit["confidence"],
                            "element_text": hit["text"],
                            "context": "OCR local (sem custo de API)",
                            "method": "ocr_local",
                        }
            except Exception:
                pass  # Cai para API Vision

        # ─── API VISION FALLBACK ──────────────────────────────────────
        b64, orig, r = self.take_screenshot()
        img_w, img_h = int(orig.width * r), int(orig.height * r)

        # Calcula zona proibida (taskbar)
        taskbar_y = img_h - int(50 * r)

        prompt = f"""Encontre este elemento na tela: {desc}

Imagem: {img_w}x{img_h}px
ZONA PROIBIDA: NÃO retorne coordenadas com Y > {taskbar_y} (isso é a barra de tarefas do Windows, NÃO é parte do app)

O elemento está DENTRO da janela do app/site citado (nunca na barra de tarefas).

JSON: {{"found":true/false,"x":int,"y":int,"width":int,"height":int,"confidence":0.0-1.0,"element_text":"...","context":"onde o elemento está"}}
Se não encontrar: {{"found":false,"reason":"...","screen_description":"o que vejo na tela"}}"""

        res = self._call(prompt, b64)

        if res.get("found") and r != 1.0:
            for k in ["x", "y", "width", "height"]:
                if res.get(k): res[k] = int(res[k] / r)

        # Zoom: a imagem foi reduzida (1920 -> 1280) e links pequenos ficam com
        # poucos pixels. Recorta a regiao em resolucao cheia e pede o ponto exato.
        if res.get("found") and r < 1.0:
            res = self._refine(orig, desc, res)

        # Validação: rejeita coordenadas na taskbar
        if res.get("found"):
            real_y = res.get("y", 0)
            if real_y > self.screen_h - 60:
                res["found"] = False
                res["reason"] = f"Coordenada Y={real_y} está na barra de tarefas. Elemento errado."

        return res

    def _refine(self, orig, desc, res, box=(640, 400)):
        """Segundo passo: recorte em resolucao nativa ao redor do palpite."""
        try:
            bw, bh = box
            x0 = max(0, min(orig.width - bw, int(res["x"]) - bw // 2))
            y0 = max(0, min(orig.height - bh, int(res["y"]) - bh // 2))
            crop = orig.crop((x0, y0, x0 + bw, y0 + bh))
            buf = io.BytesIO(); crop.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            prompt = (f"Recorte ampliado ({bw}x{bh}px) de uma tela. Encontre: {desc}\n"
                      f"JSON: {{\"found\":true/false,\"x\":int,\"y\":int,\"confidence\":0.0-1.0,\"element_text\":\"...\"}}\n"
                      "Coordenadas em pixels DESTE recorte. Se o alvo nao esta no recorte, found=false.")
            fine = self._call(prompt, b64)
            if fine.get("found") and 0 <= fine.get("x", -1) < bw and 0 <= fine.get("y", -1) < bh:
                res = dict(res, x=x0 + int(fine["x"]), y=y0 + int(fine["y"]),
                           confidence=max(res.get("confidence", 0), fine.get("confidence", 0)),
                           element_text=fine.get("element_text") or res.get("element_text"),
                           method="vision_zoom")
        except Exception:
            pass   # fica com o palpite do primeiro passo
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

    @staticmethod
    def _extract_ocr_target(desc: str) -> str | None:
        """
        Extrai a string literal procuravel quando o `desc` segue padroes
        tipicos: 'botao "Enviar"', 'aba Chat', 'campo Mensagem'. Retorna
        a string pura ou None se nao for texto-procuravel (ex: 'icone
        triangular roxo' nao tem hint textual util).
        """
        if not desc:
            return None
        d = desc.strip()

        # Captura entre aspas: botao "Enviar" -> Enviar
        import re
        m = re.search(r'["“]([^"”]{2,40})["”]', d)
        if m:
            return m.group(1).strip()

        # Padrao "<tipo> X" onde X tem >= 2 chars e e a ultima palavra
        keywords = ("botao", "aba", "tab", "menu", "link", "campo",
                    "label", "texto", "opcao", "icone")
        d_low = d.lower()
        for kw in keywords:
            idx = d_low.find(kw + " ")
            if idx >= 0:
                rest = d[idx + len(kw):].strip()
                # Pega so a primeira palavra capitalizada/significativa
                tokens = rest.split()
                if tokens:
                    first = tokens[0].strip('.,;:"\'()[]')
                    if len(first) >= 2 and not first.lower() in {"de", "do", "da"}:
                        return first
        return None

    def _call(self, prompt, b64):
        for attempt in range(3):
            try:
                raw = get_client().message(
                    model=self.model, system=SYS, max_tokens=4000,
                    user_content=prompt, images=[{"base64": b64}],
                    effort=self.effort, agent="VISION")
                if raw.startswith("```"): raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"): raw = raw[:-3]
                return json.loads(raw.strip())
            except json.JSONDecodeError:
                if attempt < 2: continue
                return {"error": True, "message": "JSON inválido"}
            except Exception as e:
                if attempt < 2: time.sleep(1); continue
                return {"error": True, "message": str(e)}