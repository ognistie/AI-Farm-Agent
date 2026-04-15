"""
DesktopAgent v14 — Agente inteligente de apps desktop.
MUDANÇAS v14:
- REMOVIDO fallback 'Ola!' — nunca inventa conteúdo
- Notepad só digita se text não vazio
- Apps genéricos (Paint, Calculadora) com ação complexa → LLM resolve
- Prompt fallback com conhecimento real de como humanos usam apps
- Detecção de tarefa complexa vs simples
"""

import json
import os
from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse


def _build_steps(app, params):
    """Constroi steps para apps conhecidos."""
    action_type = (params.get("action_type", "") or "").lower()
    person = params.get("person", "") or ""
    message = params.get("message", "") or params.get("text", "") or ""
    text = params.get("text", "") or message
    steps = []
    n = [0]

    def add(action, p, desc):
        n[0] += 1
        steps.append({"step": n[0], "action": action, "params": p, "description": desc, "agent": "DESKTOP"})

    # === TEAMS ===
    if app in ("teams", "microsoft teams"):
        add("app_search", {"name": "Microsoft Teams"}, "Abrir Teams")
        add("wait", {"seconds": 5}, "Aguardar Teams carregar")
        add("focus_window", {"title": "Teams"}, "Focar janela do Teams")
        add("wait", {"seconds": 1}, "Aguardar foco")
        add("vision_click", {"description": "texto 'Chat' na barra lateral esquerda DENTRO da janela do Teams"}, "Ir para aba Chat")
        add("wait", {"seconds": 2}, "Aguardar lista de chats")
        add("hotkey", {"keys": ["ctrl", "shift", "f"]}, "Filtrar chats")
        add("wait", {"seconds": 1}, "Aguardar campo de filtro")
        add("type_text", {"text": person}, "Filtrar por: " + person)
        add("wait", {"seconds": 2}, "Aguardar resultados")
        add("vision_click", {"description": "conversa com " + person + " na lista filtrada DENTRO do Teams"}, "Abrir conversa")
        add("wait", {"seconds": 2}, "Aguardar conversa")
        add("vision_click", {"description": "campo de texto 'Digite uma mensagem' na PARTE INFERIOR da conversa DENTRO do Teams"}, "Focar campo")
        add("wait", {"seconds": 0.5}, "Aguardar")
        if action_type in ("send_message", "") and message:
            add("type_text", {"text": message}, "Digitar: " + message[:40])
            add("wait", {"seconds": 1}, "Aguardar")
            add("hotkey", {"keys": ["enter"]}, "Enviar")
        elif action_type == "call":
            add("vision_click", {"description": "icone de telefone no canto superior direito DENTRO do Teams"}, "Ligar")
        elif action_type == "video_call":
            add("vision_click", {"description": "icone de camera no canto superior direito DENTRO do Teams"}, "Video")
        add("hotkey", {"keys": ["escape"]}, "Limpar filtro")
        return steps

    # === WHATSAPP ===
    if app in ("whatsapp", "whats", "zap"):
        add("app_search", {"name": "WhatsApp"}, "Abrir WhatsApp")
        add("wait", {"seconds": 4}, "Aguardar")
        add("focus_window", {"title": "WhatsApp"}, "Focar WhatsApp")
        add("wait", {"seconds": 1}, "Aguardar")
        add("vision_click", {"description": "campo de pesquisa com lupa NO TOPO da barra lateral DENTRO do WhatsApp"}, "Pesquisa")
        add("wait", {"seconds": 1}, "Aguardar")
        add("type_text", {"text": person}, "Pesquisar: " + person)
        add("wait", {"seconds": 2}, "Aguardar busca")
        add("vision_click", {"description": "resultado com " + person + " DENTRO do WhatsApp"}, person)
        add("wait", {"seconds": 2}, "Aguardar conversa")
        add("vision_click", {"description": "campo 'Digite uma mensagem' na parte inferior DENTRO do WhatsApp"}, "Focar campo")
        if message:
            add("type_text", {"text": message}, "Digitar mensagem")
            add("hotkey", {"keys": ["enter"]}, "Enviar")
        return steps

    # === NOTEPAD ===
    if app in ("notepad", "bloco de notas"):
        add("app_search", {"name": "Bloco de Notas"}, "Abrir Notepad")
        add("wait", {"seconds": 3}, "Aguardar abrir")
        if text and text.strip():
            add("app_type", {"window_title": "Notas", "text": text}, "Digitar texto")
        return steps

    # === WORD ===
    if app in ("word", "microsoft word"):
        add("app_search", {"name": "Word"}, "Abrir Word")
        add("wait", {"seconds": 5}, "Aguardar")
        add("vision_click", {"description": "opcao Documento em branco na tela inicial DENTRO do Word"}, "Novo documento")
        add("wait", {"seconds": 3}, "Aguardar")
        if text and text.strip():
            add("type_text", {"text": text}, "Digitar texto")
        return steps

    # === EXCEL ===
    if app in ("excel", "microsoft excel"):
        add("app_search", {"name": "Excel"}, "Abrir Excel")
        add("wait", {"seconds": 5}, "Aguardar")
        add("vision_click", {"description": "opcao Pasta de trabalho em branco na tela inicial DENTRO do Excel"}, "Nova planilha")
        add("wait", {"seconds": 3}, "Aguardar")
        return steps

    # === VS CODE ===
    if app in ("vscode", "vs code", "visual studio code"):
        add("app_search", {"name": "Visual Studio Code"}, "Abrir VS Code")
        add("wait", {"seconds": 4}, "Aguardar")
        return steps

    # === APPS GENÉRICOS (só abre se tarefa é simples) ===
    generic = {"paint": "Paint", "calculadora": "Calculadora", "calculator": "Calculadora", "spotify": "Spotify"}
    if app in generic:
        if action_type and action_type not in ("open", ""):
            return None  # Tarefa complexa → LLM resolve
        add("app_search", {"name": generic[app]}, "Abrir " + generic[app])
        add("wait", {"seconds": 3}, "Aguardar")
        return steps

    if app in ("explorer", "explorador"):
        add("hotkey", {"keys": ["win", "e"]}, "Abrir Explorer (Win+E)")
        add("wait", {"seconds": 2}, "Aguardar")
        return steps

    # === OUTLOOK ===
    if app == "outlook":
        add("app_search", {"name": "Outlook"}, "Abrir Outlook")
        add("wait", {"seconds": 5}, "Aguardar")
        add("hotkey", {"keys": ["ctrl", "n"]}, "Novo Email (Ctrl+N)")
        add("wait", {"seconds": 2}, "Aguardar")
        if person:
            add("type_text", {"text": person}, "Destinatario")
            add("hotkey", {"keys": ["tab"]}, "Tab")
        add("hotkey", {"keys": ["tab"]}, "Tab para corpo")
        if message:
            add("type_text", {"text": message}, "Corpo")
        add("hotkey", {"keys": ["ctrl", "enter"]}, "Enviar (Ctrl+Enter)")
        return steps

    return None


