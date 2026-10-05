"""
DesktopAgent v16 — Rotinas utilitárias + Few-shot LLM.
- NOVAS: minimize_all, close_all, screenshot, alt_tab, lock, volume
- Few-shot no prompt LLM (Paint círculo, Calculadora 15+20, Spotify lofi)
- Sem 'Ola!', Paint→LLM, Notepad sem digitar vazio
"""

import json, os, re
from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse
from agents.base_agent import brain_guide


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
        # Notepad do Windows 11 reaproveita a janela aberta (com abas): sem
        # isto o texto caia no documento que o usuario ja estava editando.
        add("blank_document", {"app": "notepad"}, "Garantir documento em branco")
        if text and text.strip():
            add("app_type", {"window_title": "Notas", "text": text, "require_untitled": True}, "Digitar")
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


TEXT_EDITORS = ("notepad", "bloco de notas", "word", "wordpad")

# Configuracoes do Windows: abre a pagina certa direto (ms-settings:), sem procurar no menu
_SETTINGS = re.compile(r"\b(configura\w*|config|ajustes|settings|painel de controle)\b")
# Palavra INTEIRA (\b): "tema" casava dentro de "sistema" e abria Cores.
SETTINGS_PAGES = [
    (r"\b(?:bluetooth|fones?|dispositivos)\b", "ms-settings:bluetooth"),
    (r"\b(?:wi-?fi|rede|redes|internet)\b", "ms-settings:network-status"),
    (r"\b(?:som|audio|volume|microfone|alto-?falante)\b", "ms-settings:sound"),
    (r"\b(?:tela|monitor|video|resolucao|brilho|exibicao|display)\b", "ms-settings:display"),
    (r"\b(?:atualizac\w*|atualizar|update|windows update)\b", "ms-settings:windowsupdate"),
    (r"\b(?:bateria|energia)\b", "ms-settings:powersleep"),
    (r"\b(?:aplicativos?|apps?|programas?)\b", "ms-settings:appsfeatures"),
    (r"\b(?:papel de parede|plano de fundo|fundo de tela)\b", "ms-settings:personalization-background"),
    (r"\b(?:temas?|cores|modo escuro|modo claro|tema escuro)\b", "ms-settings:colors"),
    (r"\b(?:personaliza\w*)\b", "ms-settings:personalization"),
    (r"\b(?:privacidade|seguranca)\b", "ms-settings:privacy"),
    (r"\b(?:data|hora|relogio|fuso)\b", "ms-settings:dateandtime"),
    (r"\b(?:idiomas?|lingua|teclado|regiao)\b", "ms-settings:regionlanguage"),
    (r"\b(?:mouse|touchpad)\b", "ms-settings:mousetouchpad"),
    (r"\b(?:impressoras?|scanner)\b", "ms-settings:printers"),
    (r"\b(?:notificac\w*)\b", "ms-settings:notifications"),
    (r"\b(?:armazenamento|disco|espaco)\b", "ms-settings:storagesense"),
    (r"\b(?:contas?|usuario|login|senha do windows)\b", "ms-settings:accounts"),
    (r"\b(?:acessibilidade)\b", "ms-settings:easeofaccess"),
    (r"\b(?:jogos|game bar|xbox)\b", "ms-settings:gaming-gamebar"),
    (r"\b(?:sistema|sobre o pc|sobre)\b", "ms-settings:about"),
]

# Pedido de INTERAGIR (clicar, ativar, mudar...) com as Configuracoes: nao e so abrir
# uma pagina — vai para o piloto de apps na janela aberta.
_SETTINGS_ACT = re.compile(r"\b(clic\w*|clique|selecion\w*|aperta\w*|marc\w*|ativ\w*|desativ\w*|lig\w*|"
                           r"deslig\w*|mud\w*|troc\w*|alter\w*|escolh\w*|rol\w*|desc[ae]\w*)\b")


def _vault_settings_page(t: str) -> tuple[str, str]:
    """Pagina das Configuracoes ensinada no Obsidian (70 Dicionario/Configuracoes do Windows).
    -> (uri, jeito de falar que casou). 'abre a tela de bloqueio' -> ms-settings:lockscreen."""
    try:
        from core.lexicon import get_lexicon
        best_uri, best_v = "", ""
        for e in get_lexicon().table("Configuracoes do Windows"):
            uri = e.meaning.strip("` ")
            if not uri.startswith("ms-settings:") or uri == "ms-settings:":
                continue                               # so paginas especificas
            for v in e.variants:
                if len(v) > len(best_v) and len(v) >= 3 and re.search(rf"\b{re.escape(v)}\b", t):
                    best_uri, best_v = uri, v          # o jeito de falar mais especifico vence
        return best_uri, best_v
    except Exception:
        return "", ""


