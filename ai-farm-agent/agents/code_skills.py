"""
code_skills.py — Skills detection puras para o CodeAgent.

Toda a inteligencia de classificacao da tarefa do usuario antes de chamar
o LLM. Custo zero. Sem efeitos colaterais. Sem imports pesados.

Capacidades:
    detect_project_type(task)  -> ProjectType
    detect_complexity(task)    -> Complexity ("prototype" | "small" | "medium" | "professional")
    detect_stack(task, ptype)  -> str  (framework escolhido)
    extract_dependencies(task) -> list[str]  (pip packages)
    extract_topic(task)        -> str  (snake_case para nome de pasta)
    extract_languages(task)    -> set[str]  ({"html", "css", "js", "python"} etc)
    needs_sonnet(task, ptype, complexity) -> bool
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
#  Tipos de projeto cobertos
# ═══════════════════════════════════════════════════════════════════

PROJECT_TYPES = {
    "static_site":      "HTML + CSS, sem JS, single-page ou multi-arquivo simples",
    "interactive_site": "HTML + CSS + JS vanilla, com interatividade",
    "web_app":          "Frontend dinamico (SPA), pode ter framework JS",
    "rest_api":         "Backend API sem UI (endpoints JSON)",
    "fullstack_web":    "API + frontend conectado",
    "python_cli":       "Sistema/utilitario CLI em Python (interativo ou nao)",
    "python_script":    "Script Python pequeno, 1 arquivo",
    "python_gui":       "App desktop com janela (Tkinter, PyQt, customtkinter)",
    "python_game":      "Jogo em pygame ou similar",
    "python_data":      "Notebook ou script de analise de dados (pandas, ML)",
    "python_automation":"Script de automacao (web scraping, file processing)",
    "python_bot":       "Bot (Telegram, Discord, web scraping continuo)",
    "node_js":          "Projeto Node.js (CLI, API, etc)",
    "documentation":    "Apenas docs (.md), sem codigo executavel",
}


# Mapeamento keyword -> project_type. Ordem importa: especifico antes de generico.
# Cada entrada e (keywords, project_type, score_boost).
PROJECT_TYPE_RULES = [
    # ──── APIs (muito especifico — vem primeiro)
    (["api rest", "rest api", "endpoint", "endpoints", "api crud",
      "json api", "fastapi", "api em flask", "api em fastapi",
      "swagger", "openapi"], "rest_api", 3),

    # ──── Fullstack
    (["full stack", "fullstack", "frontend + backend", "site dinamico com api",
      "spa com backend"], "fullstack_web", 3),

    # ──── Jogos
    (["jogo ", "game", "pygame", "arcade game", "jogo da velha", "snake",
      "pong", "tetris", "platformer", "rpg simples", "jogo de", "jogo em"],
     "python_game", 3),

    # ──── CLI EXPLICITO (v21.4: usuario PEDE terminal — vence GUI ambigua)
    # Markers diretos como "terminal" / "CLI" tem precedencia sobre
    # inferencia "sistema" (que vira GUI por padrao).
    (["cli em python", "command line", "linha de comando",
      "menu no terminal", "interface de terminal", "script no terminal",
      "rodar pelo terminal", "executar pelo terminal", "ferramenta cli",
      "tool cli", "cli tool", "interativo no terminal",
      "no terminal um menu", "no terminal"],
     "python_cli", 5),

    # ──── GUI Desktop (NOVO default v21.4: "sistema" sem qualificador
    # ──── vai para GUI, nao CLI. Usuario quer interface visual por padrao)
    (["interface grafica", "interface gráfica", "janela com botoes",
      "tkinter", "customtkinter", "ctk", "pyqt", "pyside", "kivy",
      "gui desktop", "app desktop em python",
      # v21.4: tasks "sistema" ambiguas viram GUI (era CLI antes)
      "sistema em python", "sistema python", "sistema profissional em python",
      "app em python", "aplicativo python", "plataforma em python",
      "dashboard em python", "gerenciador em python", "controle em python",
      "sistema de cadastro", "sistema de agendamento", "sistema de gestao",
      "sistema de gestão", "sistema dental", "sistema escolar",
      "agendamento em python", "cadastro em python", "gestao em python",
      "agendamento python", "controle de consultas", "consultorio",
      "consultório", "clinica", "clínica",
      "sistema profissional", "sistema completo", "sistema robusto",
      "aplicacao profissional", "aplicação profissional",
      # v21.4 ampliacao: "app de X" ou "app para X" assume GUI
      "app de ", "app para ", "aplicativo de ", "aplicativo para ",
      "programa de ", "programa para ",
      "controle de financas", "controle financeiro", "gestao financeira",
      "controle pessoal", "organizador pessoal", "gestao de"],
     "python_gui", 3),

    # ──── Data / ML
    (["analise de dados", "análise de dados", "machine learning", "data science",
      "pandas", "numpy", "scikit", "tensorflow", "pytorch", "regressao",
      "regressão", "classificacao", "classificação", "notebook", "jupyter",
      "visualizacao de dados", "visualização de dados", "matplotlib"],
     "python_data", 3),

    # ──── Bots
    (["bot do telegram", "telegram bot", "discord bot", "bot de discord",
      "whatsapp bot", "bot scraper continuo"], "python_bot", 3),

    # ──── Automation
    (["automatizar", "automatizacao", "automatização", "scraper", "scraping",
      "web scraping", "raspagem", "renomear em lote", "renomear ",
      "em lote", "processar arquivos", "converter arquivos",
      "batch", "processamento em massa"], "python_automation", 2),

    # ──── Node.js
    (["node js", "node.js", "express", "nodejs", "npm", "package.json"],
     "node_js", 3),

    # ──── Documentacao
    (["readme", "documentacao", "documentação", "apenas docs", "markdown"],
     "documentation", 2),

    # (CLI explicito ja foi declarado acima, antes do GUI — boost 5)

    # ──── Web app (HTML+CSS+JS dinamico)
    (["web app", "single page app", "spa ", "aplicacao web", "aplicação web",
      "dashboard web", "painel web"], "web_app", 2),

    # ──── Sites com JS
    (["html css js", "html, css e js", "html, css, javascript",
      "site interativo", "site com javascript"], "interactive_site", 2),

    # ──── Sites estaticos (HTML + CSS) — generico, no fim
    (["site sobre", "pagina sobre", "página sobre", "landing page",
      "site profissional", "site institucional", "html e css"],
     "static_site", 1),

    # ──── Python script (catch-all, BAIXA prioridade)
    # NOTA: se a task tem "sistema profissional" ou nomes de dominio como
    # "agendamento/cadastro/clinica/dentista", prefira python_cli acima.
    # python_script e SO para "rodar uma vez" sem multi-arquivo.
    (["script python", "script em python", "script para",
      "programa python", "codigo python", "código python"],
     "python_script", 1),
]


# v5: markers de "task informativa" — mostrar conteudo sobre tema
# (historia, biografia, sobre, oque eh, como foi criado). Para essas
# tarefas, mesmo com "sistema em python", static_site eh mais natural
# (pagina informativa). Mas respeitamos o pedido se vier explicito.
_INFORMATIVE_MARKERS = [
    "mostra a historia", "mostra a história", "mostre a historia",
    "mostre a história", "conta a historia", "conte a historia",
    "biografia", "sobre o", "sobre a", "sobre os", "sobre as",
    "o que e ", "o que é ", "como foi", "como surgiu", "como nasceu",
    "informacoes sobre", "informações sobre", "explicar",
    "apresentar", "apresenta", "exibe informacoes", "exibe informações",
]


def detect_project_type(task: str) -> str:
    """
    Classifica a tarefa em um dos PROJECT_TYPES.
    Retorna 'static_site' como default conservador para sites,
    ou 'python_script' se mencionar python sem mais detalhes,
    senao 'static_site'.

    v5: tasks "informativas" (mostrar historia/sobre/o que e) sao
    redirecionadas para static_site quando o usuario NAO pediu explicitamente
    python/tkinter/CLI. Pagina informativa eh o formato natural.
    """
    if not task:
        return "static_site"
    t = _normalize(task)

    # v5: detecta intencao informativa
    is_informative = any(m in t for m in _INFORMATIVE_MARKERS)
    has_explicit_python_gui = any(m in t for m in (
        "tkinter", "customtkinter", "pyqt", "interface grafica em python",
        "janela com tkinter", "gui em python com tkinter",
    ))
    has_explicit_cli = any(m in t for m in (
        "no terminal", "linha de comando", "cli em python", "menu no terminal",
    ))

    best_type = None
    best_score = 0
    for keywords, ptype, boost in PROJECT_TYPE_RULES:
        score = sum(boost for kw in keywords if kw in t) - sum(0 for _ in [])
        # Considera longest-match (keyword mais especifica vale mais)
        for kw in keywords:
            if kw in t:
                score += len(kw.split())  # frases multi-palavra ganham peso
        if score > best_score:
            best_score = score
            best_type = ptype

    # v5 OVERRIDE: se a task e informativa E o usuario NAO pediu Python GUI/CLI
    # explicito, prefere site. "sistema em python que mostra historia de X" cai
    # melhor em static_site (pagina com conteudo) do que em GUI Tkinter.
    if (is_informative
            and not has_explicit_python_gui
            and not has_explicit_cli
            and best_type in ("python_gui", "python_cli", "python_script")):
        return "static_site"

    if best_type:
        return best_type

    # Fallbacks heuristicos
    if "python" in t:
        return "python_script"
    if any(w in t for w in ("html", "css", "site", "pagina", "página")):
        return "static_site"
    return "static_site"


# ═══════════════════════════════════════════════════════════════════
#  Complexidade
# ═══════════════════════════════════════════════════════════════════

COMPLEXITY_LEVELS = ("prototype", "small", "medium", "professional")

_PROFESSIONAL_MARKERS = [
    "profissional", "completo", "completa", "robusto", "enterprise",
    "pronto para producao", "pronto para produção", "production-ready",
    "com tests", "com testes", "com docker", "com ci",
    "modular", "escalavel", "escalável", "multi-arquivo",
]
_MEDIUM_MARKERS = [
    "varias paginas", "várias páginas", "multi-pagina", "multi-página",
    "com banco de dados", "com persistencia", "com persistência",
    "com login", "com autenticacao", "com autenticação",
    "varias telas", "várias telas",
]
_PROTOTYPE_MARKERS = [
    "simples", "rapido", "rápido", "pequeno", "basico", "básico",
    "exemplo de", "minimo", "mínimo", "prototipo", "protótipo",
]


def detect_complexity(task: str) -> str:
    """Retorna nivel de complexidade pelo vocabulario."""
    if not task:
        return "small"
    t = _normalize(task)

    if any(m in t for m in _PROFESSIONAL_MARKERS):
        return "professional"
    if any(m in t for m in _MEDIUM_MARKERS):
        return "medium"
    if any(m in t for m in _PROTOTYPE_MARKERS):
        return "prototype"

    # Heuristica por tamanho da task: mais palavras = mais contexto = mais complexo
    word_count = len(re.findall(r"\w+", task))
    if word_count >= 25:
        return "medium"
    if word_count >= 12:
        return "small"
    return "prototype"


# ═══════════════════════════════════════════════════════════════════
#  Stack/framework
# ═══════════════════════════════════════════════════════════════════

STACK_RULES = {
    "rest_api":         [("fastapi", ["fastapi"]),
                         ("flask",   ["flask"]),
                         ("flask",   [])],   # default
    "fullstack_web":    [("flask",   ["flask"]),
                         ("fastapi", ["fastapi"]),
                         ("flask",   [])],
    "web_app":          [("vanilla_js", [])],
    "interactive_site": [("vanilla_js", [])],
    "static_site":      [("tailwind",  ["tailwind"]),
                         ("bootstrap", ["bootstrap"]),
                         ("vanilla_css", [])],
    # v21.4: customtkinter e o default (visual moderno). Tkinter so se
    # explicitamente pedido como "tkinter classico" ou "simples".
    "python_gui":       [("pyqt",          ["pyqt", "pyside"]),
                         ("tkinter",       ["tkinter classico", "tkinter simples"]),
                         ("customtkinter", [])],   # default
    "python_game":      [("pygame", [])],
    "python_data":      [("pandas+matplotlib", [])],
    "python_cli":       [("argparse+json", [])],
    "python_script":    [("stdlib", [])],
    "python_automation":[("stdlib", [])],
    "python_bot":       [("python-telegram-bot", ["telegram"]),
                         ("discord.py", ["discord"]),
                         ("stdlib", [])],
    "node_js":          [("express", ["express"]),
                         ("stdlib", [])],
    "documentation":    [("markdown", [])],
}


def detect_stack(task: str, project_type: str) -> str:
    """Detecta o framework/stack a usar dado o tipo do projeto."""
    rules = STACK_RULES.get(project_type, [("stdlib", [])])
    t = _normalize(task)
    for stack, keywords in rules:
        if not keywords:
            return stack
        if any(kw in t for kw in keywords):
            return stack
    return rules[-1][0] if rules else "stdlib"


# ═══════════════════════════════════════════════════════════════════
#  Dependencias (pip / npm)
# ═══════════════════════════════════════════════════════════════════

# Pacotes detectados por keywords explicitas
DEPENDENCY_PATTERNS = [
    (re.compile(r"\bflask\b", re.I),         "flask"),
    (re.compile(r"\bfastapi\b", re.I),       "fastapi"),
    (re.compile(r"\buvicorn\b", re.I),       "uvicorn"),
    (re.compile(r"\bpandas\b", re.I),        "pandas"),
    (re.compile(r"\bnumpy\b", re.I),         "numpy"),
    (re.compile(r"\bmatplotlib\b", re.I),    "matplotlib"),
    (re.compile(r"\bseaborn\b", re.I),       "seaborn"),
    (re.compile(r"\bscikit", re.I),          "scikit-learn"),
    (re.compile(r"\btensorflow\b", re.I),    "tensorflow"),
    (re.compile(r"\bpytorch\b", re.I),       "torch"),
    (re.compile(r"\brequests\b", re.I),      "requests"),
    (re.compile(r"\bbeautifulsoup\b|\bbs4\b", re.I), "beautifulsoup4"),
    (re.compile(r"\bopenpyxl\b|\bexcel\b", re.I),    "openpyxl"),
    (re.compile(r"\bpygame\b", re.I),        "pygame"),
    (re.compile(r"\bpillow\b|\bPIL\b"),      "Pillow"),
    (re.compile(r"\bqrcode\b", re.I),        "qrcode"),
    (re.compile(r"\bsqlalchemy\b", re.I),    "sqlalchemy"),
    (re.compile(r"\bpydantic\b", re.I),      "pydantic"),
    (re.compile(r"\bcustomtkinter\b|\bctk\b", re.I), "customtkinter"),
    (re.compile(r"\bpyqt\b|\bpyside\b", re.I), "PyQt6"),
    (re.compile(r"\bkivy\b", re.I),          "kivy"),
    (re.compile(r"\btelegram bot\b|python-telegram-bot", re.I), "python-telegram-bot"),
    (re.compile(r"\bdiscord\b", re.I),       "discord.py"),
]


def extract_dependencies(task: str) -> list[str]:
    """Retorna lista deduplicada de pip packages mencionados/implicados."""
    if not task:
        return []
    found: list[str] = []
    for pat, pkg in DEPENDENCY_PATTERNS:
        if pat.search(task) and pkg not in found:
            found.append(pkg)
    return found


# ═══════════════════════════════════════════════════════════════════
#  Linguagens
# ═══════════════════════════════════════════════════════════════════

def extract_languages(task: str) -> set[str]:
    """
    Retorna SET de linguagens explicitamente pedidas.
    Importante para evitar criar arquivos nao solicitados.
    """
    if not task:
        return set()
    t = _normalize(task)
    langs = set()

    if "html" in t:       langs.add("html")
    if "css" in t:        langs.add("css")
    if re.search(r"\bjs\b|javascript|java script", t): langs.add("js")
    if "typescript" in t or re.search(r"\bts\b", t):   langs.add("ts")
    if "python" in t or re.search(r"\bpy\b", t):       langs.add("python")
    if re.search(r"\bnode\b|node\.js|nodejs", t):      langs.add("js")
    if re.search(r"\bjava\b", t) and "javascript" not in t: langs.add("java")
    if re.search(r"\bc\+\+\b|\bcpp\b", t):             langs.add("cpp")
    if re.search(r"\bc#\b|csharp", t):                 langs.add("csharp")
    if re.search(r"\bgo\b|golang", t):                 langs.add("go")
    if re.search(r"\brust\b", t):                      langs.add("rust")
    if re.search(r"\bsql\b", t):                       langs.add("sql")

    return langs


# ═══════════════════════════════════════════════════════════════════
#  Topico / nome de pasta
# ═══════════════════════════════════════════════════════════════════

_STOP_FOR_TOPIC = {
    # verbos de acao
    "crie", "criar", "cria", "faca", "faça", "fazer", "construa", "monte",
    "abra", "abrir", "abre", "tenha", "tem", "ter", "use", "usar",
    # artigos/conectivos
    "um", "uma", "uns", "umas", "o", "a", "os", "as", "de", "do", "da",
    "dos", "das", "em", "no", "na", "para", "com", "sobre", "que",
    "por", "pelo", "pela", "como", "onde", "quando",
    # tipos de software (vao no prefix em vez do nome)
    "site", "sites", "pagina", "página", "sistema", "sistemas", "app",
    "aplicativo", "programa", "script", "projeto", "arquivo", "arquivos",
    # adjetivos genericos
    "completo", "completa", "robusto", "robusta", "profissional", "moderno",
    "moderna", "simples", "novo", "nova", "modular", "escalavel", "escalável",
    "arquitetura", "arquiteturas", "infraestrutura",
    # linguagens / ferramentas (nao sao tema)
    "html", "css", "javascript", "js", "ts", "typescript", "python", "py",
    "node", "java", "csharp", "ruby", "php", "rust", "go", "cpp", "react",
    "vue", "angular", "flask", "fastapi", "django", "tkinter", "pygame",
    "vs", "code", "vscode", "editor", "ide",
}


def extract_topic(task: str, project_type: str = "static_site") -> str:
    """
    Extrai o nome do projeto/pasta em snake_case a partir do tema da task.
    Ex: 'site sobre Muay Thai' -> 'site_muay_thai'
        'sistema dental em Python' -> 'sistema_dental'
        'jogo da velha' -> 'jogo_velha'
    """
    if not task:
        return _default_name(project_type)

    # Remove acentos e normaliza
    t = _normalize(task)
    words = re.findall(r"[a-z0-9]+", t)
    topic_words = [w for w in words if w not in _STOP_FOR_TOPIC and len(w) >= 2]

    if not topic_words:
        return _default_name(project_type)

    # Pega ate 4 primeiras palavras significativas
    topic = "_".join(topic_words[:4])

    # Prefixa com tipo de projeto se nao redundar
    prefix_map = {
        "static_site":      "site",
        "interactive_site": "site",
        "web_app":          "webapp",
        "rest_api":         "api",
        "fullstack_web":    "fullstack",
        "python_cli":       "cli",         # v21.4: CLI explicito recebe prefix "cli_"
        "python_script":    "script",
        "python_gui":       "sistema",     # v21.4: GUI e o default → prefix "sistema_"
        "python_game":      "jogo",
        "python_data":      "data",
        "python_automation": "automacao",
        "python_bot":       "bot",
        "node_js":          "node",
        "documentation":    "docs",
    }
    prefix = prefix_map.get(project_type, "projeto")

    if prefix in topic.split("_"):
        return topic  # ja tem o prefix
    return f"{prefix}_{topic}"


def _default_name(project_type: str) -> str:
    return {
        "static_site":      "site_novo",
        "interactive_site": "site_interativo",
        "web_app":          "webapp_novo",
        "rest_api":         "api_nova",
        "python_cli":       "sistema_novo",
        "python_script":    "script_novo",
        "python_gui":       "gui_nova",
        "python_game":      "jogo_novo",
        "python_data":      "analise_dados",
        "python_automation": "automacao",
        "python_bot":       "bot_novo",
        "node_js":          "node_novo",
        "documentation":    "docs",
    }.get(project_type, "projeto_novo")


# ═══════════════════════════════════════════════════════════════════
#  Escolha de modelo (Sonnet vs Haiku)
# ═══════════════════════════════════════════════════════════════════

# Project types que QUASE SEMPRE merecem Sonnet (conteudo rico ou multi-arquivo)
_ALWAYS_SONNET_TYPES = {
    "python_cli", "fullstack_web", "rest_api", "web_app",
    "python_gui", "python_game", "python_data", "python_bot",
}


def needs_sonnet(task: str, project_type: str, complexity: str) -> bool:
    """
    Decide se vale Sonnet (caro mas qualitativo).
    Politica:
    - prototype + static_site simples -> Haiku
    - complexity professional ou medium -> Sonnet
    - tipos que sempre merecem -> Sonnet
    - resto -> Haiku
    """
    if complexity == "professional":
        return True
    if complexity == "medium":
        return True
    if project_type in _ALWAYS_SONNET_TYPES:
        return True
    # static_site pequeno com tema rico (perfil/portfolio) -> Sonnet
    t = _normalize(task)
    rich_content_markers = (
        "portfolio", "portfólio", "curriculo", "currículo", "biografia",
        "apresentacao pessoal", "apresentação pessoal", "linkedin",
        "github.com", "redes sociais",
    )
    if any(m in t for m in rich_content_markers):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """lowercase + remove acentos para matching robusto."""
    if not text:
        return ""
    text = text.lower()
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accent


def analyze(task: str) -> dict:
    """
    Funcao publica unica que devolve TUDO de uma vez.
    Usada pelo CodeAgent para 1 chamada centralizada.

    Returns:
        {
            "project_type": str,
            "complexity": str,
            "stack": str,
            "dependencies": list[str],
            "languages": set[str],
            "topic": str,
            "needs_sonnet": bool,
        }
    """
    ptype = detect_project_type(task)
    complexity = detect_complexity(task)
    stack = detect_stack(task, ptype)
    deps = extract_dependencies(task)
    langs = extract_languages(task)
    topic = extract_topic(task, ptype)
    sonnet = needs_sonnet(task, ptype, complexity)

    return {
        "project_type": ptype,
        "complexity": complexity,
        "stack": stack,
        "dependencies": deps,
        "languages": langs,
        "topic": topic,
        "needs_sonnet": sonnet,
    }