PROMPT_FALLBACK = (
    "Voce e o DESKTOP AGENT — especialista em operar apps Windows como um humano.\n"
    "Pense passo a passo: o que um usuario faria para cumprir esta tarefa?\n\n"
    "ACOES DISPONIVEIS:\n"
    "- app_search(name): abre app pelo menu iniciar\n"
    "- app_type(window_title, text): digita texto na janela com esse titulo\n"
    "- focus_window(title): foca uma janela\n"
    "- vision_click(description): clica em elemento visual DENTRO do app\n"
    "- vision_type(description, text): clica em campo e digita\n"
    "- type_text(text): digita via clipboard no campo ativo\n"
    "- hotkey(keys): atalho (ex: ['ctrl','n'])\n"
    "- wait(seconds): espera\n"
    "- click(x, y): clique em coordenada\n\n"
    "CONHECIMENTO DE APPS:\n"
    "- Paint: Pincel ja vem selecionado. Para desenhar, use click(x,y) em sequencia.\n"
    "  Para formas: vision_click('ferramenta Retangulo') → click e arraste.\n"
    "  Para cores: vision_click('cor vermelha na paleta de cores').\n"
    "- Calculadora: vision_click('botao 5'), vision_click('botao +'), etc.\n"
    "- Spotify: vision_click('campo de pesquisa') → type_text(consulta).\n\n"
    "REGRAS CRITICAS:\n"
    "- SEMPRE wait(3-5) apos abrir app\n"
    "- Descricoes de vision_click DENTRO DO APP (nunca taskbar)\n"
    "- NUNCA invente texto que o usuario nao pediu\n"
    "- Se o usuario nao pediu para escrever nada, NAO escreva\n"
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

        # Tenta rotina hardcoded ($0)
        if app:
            steps = _build_steps(app, params)
            if steps:
                print(f"  [DESKTOP] Rotina: {len(steps)} steps ($0)")
                return {"steps": steps, "agent": "DESKTOP"}

        # Detecção por keyword com inteligência
        task_lower = str(task_text).lower()
        complex_keywords = ["desenh", "pint", "calcul", "som", "toc", "play", "ouç", "escrev", "digit"]

        # Verifica se a tarefa pede ação complexa em app genérico
        task_is_complex = any(ck in task_lower for ck in complex_keywords)

        for kw, detected in {
            "teams": "teams", "whatsapp": "whatsapp", "whats": "whatsapp",
            "notepad": "notepad", "bloco de notas": "notepad", "word": "word",
            "excel": "excel", "vscode": "vscode", "vs code": "vscode",
            "paint": "paint", "calculadora": "calculadora",
            "spotify": "spotify", "explorer": "explorer",
        }.items():
            if kw in task_lower:
                # Apps genéricos com tarefa complexa → LLM
                if detected in ("paint", "calculadora", "calculator", "spotify") and task_is_complex:
                    break
                steps = _build_steps(detected, {"app": detected, "action_type": "open"})
                if steps:
                    return {"steps": steps, "agent": "DESKTOP"}

        # LLM fallback — o agente pensa como humano
        print("  [DESKTOP] LLM fallback ($)")
        try:
            raw = self._client.message(
                model=self.model,
                system=PROMPT_FALLBACK,
                user_content=f"TAREFA: {task_text}\nJSON puro.",
                max_tokens=3000,
            )
            plan = safe_parse(raw, self.model)
            for st in plan.get("steps", []):
                st["agent"] = "DESKTOP"
            return {"steps": plan.get("steps", []), "agent": "DESKTOP"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "DESKTOP"}