def settings_steps(task_text: str):
    """'abra as configuracoes do windows' / 'abre o bluetooth nas configuracoes' -> ms-settings:.
    So para ABRIR: 'clica em sistema', 'ativa o modo escuro' vao para o piloto."""
    from core.lexicon import norm
    t = norm(task_text)
    if not _SETTINGS.search(t):
        return None
    # "configuracoes do youtube/do chrome/do site" nao sao do Windows
    if re.search(r"\b(youtube|chrome|edge|navegador|site|spotify|whatsapp|teams|vs ?code|word|excel|jogo)\b", t) \
            and "windows" not in t:
        return None
    # Nome de varias palavras ensinado no Obsidian ("tela de bloqueio") e mais especifico que a
    # lista em codigo ("tela" -> Video); palavra solta: a lista em codigo vem primeiro.
    vault_uri, vault_v = _vault_settings_page(t)
    code_uri = next((u for pat, u in SETTINGS_PAGES if re.search(pat, t)), "")
    page = (vault_uri if " " in vault_v else "") or code_uri or vault_uri or "ms-settings:"
    steps = [{"step": 1, "action": "open_path", "params": {"path": page},
              "description": "Abrir Configurações do Windows" + ("" if page == "ms-settings:" else f" ({page.split(':')[1]})"),
              "agent": "DESKTOP"}]
    if _SETTINGS_ACT.search(t):
        # Abre a pagina mais proxima e o piloto termina o pedido (clicar/ativar) nela
        steps += [{"step": 2, "action": "app_task", "params": {"goal": task_text, "app": "configuracoes"},
                   "description": f"Nas Configurações: {task_text[:50]}", "agent": "DESKTOP"}]
    return steps


_DO_MORE = re.compile(r"\b(escrev\w*|digit\w*|preench\w*|anot\w*|coloc\w*|bot[ae]|insir\w*|cri[ae]\w* uma? "
                      r"(?:tabela|lista|planilha)|calcul\w*|clic\w*|selecion\w*|toc\w*|pesquis\w*|procur\w*|"
                      r"desenh\w*|mand\w*|envi\w*)\b")
TYPING_ACTIONS = ("app_type", "type_text", "vision_type", "uia_type", "app_task")


def _then_do_rest(steps: list, app: str, task_text: str, params: dict) -> list:
    """Rotina de ABRIR + o resto do pedido. As rotinas so abrem o app; quando o
    pedido tambem manda escrever/preencher/clicar ("abre o Excel e preenche as
    colunas"), o piloto de apps faz o resto NA janela que acabou de abrir."""
    from core.lexicon import norm
    if any(s["action"] in TYPING_ACTIONS for s in steps):
        return steps
    t = norm(task_text)
    after_open = re.split(r"\b(?:e|depois|entao)\b", t, maxsplit=1)
    rest = after_open[1] if len(after_open) > 1 else ""
    wants = (params.get("text") or params.get("message")) or _DO_MORE.search(rest or t)
    if not wants or app in ("notepad", "bloco de notas"):
        return steps
    from core.lexicon import get_lexicon
    key = get_lexicon().app_key(app) or app
    return steps + [{"step": len(steps) + 1, "action": "app_task",
                     "params": {"goal": task_text, "app": key},
                     "description": f"Fazer no {app}: {task_text[:50]}", "agent": "DESKTOP"}]


