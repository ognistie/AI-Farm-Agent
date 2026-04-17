"""
DesktopAgent v16 — Rotinas utilitárias + Few-shot LLM.
- NOVAS: minimize_all, close_all, screenshot, alt_tab, lock, volume
- Few-shot no prompt LLM (Paint círculo, Calculadora 15+20, Spotify lofi)
- Sem 'Ola!', Paint→LLM, Notepad sem digitar vazio
"""

import json, os
from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse


def _build_steps(app, params):
    action_type = (params.get("action_type", "") or "").lower()
    person = params.get("person", "") or ""
    message = params.get("message", "") or params.get("text", "") or ""
    text = params.get("text", "") or message
    steps = []
    n = [0]

    def add(action, p, desc):
        n[0] += 1
        steps.append({"step": n[0], "action": action, "params": p, "description": desc, "agent": "DESKTOP"})

    if app in ("teams", "microsoft teams"):
        add("app_search", {"name": "Microsoft Teams"}, "Abrir Teams")
        add("wait", {"seconds": 5}, "Aguardar")
        add("focus_window", {"title": "Teams"}, "Focar")
        add("wait", {"seconds": 1}, "Aguardar")
        add("vision_click", {"description": "texto 'Chat' na barra lateral esquerda DENTRO do Teams"}, "Chat")
        add("wait", {"seconds": 2}, "Aguardar")
        add("hotkey", {"keys": ["ctrl", "shift", "f"]}, "Filtrar")
        add("wait", {"seconds": 1}, "Aguardar")
        add("type_text", {"text": person}, "Filtrar: " + person)
        add("wait", {"seconds": 2}, "Aguardar")
        add("vision_click", {"description": "conversa com " + person + " DENTRO do Teams"}, "Abrir")
        add("wait", {"seconds": 2}, "Aguardar")
        add("vision_click", {"description": "campo 'Digite uma mensagem' na PARTE INFERIOR DENTRO do Teams"}, "Focar")
        add("wait", {"seconds": 0.5}, "Aguardar")
        if action_type in ("send_message", "") and message:
            add("type_text", {"text": message}, "Digitar")
            add("wait", {"seconds": 1}, "Aguardar")
            add("hotkey", {"keys": ["enter"]}, "Enviar")
        elif action_type == "call":
            add("vision_click", {"description": "icone de telefone DENTRO do Teams"}, "Ligar")
        elif action_type == "video_call":
            add("vision_click", {"description": "icone de camera DENTRO do Teams"}, "Video")
        add("hotkey", {"keys": ["escape"]}, "Limpar")
        return steps

    if app in ("whatsapp", "whats", "zap"):
        add("app_search", {"name": "WhatsApp"}, "Abrir WhatsApp")
        add("wait", {"seconds": 4}, "Aguardar")
        add("focus_window", {"title": "WhatsApp"}, "Focar")
        add("wait", {"seconds": 1}, "Aguardar")
        add("vision_click", {"description": "campo de pesquisa DENTRO do WhatsApp"}, "Pesquisa")
        add("wait", {"seconds": 1}, "Aguardar")
        add("type_text", {"text": person}, "Pesquisar")
        add("wait", {"seconds": 2}, "Aguardar")
        add("vision_click", {"description": "resultado " + person + " DENTRO do WhatsApp"}, person)
        add("wait", {"seconds": 2}, "Aguardar")
        add("vision_click", {"description": "campo 'Digite uma mensagem' DENTRO do WhatsApp"}, "Focar")
        if message:
            add("type_text", {"text": message}, "Digitar")
            add("hotkey", {"keys": ["enter"]}, "Enviar")
        return steps

    if app in ("notepad", "bloco de notas"):
        add("app_search", {"name": "Bloco de Notas"}, "Abrir Notepad")
        add("wait", {"seconds": 3}, "Aguardar")
        if text and text.strip():
            add("app_type", {"window_title": "Notas", "text": text}, "Digitar")
        return steps

    if app in ("word", "microsoft word"):
        add("app_search", {"name": "Word"}, "Abrir Word")
        add("wait", {"seconds": 5}, "Aguardar")
        add("vision_click", {"description": "Documento em branco DENTRO do Word"}, "Novo")
        add("wait", {"seconds": 3}, "Aguardar")
        if text and text.strip():
            add("type_text", {"text": text}, "Digitar")
        return steps

    if app in ("excel", "microsoft excel"):
        add("app_search", {"name": "Excel"}, "Abrir Excel")
        add("wait", {"seconds": 5}, "Aguardar")
        add("vision_click", {"description": "Pasta de trabalho em branco DENTRO do Excel"}, "Nova")
        add("wait", {"seconds": 3}, "Aguardar")
        return steps

    if app in ("vscode", "vs code", "visual studio code"):
        add("app_search", {"name": "Visual Studio Code"}, "Abrir VS Code")
        add("wait", {"seconds": 4}, "Aguardar")
        return steps

    generic = {"paint": "Paint", "calculadora": "Calculadora", "calculator": "Calculadora", "spotify": "Spotify"}
    if app in generic:
        if action_type and action_type not in ("open", ""):
            return None
        add("app_search", {"name": generic[app]}, "Abrir " + generic[app])
        add("wait", {"seconds": 3}, "Aguardar")
        return steps

    if app in ("explorer", "explorador"):
        add("hotkey", {"keys": ["win", "e"]}, "Abrir Explorer")
        add("wait", {"seconds": 2}, "Aguardar")
        return steps

    if app == "outlook":
        add("app_search", {"name": "Outlook"}, "Abrir Outlook")
        add("wait", {"seconds": 5}, "Aguardar")
        add("hotkey", {"keys": ["ctrl", "n"]}, "Novo")
        add("wait", {"seconds": 2}, "Aguardar")
        if person:
            add("type_text", {"text": person}, "Para")
            add("hotkey", {"keys": ["tab"]}, "Tab")
        add("hotkey", {"keys": ["tab"]}, "Tab")
        if message:
            add("type_text", {"text": message}, "Corpo")
        add("hotkey", {"keys": ["ctrl", "enter"]}, "Enviar")
        return steps

    return None


