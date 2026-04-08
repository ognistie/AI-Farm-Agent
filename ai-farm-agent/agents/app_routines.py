"""
AppRoutines v6 — Titulos flexiveis, rotinas de passo unico onde possivel.
"""


def get_routine(params):
    """Recebe params estruturados e retorna steps."""
    app = (params.get("app", "") or "").lower().strip()
    action_type = (params.get("action_type", "") or "").lower().strip()
    person = params.get("person", "") or "Contato"
    message = params.get("message", "") or params.get("text", "") or "Ola!"
    text = params.get("text", "") or message

    if app in ("teams", "microsoft teams"):
        if action_type in ("call",): return _teams_call(person)
        if action_type in ("video_call",): return _teams_video(person)
        return _teams_msg(person, message)
    if app in ("whatsapp", "whats", "zap"): return _whatsapp_msg(person, message)
    if app in ("notepad", "bloco de notas"): return _notepad(text)
    if app in ("word", "microsoft word"): return _word(text)
    if app in ("excel", "microsoft excel"): return _excel_open()
    if app in ("vscode", "vs code", "visual studio code"): return _vscode()
    if app in ("paint",): return _generic("Paint", "Paint")
    if app in ("calculadora", "calculator"): return _generic("Calculadora", "Calculadora")
    if app in ("outlook",): return _outlook(params)
    if app in ("spotify",): return _spotify(text)
    if app in ("explorer", "explorador"): return _explorer()
    return None


def _s(step, action, params, desc):
    return {"step": step, "action": action, "params": params, "description": desc, "agent": "DESKTOP"}


def _teams_msg(person, message):
    return [
        _s(1, "app_search", {"name": "Microsoft Teams"}, "Abrir Teams"),
        _s(2, "wait_for_window", {"title": "Teams", "timeout": 15}, "Aguardar Teams"),
        _s(3, "uia_click", {"app_name": "Teams", "element": "chat"}, "Clicar em Chat"),
        _s(4, "wait", {"seconds": 2}, "Aguardar lista"),
        _s(5, "uia_click", {"app_name": "Teams", "element": person}, "Conversa: " + person),
        _s(6, "wait", {"seconds": 2}, "Aguardar conversa"),
        _s(7, "uia_type", {"app_name": "Teams", "field": "message_box", "text": message}, "Digitar: " + message[:40]),
        _s(8, "wait", {"seconds": 1}, "Aguardar"),
        _s(9, "hotkey", {"keys": ["enter"]}, "Enviar"),
    ]


def _teams_call(person):
    return [
        _s(1, "app_search", {"name": "Microsoft Teams"}, "Abrir Teams"),
        _s(2, "wait_for_window", {"title": "Teams", "timeout": 15}, "Aguardar"),
        _s(3, "uia_click", {"app_name": "Teams", "element": "chat"}, "Chat"),
        _s(4, "wait", {"seconds": 2}, "Aguardar"),
        _s(5, "uia_click", {"app_name": "Teams", "element": person}, "Conversa: " + person),
        _s(6, "wait", {"seconds": 2}, "Aguardar"),
        _s(7, "vision_click", {"description": "icone de telefone no canto superior direito da conversa DENTRO do Teams"}, "Ligar"),
    ]


def _teams_video(person):
    return [
        _s(1, "app_search", {"name": "Microsoft Teams"}, "Abrir Teams"),
        _s(2, "wait_for_window", {"title": "Teams", "timeout": 15}, "Aguardar"),
        _s(3, "uia_click", {"app_name": "Teams", "element": "chat"}, "Chat"),
        _s(4, "wait", {"seconds": 2}, "Aguardar"),
        _s(5, "uia_click", {"app_name": "Teams", "element": person}, "Conversa: " + person),
        _s(6, "wait", {"seconds": 2}, "Aguardar"),
        _s(7, "vision_click", {"description": "icone de camera no canto superior direito DENTRO do Teams"}, "Video"),
    ]


