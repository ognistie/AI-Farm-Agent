"""
DesktopAgent v12 — Fix Teams: vai para Chat PRIMEIRO, depois pesquisa.
O Ctrl+E pesquisa globalmente e abre Connections. Errado.
A sequencia correta:
1. Abrir Teams
2. Clicar na aba Chat na barra lateral
3. Clicar na barra de pesquisa OU usar atalho para filtrar chats
4. Digitar nome da pessoa
5. Clicar na conversa que aparece
6. Digitar mensagem
7. Enviar
"""

import json, os
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _build_steps(app, params):
    """Constroi steps usando atalhos + vision preciso."""
    action_type = (params.get("action_type", "") or "").lower()
    person = params.get("person", "") or ""
    message = params.get("message", "") or params.get("text", "") or "Ola!"
    text = params.get("text", "") or message
    steps = []
    n = [0]

    def add(action, p, desc):
        n[0] += 1
        steps.append({"step": n[0], "action": action, "params": p, "description": desc, "agent": "DESKTOP"})

    # === TEAMS ===
    # Fluxo correto: Chat primeiro, depois pesquisa DENTRO do chat
    if app in ("teams", "microsoft teams"):
        add("app_search", {"name": "Microsoft Teams"}, "Abrir Teams")
        add("wait", {"seconds": 5}, "Aguardar Teams carregar")
        add("focus_window", {"title": "Teams"}, "Focar janela do Teams")
        add("wait", {"seconds": 1}, "Aguardar foco")
        # 1. Vai para a aba Chat clicando nela (garante contexto de chat)
        add("vision_click", {"description": "texto 'Chat' na barra lateral esquerda DENTRO da janela do Teams, e um dos icones na coluna vertical do lado esquerdo com texto 'Chat' embaixo"}, "Ir para aba Chat")
        add("wait", {"seconds": 2}, "Aguardar lista de chats carregar")
        # 2. Usa o campo de filtro/busca que aparece DENTRO da area de Chat
        #    No Teams novo, tem um icone de filtro ou campo no topo da lista de chats
        add("hotkey", {"keys": ["ctrl", "shift", "f"]}, "Filtrar chats (Ctrl+Shift+F)")
        add("wait", {"seconds": 1}, "Aguardar campo de filtro")
        # 3. Digita o nome para filtrar
        add("type_text", {"text": person}, "Filtrar por: " + person)
        add("wait", {"seconds": 2}, "Aguardar resultados do filtro")
        # 4. O primeiro resultado filtrado e a conversa — clica nela
        add("vision_click", {"description": "conversa com " + person + " que aparece na lista filtrada de chats DENTRO do Teams, deve ser o primeiro item da lista apos o filtro"}, "Abrir conversa com " + person)
        add("wait", {"seconds": 2}, "Aguardar conversa carregar")
        # 5. Agora o campo de mensagem esta visivel — clica nele para garantir foco
        add("vision_click", {"description": "campo de texto 'Digite uma mensagem' na PARTE INFERIOR da conversa DENTRO do Teams"}, "Focar campo de mensagem")
        add("wait", {"seconds": 0.5}, "Aguardar")
        if action_type in ("send_message", "") and message:
            # 6. Digita via clipboard (preserva acentos)
            add("type_text", {"text": message}, "Digitar: " + message[:40])
            add("wait", {"seconds": 1}, "Aguardar texto")
            # 7. Envia
            add("hotkey", {"keys": ["enter"]}, "Enviar mensagem")
        elif action_type == "call":
            add("vision_click", {"description": "icone de telefone no canto superior direito DENTRO da conversa do Teams"}, "Ligar")
        elif action_type == "video_call":
            add("vision_click", {"description": "icone de camera no canto superior direito DENTRO da conversa do Teams"}, "Videochamada")
        # Limpa filtro para nao atrapalhar proxima vez
        add("hotkey", {"keys": ["escape"]}, "Limpar filtro")
        return steps

    # === WHATSAPP ===
    if app in ("whatsapp", "whats", "zap"):
        add("app_search", {"name": "WhatsApp"}, "Abrir WhatsApp")
        add("wait", {"seconds": 4}, "Aguardar carregar")
        add("focus_window", {"title": "WhatsApp"}, "Focar WhatsApp")
        add("wait", {"seconds": 1}, "Aguardar")
        add("vision_click", {"description": "campo de pesquisa com icone de lupa NO TOPO da barra lateral ESQUERDA DENTRO do WhatsApp"}, "Pesquisa")
        add("wait", {"seconds": 1}, "Aguardar")
        add("type_text", {"text": person}, "Pesquisar: " + person)
        add("wait", {"seconds": 2}, "Aguardar busca")
        add("vision_click", {"description": "resultado mostrando " + person + " na lista DENTRO do WhatsApp"}, person)
        add("wait", {"seconds": 2}, "Aguardar conversa")
        add("vision_click", {"description": "campo 'Digite uma mensagem' na parte inferior DENTRO do WhatsApp"}, "Focar campo")
        add("type_text", {"text": message}, "Digitar mensagem")
        add("hotkey", {"keys": ["enter"]}, "Enviar")
        return steps

    # === NOTEPAD ===
    if app in ("notepad", "bloco de notas"):
        add("app_search", {"name": "Bloco de Notas"}, "Abrir Notepad")
        add("wait", {"seconds": 3}, "Aguardar abrir")
        add("app_type", {"window_title": "Notas", "text": text}, "Digitar texto")
        return steps

    # === WORD ===
    if app in ("word", "microsoft word"):
        add("app_search", {"name": "Word"}, "Abrir Word")
        add("wait", {"seconds": 5}, "Aguardar")
        add("vision_click", {"description": "opcao Documento em branco na tela inicial DENTRO do Word"}, "Novo documento")
        add("wait", {"seconds": 3}, "Aguardar")
        add("type_text", {"text": text}, "Digitar texto")
        return steps

    # === EXCEL (abrir visual) ===
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

    # === GENERICO ===
    generic = {"paint": "Paint", "calculadora": "Calculadora", "calculator": "Calculadora",
               "spotify": "Spotify"}
    if app in generic:
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
        add("type_text", {"text": message}, "Corpo")
        add("hotkey", {"keys": ["ctrl", "enter"]}, "Enviar (Ctrl+Enter)")
        return steps

    return None