def _utility_steps(task_lower):
    s = lambda n, a, p, d: {"step": n, "action": a, "params": p, "description": d, "agent": "DESKTOP"}

    if any(kw in task_lower for kw in ["minimize tudo", "minimizar tudo", "minimizar todas", "minimize todas", "mostrar desktop", "mostrar area de trabalho"]):
        return [s(1, "hotkey", {"keys": ["win", "d"]}, "Minimizar tudo (Win+D)")]

    if any(kw in task_lower for kw in ["feche tudo", "fechar tudo", "feche todos", "fechar todos"]):
        return [s(1, "hotkey", {"keys": ["alt", "f4"]}, "Fechar janela"),
                s(2, "wait", {"seconds": 1}, "Aguardar"),
                s(3, "hotkey", {"keys": ["alt", "f4"]}, "Fechar próxima"),
                s(4, "wait", {"seconds": 1}, "Aguardar"),
                s(5, "hotkey", {"keys": ["alt", "f4"]}, "Fechar próxima")]

    if any(kw in task_lower for kw in ["print da tela", "screenshot", "captura de tela", "tire um print", "tirar print"]):
        return [s(1, "run_python", {
            "code": "import pyautogui, os, subprocess\nfrom datetime import datetime\ndesktop = os.path.join(os.path.expanduser('~'), 'Desktop')\nfp = os.path.join(desktop, f'screenshot_{datetime.now().strftime(\"%H%M%S\")}.png')\npyautogui.screenshot().save(fp)\nsubprocess.Popen(['explorer', '/select,', fp])\nprint(f'Salvo: {fp}')",
            "description": "Capturar tela"}, "Screenshot → Desktop")]

    if any(kw in task_lower for kw in ["volta pra tela", "trocar janela", "alt tab", "janela anterior"]):
        return [s(1, "hotkey", {"keys": ["alt", "tab"]}, "Alt+Tab")]

    if any(kw in task_lower for kw in ["bloquear tela", "bloquear pc", "lock", "travar tela"]):
        return [s(1, "hotkey", {"keys": ["win", "l"]}, "Bloquear (Win+L)")]

    if "aumentar volume" in task_lower or "volume mais alto" in task_lower:
        return [s(1, "hotkey", {"keys": ["volumeup"]}, "Vol+"),
                s(2, "hotkey", {"keys": ["volumeup"]}, "Vol+"),
                s(3, "hotkey", {"keys": ["volumeup"]}, "Vol+")]
    if "diminuir volume" in task_lower or "abaixar volume" in task_lower:
        return [s(1, "hotkey", {"keys": ["volumedown"]}, "Vol-"),
                s(2, "hotkey", {"keys": ["volumedown"]}, "Vol-"),
                s(3, "hotkey", {"keys": ["volumedown"]}, "Vol-")]
    if "mutar" in task_lower or "silenciar" in task_lower or "mudo" in task_lower:
        return [s(1, "hotkey", {"keys": ["volumemute"]}, "Mutar")]

    return None