def continue_steps(cont: dict, task_text: str, params: dict) -> list:
    """Passos para continuar numa janela ja aberta (sem reabrir o app).
    Editor de texto + texto pedido -> digita no MESMO documento; qualquer outra
    coisa (tocar a musica de baixo, calcular, clicar...) -> piloto de apps."""
    title = cont.get("title", "")
    key = (cont.get("key") or "").lower()
    text = (params.get("text") or params.get("message") or "").strip()
    from core.lexicon import norm
    t = norm(task_text)
    # "abre o Excel" com o Excel ja aberto: so trazer para a frente (nada de reabrir).
    # "voltar para a tela anterior" e NAVEGAR dentro do app (piloto), nao trazer a janela.
    if not text and re.match(r"^(?:abr\w*|mostr\w*|traz\w*|traga|volt\w* (?:pro|para|ao|a)|vai (?:pro|para|no|na)|"
                             r"foc\w*|ir (?:pro|para))\b", t) \
            and not re.search(r"\b(clic|selecion|digit|escrev|preench|toc|pesquis|procur|marc|aperta)", t) \
            and not re.search(r"\b(anterior|atras|pagina|tela|inicio|menu|aba|item|opcao|secao)\b", t):
        return [{"step": 1, "action": "focus_window", "params": {"hwnd": cont.get("hwnd"), "title": title},
                 "description": f"Trazer {title[:40]} para a frente", "agent": "DESKTOP"}]
    editor = key in TEXT_EDITORS or "bloco de notas" in title.lower() or "word" in title.lower()
    if not (text and editor):
        return [{"step": 1, "action": "app_task",
                 "params": {"goal": task_text, "hwnd": cont.get("hwnd"), "title": title},
                 "description": f"Continuar em {title[:30]}: {task_text[:50]}", "agent": "DESKTOP"}]
    if cont.get("last_text"):
        text = "\n\n" + text          # continua abaixo do que ja foi escrito
    return [{"step": 1, "action": "focus_window",
             "params": {"hwnd": cont.get("hwnd"), "title": title},
             "description": f"Voltar para {title[:40]}", "agent": "DESKTOP"},
            {"step": 2, "action": "app_type",
             "params": {"window_title": title, "hwnd": cont.get("hwnd"), "text": text,
                        "expect_title": title},
             "description": "Digitar", "agent": "DESKTOP"}]


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
        self.effort = self._config.get_effort("desktop")
        self.name = "DESKTOP"

    def plan(self, task, context=None):
        """
        Subagentes: AppResolver (qual app) e ContentComposer (texto pronto)
        preparam a entrada; ScreenGuard revisa os passos antes de executar.
        """
        from agents.subagents import AppResolver, ContentComposer, ScreenGuard
        params = dict(task.get("params") or {}) if isinstance(task, dict) else {}
        if isinstance(context, dict) and "app" in context:
            params = dict(context)
        task_text = task.get("task", "") if isinstance(task, dict) else str(task)

        # Continuacao da conversa: age na MESMA janela do pedido anterior
        cont = params.get("continue") or {}
        if cont.get("type") == "app":
            steps = continue_steps(cont, task_text, params)
            guard = ScreenGuard().run(steps)
            return {"steps": guard.data["steps"], "agent": "DESKTOP",
                    "subagents": [ScreenGuard().trace(True, f"continuar em \"{cont.get('title', '')[:50]}\""),
                                  guard]}

        app_t = AppResolver().run(task_text, params)
        text_t = ContentComposer().run(params)
        params = text_t.data["params"]
        if params.get("app"):
            params["app"] = app_t.data["app"]

        if isinstance(task, dict):
            task = {**task, "params": params}
        if isinstance(context, dict) and "app" in context:
            context = params
        result = self._plan_steps(task, context)

        traces = [app_t, text_t]
        if result.get("steps"):
            guard = ScreenGuard().run(result["steps"])
            traces.append(guard)
            result["steps"] = guard.data["steps"]
            if not guard.ok:
                result = {"steps": [], "agent": "DESKTOP",
                          "error": f"ScreenGuard reprovou os passos: {guard.summary}"}
        result["subagents"] = traces
        return result

    def _plan_steps(self, task, context=None):
        params = {}
        task_text = task
        if isinstance(task, dict):
            params = task.get("params", {})
            task_text = task.get("task", str(task))
        if isinstance(context, dict) and "app" in context:
            params = context

        app = (params.get("app", "") or "").lower().strip()
        task_lower = str(task_text).lower()

        sett = settings_steps(str(task_text)) or (settings_steps(app) if app else None)
        if sett:
            print(f"  [DESKTOP] Configurações do Windows: {sett[0]['params']['path']}")
            return {"steps": sett, "agent": "DESKTOP"}

        # "abra a pasta downloads" / "abra C:\projetos": abre direto, sem
        # digitar no menu Iniciar (fragil) nem navegar pelo Explorer.
        from core.paths import is_open_folder_request, extract_path
        if is_open_folder_request(str(task_text)):
            path = extract_path(str(task_text))
            print(f"  [DESKTOP] Abrir caminho direto: {path}")
            return {"steps": [{"step": 1, "action": "open_path", "params": {"path": path},
                               "description": f"Abrir {path}", "agent": "DESKTOP"}],
                    "agent": "DESKTOP"}

        if app:
            steps = _build_steps(app, params)
            if not steps and (params.get("action_type") or "").lower() not in ("", "open"):
                # Rotina so sabe ABRIR: abre e o piloto de apps faz o resto na janela
                # ("abre a calculadora e calcula 15% de 200"). Antes caia no modo de
                # cliques "chutados" pela visao.
                steps = _build_steps(app, {**params, "action_type": "open", "text": "", "message": ""})
            if steps:
                steps = _then_do_rest(steps, app, str(task_text), params)
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
                    return {"steps": _then_do_rest(steps, detected, str(task_text), params),
                            "agent": "DESKTOP"}

        print("  [DESKTOP] LLM fallback ($)")
        try:
            raw = self._client.message(
                model=self.model, system=PROMPT_FALLBACK,
                user_content=f"TAREFA: {task_text}{brain_guide('DESKTOP', task_text)}\nJSON puro.", max_tokens=8000,
                effort=self.effort, agent="DESKTOP",
            )
            plan = safe_parse(raw, self.model)
            for st in plan.get("steps", []): st["agent"] = "DESKTOP"
            return {"steps": plan.get("steps", []), "agent": "DESKTOP"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "DESKTOP"}