PROMPT_FALLBACK = (
    "Voce e o DESKTOP AGENT para apps SEM rotina conhecida.\n"
    "Windows PT-BR.\n\n"
    "PREFIRA ATALHOS DE TECLADO sobre cliques visuais.\n"
    "ACOES: app_search(name) | app_type(window_title, text) | focus_window(title)\n"
    "       vision_click(description) | vision_type(description, text)\n"
    "       type_text(text) | hotkey(keys) | wait(seconds)\n\n"
    "REGRAS:\n"
    "- SEMPRE wait(3-5) apos abrir app\n"
    "- Descricoes DENTRO DO APP (nunca taskbar)\n"
    "- Maximo 10 passos. JSON puro.\n\n"
    '{"steps":[{"step":1,"description":"...","action":"...","params":{}}]}'
)


class DesktopAgent:
    def __init__(self):
        self.model = "claude-sonnet-4-20250514"
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
        if app:
            steps = _build_steps(app, params)
            if steps:
                print("  [DESKTOP] Rotina: " + str(len(steps)) + " steps ($0)")
                return {"steps": steps, "agent": "DESKTOP"}

        for kw, detected in {"teams":"teams","whatsapp":"whatsapp","whats":"whatsapp",
            "notepad":"notepad","bloco de notas":"notepad","word":"word","excel":"excel",
            "vscode":"vscode","vs code":"vscode","paint":"paint","calculadora":"calculadora",
            "spotify":"spotify","explorer":"explorer"}.items():
            if kw in str(task_text).lower():
                steps = _build_steps(detected, {"app": detected, "action_type": "open"})
                if steps:
                    return {"steps": steps, "agent": "DESKTOP"}

        print("  [DESKTOP] LLM fallback ($)")
        try:
            resp = client.messages.create(model=self.model, max_tokens=2500, system=PROMPT_FALLBACK,
                messages=[{"role": "user", "content": "TAREFA: " + str(task_text) + "\nJSON puro."}])
            plan = safe_parse(resp.content[0].text.strip(), self.model)
            for st in plan.get("steps", []):
                st["agent"] = "DESKTOP"
            return {"steps": plan.get("steps", []), "agent": "DESKTOP"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "DESKTOP"}