PROMPT_FALLBACK = (
    "Voce e o DESKTOP AGENT — especialista em operar apps Windows.\n"
    "Pense como humano: o que faria passo a passo?\n\n"
    "ACOES:\n"
    "app_search(name) | app_type(window_title, text) | focus_window(title)\n"
    "vision_click(description) | vision_type(description, text)\n"
    "type_text(text) | hotkey(keys) | wait(seconds) | click(x,y)\n"
    "run_python(code, description)\n\n"

    "═══ EXEMPLOS (few-shot) ═══\n\n"

    "Tarefa: 'abra o paint e desenhe um circulo'\n"
    '{"steps":['
    '{"step":1,"action":"app_search","params":{"name":"Paint"},"description":"Abrir Paint"},'
    '{"step":2,"action":"wait","params":{"seconds":4},"description":"Aguardar"},'
    '{"step":3,"action":"vision_click","params":{"description":"ferramenta Circulo ou Oval DENTRO do Paint"},"description":"Selecionar circulo"},'
    '{"step":4,"action":"wait","params":{"seconds":0.5},"description":"Aguardar"},'
    '{"step":5,"action":"click","params":{"x":400,"y":350},"description":"Ponto inicial"},'
    '{"step":6,"action":"run_python","params":{"code":"import pyautogui; pyautogui.drag(200,200,duration=0.5)","description":"Arrastar"},"description":"Desenhar"}'
    ']}\n\n'

    "Tarefa: 'abra a calculadora e calcule 15+20'\n"
    '{"steps":['
    '{"step":1,"action":"app_search","params":{"name":"Calculadora"},"description":"Abrir"},'
    '{"step":2,"action":"wait","params":{"seconds":3},"description":"Aguardar"},'
    '{"step":3,"action":"vision_click","params":{"description":"botao 1 na calculadora"},"description":"1"},'
    '{"step":4,"action":"vision_click","params":{"description":"botao 5 na calculadora"},"description":"5"},'
    '{"step":5,"action":"vision_click","params":{"description":"botao + na calculadora"},"description":"+"},'
    '{"step":6,"action":"vision_click","params":{"description":"botao 2 na calculadora"},"description":"2"},'
    '{"step":7,"action":"vision_click","params":{"description":"botao 0 na calculadora"},"description":"0"},'
    '{"step":8,"action":"vision_click","params":{"description":"botao = na calculadora"},"description":"="}'
    ']}\n\n'

    "Tarefa: 'abra o spotify e toque musica lofi'\n"
    '{"steps":['
    '{"step":1,"action":"app_search","params":{"name":"Spotify"},"description":"Abrir"},'
    '{"step":2,"action":"wait","params":{"seconds":5},"description":"Aguardar"},'
    '{"step":3,"action":"vision_click","params":{"description":"campo Pesquisar DENTRO do Spotify"},"description":"Pesquisa"},'
    '{"step":4,"action":"wait","params":{"seconds":1},"description":"Aguardar"},'
    '{"step":5,"action":"type_text","params":{"text":"lofi"},"description":"lofi"},'
    '{"step":6,"action":"hotkey","params":{"keys":["enter"]},"description":"Buscar"},'
    '{"step":7,"action":"wait","params":{"seconds":2},"description":"Aguardar"},'
    '{"step":8,"action":"vision_click","params":{"description":"primeira playlist DENTRO do Spotify"},"description":"Tocar"}'
    ']}\n\n'

    "REGRAS:\n"
    "- SEMPRE wait(3-5) apos abrir app\n"
    "- Descricoes DENTRO DO APP (nunca taskbar)\n"
    "- NUNCA invente texto que o usuario nao pediu\n"
    "- Maximo 15 passos. JSON puro.\n\n"
    '{"steps":[{"step":1,"description":"...","action":"...","params":{}}]}'
)


class DesktopAgent:
    def __init__(self):
        self._config = get_config()
        self._client = get_client()
        self.model = self._config.get_model("desktop")
        self.name = "DESKTOP"

    def plan(self, task, context=None):
        params = {}
        task_text = task
        if isinstance(task, dict):
            params = task.get("params", {})
            task_text = task.get("task", str(task))
        if isinstance(context, dict) and "app" in context:
            params = context

        app = (params.get("app", "") or "").lower().strip()
        task_lower = str(task_text).lower()

        if app:
            steps = _build_steps(app, params)
            if steps:
                print(f"  [DESKTOP] Rotina: {len(steps)} steps ($0)")
                return {"steps": steps, "agent": "DESKTOP"}

        util = _utility_steps(task_lower)
        if util:
            print(f"  [DESKTOP] Utilitário: {len(util)} steps ($0)")
            return {"steps": util, "agent": "DESKTOP"}

        complex_kw = ["desenh", "pint", "calcul", "som", "toc", "play", "ouç"]
        is_complex = any(ck in task_lower for ck in complex_kw)

        for kw, detected in {
            "teams": "teams", "whatsapp": "whatsapp", "whats": "whatsapp",
            "notepad": "notepad", "bloco de notas": "notepad", "word": "word",
            "excel": "excel", "vscode": "vscode", "vs code": "vscode",
            "paint": "paint", "calculadora": "calculadora",
            "spotify": "spotify", "explorer": "explorer",
        }.items():
            if kw in task_lower:
                if detected in ("paint", "calculadora", "calculator", "spotify") and is_complex:
                    break
                steps = _build_steps(detected, {"app": detected, "action_type": "open"})
                if steps:
                    return {"steps": steps, "agent": "DESKTOP"}

        print("  [DESKTOP] LLM fallback ($)")
        try:
            raw = self._client.message(
                model=self.model, system=PROMPT_FALLBACK,
                user_content=f"TAREFA: {task_text}\nJSON puro.", max_tokens=3000,
            )
            plan = safe_parse(raw, self.model)
            for st in plan.get("steps", []): st["agent"] = "DESKTOP"
            return {"steps": plan.get("steps", []), "agent": "DESKTOP"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "DESKTOP"}