def _whatsapp_msg(person, message):
    return [
        _s(1, "app_search", {"name": "WhatsApp"}, "Abrir WhatsApp"),
        _s(2, "wait_for_window", {"title": "WhatsApp", "timeout": 10}, "Aguardar"),
        _s(3, "uia_click", {"app_name": "WhatsApp", "element": "search"}, "Pesquisa"),
        _s(4, "type_text", {"text": person}, "Digitar: " + person),
        _s(5, "wait", {"seconds": 2}, "Aguardar busca"),
        _s(6, "vision_click", {"description": "resultado com " + person + " DENTRO do WhatsApp"}, person),
        _s(7, "wait", {"seconds": 2}, "Aguardar conversa"),
        _s(8, "uia_type", {"app_name": "WhatsApp", "field": "message", "text": message}, "Digitar mensagem"),
        _s(9, "hotkey", {"keys": ["enter"]}, "Enviar"),
    ]


def _notepad(text):
    """Notepad: abre e digita em sequencia unica. Titulo flexivel."""
    return [
        _s(1, "app_search", {"name": "Bloco de Notas"}, "Abrir Notepad"),
        _s(2, "wait", {"seconds": 3}, "Aguardar Notepad abrir"),
        _s(3, "app_type", {"window_title": "Notas", "text": text}, "Digitar texto"),
    ]


def _word(text):
    return [
        _s(1, "app_search", {"name": "Word"}, "Abrir Word"),
        _s(2, "wait", {"seconds": 5}, "Aguardar Word"),
        _s(3, "uia_click", {"app_name": "Word", "element": "blank_doc"}, "Documento em branco"),
        _s(4, "wait", {"seconds": 3}, "Aguardar documento"),
        _s(5, "type_text", {"text": text}, "Digitar"),
    ]


def _excel_open():
    return [
        _s(1, "app_search", {"name": "Excel"}, "Abrir Excel"),
        _s(2, "wait", {"seconds": 5}, "Aguardar Excel"),
        _s(3, "uia_click", {"app_name": "Excel", "element": "blank_workbook"}, "Planilha em branco"),
        _s(4, "wait", {"seconds": 3}, "Aguardar planilha"),
    ]


def _vscode():
    return [
        _s(1, "app_search", {"name": "Visual Studio Code"}, "Abrir VS Code"),
        _s(2, "wait", {"seconds": 4}, "Aguardar VS Code"),
    ]


def _explorer():
    return [
        _s(1, "hotkey", {"keys": ["win", "e"]}, "Abrir Explorer"),
        _s(2, "wait", {"seconds": 2}, "Aguardar"),
    ]


def _generic(name, wait_title):
    return [
        _s(1, "app_search", {"name": name}, "Abrir " + name),
        _s(2, "wait", {"seconds": 3}, "Aguardar " + name),
    ]


def _outlook(params):
    to = params.get("person", "")
    subject = params.get("subject", "Sem assunto")
    body = params.get("message", "") or params.get("text", "")
    return [
        _s(1, "app_search", {"name": "Outlook"}, "Abrir Outlook"),
        _s(2, "wait", {"seconds": 5}, "Aguardar Outlook"),
        _s(3, "uia_click", {"app_name": "Outlook", "element": "new_email"}, "Novo Email"),
        _s(4, "wait", {"seconds": 2}, "Aguardar"),
        _s(5, "uia_type", {"app_name": "Outlook", "field": "to", "text": to}, "Destinatario"),
        _s(6, "hotkey", {"keys": ["tab"]}, "Tab"),
        _s(7, "type_text", {"text": subject}, "Assunto"),
        _s(8, "hotkey", {"keys": ["tab"]}, "Tab"),
        _s(9, "type_text", {"text": body}, "Corpo"),
        _s(10, "uia_click", {"app_name": "Outlook", "element": "send"}, "Enviar"),
    ]


def _spotify(query):
    return [
        _s(1, "app_search", {"name": "Spotify"}, "Abrir Spotify"),
        _s(2, "wait", {"seconds": 4}, "Aguardar Spotify"),
        _s(3, "uia_click", {"app_name": "Spotify", "element": "search"}, "Pesquisa"),
        _s(4, "type_text", {"text": query}, "Digitar: " + str(query)[:30]),
        _s(5, "hotkey", {"keys": ["enter"]}, "Buscar"),
        _s(6, "wait", {"seconds": 2}, "Aguardar resultados"),
    ]