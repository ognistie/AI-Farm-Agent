"""
code_validators.py — Validacoes enriquecidas para o CodeAgent.

Cobrem qualidade real do codigo gerado, nao so sintaxe.

Camadas:
1. Sintaxe — ast.parse passa
2. Estrutura — quantos arquivos por extensao
3. Qualidade — placeholders, tamanho minimo, anti-cross-tech
4. Tema — pasta/title refletem a task (anti vazamento)
5. Defesa — substitui os.startfile -> webbrowser.open, anti inline program
"""

from __future__ import annotations

import ast
import re
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
#  Placeholders proibidos
# ═══════════════════════════════════════════════════════════════════

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bLorem ipsum\b", re.I),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bxxx\b", re.I),
    re.compile(r"<title>\s*(meu site|seu site|site)\s*</title>", re.I),
    re.compile(r"<h1>\s*(bem-?vindo|seu titulo|titulo aqui)\s*</h1>", re.I),
    re.compile(r"#\s*adicione\s+seu\s+codigo\s+aqui", re.I),
    re.compile(r"\bcoloque\s+seu\s+conteudo\b", re.I),
    re.compile(r"/\*\s*styles?\s+css\s+placeholder\s*\*/", re.I),
    re.compile(r"\.\.\.\s*$", re.M),   # linha terminando com ... (ellipsis solto)
]


def detect_placeholders(code: str) -> list[str]:
    """Retorna lista de placeholders encontrados no codigo (vazia = limpo)."""
    found = []
    for pat in PLACEHOLDER_PATTERNS:
        m = pat.search(code)
        if m:
            found.append(m.group(0)[:60])
    return found


# ═══════════════════════════════════════════════════════════════════
#  Tamanhos minimos por tipo
# ═══════════════════════════════════════════════════════════════════

# Tamanho minimo em chars do CONTEUDO escrito para cada arquivo critico.
# Mede o tamanho da string passada ao with open(...).write(...)
#
# v21.4: main.py reduzido de 500 -> 250. Em sistemas modulares, main.py
# costuma ser um delegador curto (imports + chamada de outras funcoes).
# Forcar 500 chars empurrava o LLM a inflar com codigo desnecessario
# OU a falhar quando ja tinha conteudo legitimo curto. Outros arquivos
# (database/cli/etc) ja sao validados por validate_min_files.
MIN_CONTENT_SIZES = {
    "main.py":      250,   # delegador minimo (imports + chamada principal)
    "index.html":   400,   # HTML com conteudo tematico real
    "style.css":   1500,   # CSS com 80+ linhas reais (~1.5KB)
    "script.js":    300,
    "README.md":    200,
}


def _extract_file_contents(code: str) -> dict[str, str]:
    """
    Extrai aproximadamente o conteudo escrito em cada arquivo no creator script.
    Usa heuristica: procura por `variavel = '''...'''` seguido de
    `with open(..., 'X.py'/'X.html'/...) as f: f.write(variavel)`.
    Retorna {filename: content_approx}.
    """
    files: dict[str, str] = {}

    # Capture: variavel = '''...'''
    var_pattern = re.compile(
        r"^([a-zA-Z_][\w]*)\s*=\s*(?:r?)('{3}|\"{3})(.*?)\2",
        re.MULTILINE | re.DOTALL,
    )
    vars_map: dict[str, str] = {}
    for m in var_pattern.finditer(code):
        var, _, content = m.group(1), m.group(2), m.group(3)
        vars_map[var] = content

    # Capture: with open(..., 'X.ext', ...) ... .write(VAR)
    # ou f.write(VAR)
    open_pattern = re.compile(
        r"open\s*\([^)]*['\"]([\w./-]+\.(?:py|html|css|js|md|json|txt|yml|yaml|toml))['\"][^)]*\)",
        re.IGNORECASE,
    )
    write_pattern = re.compile(
        r"\.write\(\s*([a-zA-Z_][\w]*)\s*\)",
    )

    # Junta sequencialmente: cada `open(...filename...)` casa com a proxima `write(var)`
    opens = list(open_pattern.finditer(code))
    writes = list(write_pattern.finditer(code))

    for o in opens:
        filename = o.group(1).split("/")[-1]
        pos = o.end()
        # proxima write apos esse open
        next_write = next((w for w in writes if w.start() > pos), None)
        if next_write:
            var = next_write.group(1)
            content = vars_map.get(var, "")
            files[filename] = content
            writes = [w for w in writes if w.start() > next_write.end()]

    # Fallback: f.write('''...''')  inline (sem var intermediaria)
    inline_pattern = re.compile(
        r"open\s*\([^)]*['\"]([\w./-]+\.(?:py|html|css|js|md))['\"][^)]*\)"
        r".*?\.write\(\s*(?:r?)('{3}|\"{3})(.*?)\2",
        re.DOTALL,
    )
    for m in inline_pattern.finditer(code):
        filename = m.group(1).split("/")[-1]
        if filename not in files:
            files[filename] = m.group(3)

    return files


def validate_file_sizes(code: str, project_type: str) -> Optional[str]:
    """
    Verifica que arquivos criticos tem tamanho >= minimo.
    Retorna mensagem de erro ou None se tudo ok.
    """
    files = _extract_file_contents(code)

    # Filtra so arquivos relevantes pro project_type
    relevant = {
        "static_site":       ["index.html", "style.css"],
        "interactive_site":  ["index.html", "style.css", "script.js"],
        "python_cli":        ["main.py"],
        "python_gui":        ["main.py"],
        "python_game":       ["main.py"],
        "rest_api":          ["main.py"],
    }.get(project_type, [])

    for fname in relevant:
        content = files.get(fname, "")
        minsize = MIN_CONTENT_SIZES.get(fname, 0)
        if not content:
            continue  # arquivo nao detectado nesta heuristica; outra validacao trata
        if len(content.strip()) < minsize:
            return (
                f"Arquivo '{fname}' muito pequeno ({len(content.strip())} chars, "
                f"minimo {minsize}). Adicione conteudo real e substancial."
            )

    return None


# ═══════════════════════════════════════════════════════════════════
#  Contagem de arquivos por extensao
# ═══════════════════════════════════════════════════════════════════

def count_files_by_ext(code: str) -> dict[str, int]:
    """
    Conta arquivos distintos criados pelo creator script, agrupados por ext.

    v21.5: filtra extensoes numericas (.0, .1, .9) que vinham de strings como
    'python>=3.0' ou '1.0.0' — versoes de pacote nao sao arquivos.
    Tambem filtra .py/.html/.css/.js/.md/etc devem ter no minimo 1 letra alfa.
    """
    counts: dict[str, int] = {}
    seen = set()
    for m in re.finditer(r"""['"]([\w/.\-]+\.(\w{1,6}))['"]""", code):
        name = m.group(1)
        ext_raw = m.group(2).lower()
        # ext precisa ter pelo menos 1 letra alfabetica (filtra .0 .99 etc)
        if not any(c.isalpha() for c in ext_raw):
            continue
        if name.endswith("__init__.py"):
            continue
        if name in seen:
            continue
        seen.add(name)
        ext = "." + ext_raw
        counts[ext] = counts.get(ext, 0) + 1
    return counts


# ═══════════════════════════════════════════════════════════════════
#  Anti-cross-tech (Python NAO cria .html, site NAO cria .py)
# ═══════════════════════════════════════════════════════════════════

def detect_cross_tech_violations(code: str, project_type: str) -> Optional[str]:
    """Retorna erro se o codigo cria arquivos de outra tech."""
    counts = count_files_by_ext(code)

    if project_type in ("static_site", "interactive_site", "web_app"):
        py = counts.get(".py", 0)
        if py > 0:
            return (
                f"Projeto web nao deve criar arquivos .py ({py} detectado). "
                "So HTML/CSS/JS."
            )

    if project_type in ("python_cli", "python_script", "python_gui",
                        "python_game", "python_data", "python_automation",
                        "python_bot"):
        bad = sum(counts.get(ext, 0) for ext in (".html", ".css", ".js"))
        if bad > 0:
            return (
                f"Projeto Python nao deve criar arquivos web ({bad} detectado: "
                f"{counts}). So .py, .md, .txt, .json, requirements.txt."
            )

    if project_type == "static_site":
        js = counts.get(".js", 0)
        if js > 0:
            return (
                f"Tarefa pediu site estatico (HTML+CSS). Detectei {js} arquivo(s) "
                ".js — REMOVA. Apenas index.html e style.css."
            )

    return None


# ═══════════════════════════════════════════════════════════════════
#  Validacao multi-arquivo (sistema python = >=3 .py + README)
# ═══════════════════════════════════════════════════════════════════

MIN_FILES_BY_TYPE = {
    "python_cli":   {"py": 3, "md": 1},   # main + database + cli + README
    "rest_api":     {"py": 3, "md": 1},
    "fullstack_web": {"py": 2, "html": 1, "css": 1},
    # v21.4: python_gui agora e DEFAULT para "sistema" — exige 3+ .py
    # (main + ui + database) + README pra ser realmente um sistema completo
    "python_gui":   {"py": 3, "md": 1},
    "python_data":  {"py": 1, "md": 1},
    "interactive_site": {"html": 1, "css": 1, "js": 1},
    "static_site":  {"html": 1, "css": 1},
}


def validate_min_files(code: str, project_type: str) -> Optional[str]:
    """Garante que o creator script cria a quantidade minima por extensao.

    v5.1: retorna o mesmo formato (msg ou None) — eh usado em ambos os
    paths (HARD severo + SOFT marginal). A funcao validate_min_files_severity
    abaixo classifica.
    """
    requirements = MIN_FILES_BY_TYPE.get(project_type, {})
    if not requirements:
        return None

    counts = count_files_by_ext(code)
    for ext, minimum in requirements.items():
        actual = counts.get("." + ext, 0)
        if actual < minimum:
            return (
                f"Projeto '{project_type}' precisa de >={minimum} arquivos .{ext}, "
                f"mas o creator script cria apenas {actual}. "
                f"Atual: {counts}."
            )

    return None


def validate_min_files_severity(code: str, project_type: str) -> tuple[str, Optional[str]]:
    """
    Retorna (severity, mensagem).

    severity:
      'ok'       — atende o minimo, tudo certo
      'marginal' — tem alguns mas falta <=1 (warning)
      'severe'   — tem 0 ou menos de metade (bloqueia)

    Razao: virar min_files inteiramente em SOFT permitiu que LLM gerasse
    creator scripts SEM NENHUM arquivo (0 .py em projeto python_gui). Sistema
    vazio nao serve ao usuario. Sistema com 1 arquivo a menos do ideal SERVE.
    """
    requirements = MIN_FILES_BY_TYPE.get(project_type, {})
    if not requirements:
        return ("ok", None)

    counts = count_files_by_ext(code)
    worst_severity = "ok"
    worst_msg = None

    for ext, minimum in requirements.items():
        actual = counts.get("." + ext, 0)
        if actual >= minimum:
            continue
        # Gradacao: <50% do minimo OU 0 = severo. Senao marginal.
        if actual == 0 or actual * 2 < minimum:
            severity = "severe"
        else:
            severity = "marginal"
        msg = (
            f"Projeto '{project_type}' precisa de >={minimum} arquivos .{ext}, "
            f"mas o creator script cria apenas {actual}. Atual: {counts}."
        )
        # Severe sobrescreve marginal
        if severity == "severe":
            return ("severe", msg)
        if worst_severity == "ok":
            worst_severity = "marginal"
            worst_msg = msg

    return (worst_severity, worst_msg)


def validate_creates_any_file(code: str) -> Optional[str]:
    """
    HARD: o creator script DEVE criar pelo menos 1 arquivo via open().
    Sem isso, o output e literalmente nada — pior caso possivel.

    Detecta padroes:
      open(..., 'w')
      open(..., 'wb')
      Path(...).write_text/write_bytes
    """
    if re.search(r"open\s*\([^)]*['\"]\w", code) and "'w'" in code or '"w"' in code:
        return None
    if re.search(r"\.write_text\s*\(", code) or re.search(r"\.write_bytes\s*\(", code):
        return None
    # Procura mais permissivo: open + qualquer write
    if re.search(r"open\s*\([^)]+\)[^.]*\.write", code, re.DOTALL):
        return None
    if re.search(r"open\s*\([^)]+,\s*['\"]w", code):
        return None

    return (
        "O creator script NAO cria nenhum arquivo via open(..., 'w'). "
        "Voce DEVE escrever algo no disco para o projeto existir. "
        "Use: with open(os.path.join(project_dir, 'X.py'), 'w', encoding='utf-8') "
        "as f: f.write(conteudo)"
    )


# ═══════════════════════════════════════════════════════════════════
#  Inline program vs creator script
# ═══════════════════════════════════════════════════════════════════

INLINE_RUN_PATTERNS = [
    (".mainloop()",       "Tkinter mainloop"),
    ("app.run(",          "Flask/FastAPI app.run"),
    ("uvicorn.run(",      "Uvicorn run"),
    (".serve_forever()",  "HTTP server"),
    ("ctk.CTk()",         "CustomTkinter root"),
    ("pygame.init()",     "pygame init top-level"),
]


def _strip_triple_quoted_strings(code: str) -> str:
    """Remove conteudo entre ''' ... ''' e ""\" ... ""\" para analisar
    apenas o nivel top-level do creator script (ignora corpo das strings
    que serao gravadas em arquivos)."""
    cleaned = re.sub(r"'''.*?'''", "''", code, flags=re.DOTALL)
    cleaned = re.sub(r'""".*?"""', '""', cleaned, flags=re.DOTALL)
    return cleaned


def detect_inline_program(code: str) -> Optional[str]:
    """
    Retorna motivo se code parece ser o PROGRAMA inline (sem criar arquivos).
    Para passar, o codigo precisa ter `open(..., 'X.py', 'w')`.

    v5: detecta tambem classes que herdam de tkinter/ctk DEFINIDAS no
    TOP-LEVEL do creator script (forma comum do LLM errar em projetos GUI).

    Estrategia: limpa o conteudo das strings triple-quoted ANTES de
    procurar patterns de "programa rodando". Assim, codigo legitimo que
    tem mainloop() DENTRO de uma string nao da falso-positivo.
    """
    # IMPORTANTE: analisa apenas o codigo TOP-LEVEL, removendo o conteudo
    # das strings triple-quoted (que serao escritas em arquivos).
    cleaned = _strip_triple_quoted_strings(code)

    detected = None
    for pat, label in INLINE_RUN_PATTERNS:
        if pat in cleaned:
            detected = label
            break

    # v5 — detecta classe GUI definida diretamente no top-level
    if not detected:
        gui_class_pattern = re.compile(
            r"^class\s+\w+\s*\(\s*(?:tk\.Tk|ctk\.CTk|customtkinter\.CTk|"
            r"QMainWindow|QWidget|QApplication)\s*\)",
            re.MULTILINE,
        )
        m = gui_class_pattern.search(cleaned)
        if m:
            detected = f"classe GUI no top-level: '{m.group(0)[:50]}'"

    if not detected:
        return None

    # Verifica se cria pelo menos 1 .py via open() (no codigo ORIGINAL,
    # porque o open() esta no top-level mas o nome 'main.py' pode estar
    # em string — checamos a string original)
    has_file_writes_py = bool(re.search(
        r"open\s*\(\s*[^)]*['\"][\w/.\-]+\.py['\"]", code
    ))
    if has_file_writes_py:
        # Tem file writes e o detectado estava em codigo top-level que ja
        # nao foi limpado → realmente eh inline. Mas se foi falso-positivo
        # de string nao-fechada, a validacao de truncamento ja pegou antes.
        return (
            f"O campo 'code' parece ser o PROGRAMA em si (detectei {detected} "
            "no top-level). Voce escreveu logica de UI DIRETAMENTE no creator "
            "script. Toda essa logica DEVE estar DENTRO de strings "
            "triple-quoted que serao gravadas em arquivos .py. "
            "Exemplo correto: "
            "main_py = '''import customtkinter as ctk\\nclass App(ctk.CTk): ...''' "
            "e depois with open(...'main.py', 'w') as f: f.write(main_py)."
        )
    # Sem file writes E com mainloop/class GUI top-level → claramente inline
    return (
        f"O campo 'code' parece ser o PROGRAMA em si (detectei {detected}). "
        "Voce deveria escrever um CREATOR SCRIPT que CRIA arquivos com open(). "
        "TODA logica de UI deve estar DENTRO de strings triple-quoted."
    )


# ═══════════════════════════════════════════════════════════════════
#  os.startfile -> webbrowser.open
# ═══════════════════════════════════════════════════════════════════

def replace_startfile_with_webbrowser(code: str) -> tuple[str, int]:
    """
    Substitui os.startfile(...) por webbrowser.open(...) quando o script
    lida com HTML. Retorna (codigo_novo, num_substituicoes).
    """
    if "os.startfile" not in code:
        return code, 0

    code_low = code.lower()
    deals_with_html = (
        ".html" in code_low or ".htm'" in code_low or '.htm"' in code_low
    )
    if not deals_with_html:
        return code, 0

    count = 0

    def replace(m):
        nonlocal count
        count += 1
        arg = m.group(1).strip()
        return (
            "webbrowser.open('file:///' + ("
            + arg + ").replace('\\\\', '/'))"
        )

    new_code = re.sub(r"os\.startfile\s*\(([^)]+)\)", replace, code)

    if count and "import webbrowser" not in new_code:
        new_code = "import webbrowser\n" + new_code
    return new_code, count


# ═══════════════════════════════════════════════════════════════════
#  Sintaxe (ast.parse)
# ═══════════════════════════════════════════════════════════════════

def validate_syntax(code: str) -> Optional[str]:
    """Retorna mensagem de erro de sintaxe ou None se OK."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        snippet = ""
        try:
            snippet = code.split("\n")[(e.lineno or 1) - 1][:120]
        except Exception:
            pass
        return (
            f"SyntaxError linha {e.lineno}: {e.msg}. Linha: `{snippet}`. "
            "Provavel string triple-quoted nao fechada ou escape errado."
        )


# ═══════════════════════════════════════════════════════════════════
#  Validacao de tema (anti-vazamento de exemplos)
# ═══════════════════════════════════════════════════════════════════
#
# v21.1 — Estrategia POSITIVA em vez de blacklist:
#   - Antes: tinha blacklist de palavras "de exemplo" (dental, paciente,
#     consulta...). DESASTRE: quando o usuario pedia algo sobre dentista,
#     o validator confundia com vazamento e bloqueava codigo legitimo.
#   - Agora: extraimos as palavras-tema da TASK ORIGINAL. Se o codigo
#     gerado tem 0 dessas palavras E o topic tem palavras significativas,
#     pode ser vazamento. Caso contrario, ok.
# ═══════════════════════════════════════════════════════════════════

# Stopwords gerais para extracao de palavras-tema da task
_THEME_STOPWORDS = {
    "que", "para", "como", "onde", "quando", "para", "mas", "porem",
    "uma", "umas", "uns", "dos", "das", "dois", "tres", "sobre",
    "abra", "abrir", "abre", "crie", "criar", "cria", "faca", "faça",
    "fazer", "novo", "nova", "mesmo", "mesma", "outro", "outra",
    "site", "sites", "pagina", "página", "sistema", "sistemas",
    "app", "aplicativo", "programa", "script", "projeto", "arquivo",
    "arquivos", "completo", "completa", "profissional", "moderno",
    "moderna", "simples", "html", "css", "javascript", "python",
    "node", "express", "flask", "fastapi", "django", "react", "vue",
    "vscode", "vs", "code", "editor", "ide", "tkinter", "customtkinter",
    "pygame", "pandas", "numpy", "matplotlib",
    "voce", "você", "tem", "vai", "vou", "esta", "está",
    "minha", "meu", "seu", "sua", "deles", "delas",
}


def _extract_theme_words(text: str, min_len: int = 4) -> set[str]:
    """
    Extrai palavras-tema significativas do texto (substantivos provaveis).
    Lowercase + acentos removidos. Filtra stopwords e palavras curtas.
    """
    if not text:
        return set()
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower())
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    words = re.findall(r"[a-z0-9]+", no_accent)
    return {w for w in words if len(w) >= min_len and w not in _THEME_STOPWORDS}


def detect_theme_leak(code: str, topic: str,
                      task: str = "") -> Optional[str]:
    """
    Detecta vazamento de tema: o LLM copiou o tema do EXEMPLO do prompt
    em vez de seguir o tema da TASK do usuario.

    Estrategia POSITIVA:
    - Extrai palavras-tema da TASK original (ex: "dentista", "agendamento")
    - Verifica se o CODIGO contem PELO MENOS uma dessas palavras
    - Se nao tem nenhuma → provavelmente foi para outro tema (vazamento)
    - Se tem pelo menos uma → e legitimo, OK

    Heuristica conservadora: so dispara quando a task tem >= 2 palavras
    tematicas claras E o codigo nao contem nenhuma delas.
    """
    if not topic and not task:
        return None

    # Palavras-tema da fonte mais confiavel: task original.
    # Topic e fallback (gerado pelo extract_topic).
    source_words = _extract_theme_words(task or topic)
    if len(source_words) < 2:
        # Sem palavras-tema suficientes, nao da pra validar
        return None

    code_low = code.lower()
    hits = [w for w in source_words if w in code_low]

    if not hits:
        # Zero palavras da task aparecem no codigo — provavel vazamento
        return (
            f"Vazamento de tema: a tarefa fala em {sorted(source_words)[:5]} "
            f"mas o codigo gerado nao contem NENHUMA dessas palavras. "
            "Use o tema REAL da tarefa, nao o de exemplos do prompt."
        )

    return None


# ═══════════════════════════════════════════════════════════════════
#  Pipeline completo
# ═══════════════════════════════════════════════════════════════════

def detect_relative_path(code: str) -> Optional[str]:
    """
    v21.2: detecta criacao de pasta em caminho RELATIVO (sem expanduser).
    Razao: o exec do AutomationEngine costumava rodar com CWD = pasta do
    projeto. Codigo como `os.makedirs('pasta_x')` criava DENTRO do projeto.

    Agora forcamos chdir no executor + validamos aqui em profundidade.
    Aceita: os.path.expanduser, os.path.join(BASE, ...), os.environ['USERPROFILE'],
            pathlib.Path.home(), caminho literal absoluto (C:/ ou C:\)
    Rejeita: os.makedirs('nome_pasta', ...) ou Path('nome_pasta')
    """
    # Quaisquer hints de absoluto presentes no codigo
    has_absolute_hint = any(h in code for h in (
        "expanduser",
        "Path.home",
        "USERPROFILE",
        "HOMEDRIVE",
        "BASE",                  # const injetada pelo agent
        "{BASE}",                # placeholder
    ))
    # Tambem aceita caminho literal com C:/ ou C:\
    has_drive_literal = bool(re.search(
        r"['\"][a-zA-Z]:[\\/]", code
    ))
    if has_absolute_hint or has_drive_literal:
        return None

    # Se chegou aqui, NAO tem hint de path absoluto. Verificamos se o codigo
    # faz makedirs/mkdir de algo parecido com nome de pasta.
    rel_pattern = re.compile(
        r"(?:os\.makedirs|os\.mkdir|Path\([^)]*\)\.mkdir)\s*\(\s*"
        r"['\"]([\w\-/.]+)['\"]"
    )
    matches = rel_pattern.findall(code)
    if matches:
        return (
            f"Caminho RELATIVO detectado: makedirs/mkdir em {matches[:3]} sem "
            "expanduser ou path absoluto. Isso cria a pasta DENTRO do diretorio "
            "atual do processo (que costuma ser a pasta do projeto). "
            "USE: project_dir = os.path.join(os.path.expanduser('~'), 'Desktop', '<nome>')"
        )
    return None


def detect_truncated_strings(code: str) -> Optional[str]:
    """
    v21.2: detecta strings triple-quoted nao fechadas (sintoma de output
    truncado por max_tokens). AST ja pega isso como SyntaxError, mas damos
    mensagem mais clara aqui.
    """
    triple_single = code.count("'''")
    triple_double = code.count('"""')
    if triple_single % 2 != 0:
        return ("String triple-quoted com ''' nao foi fechada — output do LLM "
                "provavelmente foi truncado por max_tokens. Divida o conteudo "
                "em variaveis menores: parte1 + parte2.")
    if triple_double % 2 != 0:
        return ('String triple-quoted com """ nao foi fechada — output truncado. '
                "Divida o conteudo em variaveis menores.")
    return None


def validate_cross_references(code: str) -> Optional[str]:
    """
    v21.3: validacao SEMANTICA — imports entre arquivos do projeto.

    Extrai cada arquivo .py criado pelo creator script, faz AST de cada
    um, e verifica que `from X import Y` no arquivo A se refere a Y
    realmente definido em X.py do MESMO projeto.

    Bloqueia codigo com imports quebrados que passariam na sintaxe
    mas quebrariam em runtime:
        main.py:     from database import PatientDB    # ❌ nao existe
        database.py: class DB: ...                     # diferente nome

    NAO valida imports externos (anthropic, flask, pandas) — apenas refs
    entre arquivos do projeto.
    """
    files = _extract_file_contents(code)
    py_files = {n: c for n, c in files.items() if n.endswith(".py")}
    if len(py_files) < 2:
        return None  # so faz sentido com 2+ arquivos

    # Map: filename (sem .py) -> set de defs top-level (funcoes, classes, vars)
    defs_by_module: dict[str, set[str]] = {}
    for fname, content in py_files.items():
        module_name = fname.replace(".py", "").split("/")[-1]
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Sintaxe quebrada em arquivo individual — outra validacao pega
            continue
        defs = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defs.add(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defs.add(node.target.id)
        defs_by_module[module_name] = defs

    # Para cada arquivo, verifica `from X import Y` onde X e modulo do projeto
    for fname, content in py_files.items():
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level != 0:        # imports relativos (raros) — pula
                continue
            if not node.module:
                continue
            target = node.module.split(".")[0]
            if target not in defs_by_module:
                continue  # import de lib externa, OK
            target_defs = defs_by_module[target]
            for alias in node.names:
                name = alias.name
                if name == "*":
                    continue
                if name not in target_defs:
                    return (
                        f"Import quebrado: '{fname}' importa '{name}' de "
                        f"'{target}', mas '{target}.py' nao define '{name}'. "
                        f"Definicoes encontradas em {target}.py: "
                        f"{sorted(target_defs)[:8]}. Corrija o nome ou "
                        f"adicione a definicao."
                    )
    return None


def validate_all(code: str, project_type: str, topic: str = "",
                 task: str = "") -> dict:
    """
    Pipeline de validacao em DUAS categorias:

    HARD (bloqueia + dispara retry — codigo realmente nao roda):
        - truncated_strings
        - syntax
        - relative_path
        - inline_program
        - cross_tech_violations

    SOFT (loga warning mas DEIXA PASSAR — qualidade nao-critica):
        - min_files
        - file_sizes
        - cross_references
        - placeholders
        - theme_leak

    Razao: antes, qualquer dos 11 validators bloqueava. LLM acertava uns
    e errava outros, ficava em pingue-pongue. Agora, codigo que RODA
    passa mesmo com warnings de qualidade — o usuario tem o sistema
    funcional, com aviso opcional do que poderia melhorar.

    Retorna:
        {"ok": True, "code": code_corrigido, "warnings": [...]}
        {"ok": False, "reason": "..."}
    """
    warnings: list[str] = []

    # ═══════════════ HARD: nao roda sem isso ════════════════════════

    # H1. Truncamento (mais especifico que SyntaxError generico)
    err = detect_truncated_strings(code)
    if err:
        return {"ok": False, "reason": err}

    # H2. Sintaxe
    err = validate_syntax(code)
    if err:
        return {"ok": False, "reason": err}

    # H3. Fix automatico: os.startfile -> webbrowser (nao bloqueia)
    code, replaced = replace_startfile_with_webbrowser(code)

    # H4. Caminho relativo — pasta acabaria DENTRO do projeto
    err = detect_relative_path(code)
    if err:
        return {"ok": False, "reason": err}

    # H5. Inline program (sem file writes = nao gera nada)
    err = detect_inline_program(code)
    if err:
        return {"ok": False, "reason": err}

    # H6. Cross-tech (Python criando .html viola intencao do usuario)
    err = detect_cross_tech_violations(code, project_type)
    if err:
        return {"ok": False, "reason": err}

    # H7. v5.1 — criou ZERO arquivos? Sistema vazio = inutil
    err = validate_creates_any_file(code)
    if err:
        return {"ok": False, "reason": err}

    # H8. v5.1 — min_files SEVERO (0 ou <50%) = HARD, marginal = SOFT
    severity, severity_msg = validate_min_files_severity(code, project_type)
    if severity == "severe":
        return {"ok": False, "reason": severity_msg}

    # ═══════════════ SOFT: warnings, nao bloqueia ═══════════════════
    # Sistema pode ter qualidade abaixo do ideal mas RODA.

    if severity == "marginal":
        warnings.append(f"[min_files] {severity_msg}")

    err = validate_cross_references(code)
    if err:
        warnings.append(f"[cross_refs] {err}")

    err = validate_file_sizes(code, project_type)
    if err:
        warnings.append(f"[file_sizes] {err}")

    placeholders = detect_placeholders(code)
    if placeholders:
        warnings.append(f"[placeholders] encontrados: {placeholders[:3]}")

    err = detect_theme_leak(code, topic, task=task)
    if err:
        warnings.append(f"[theme_leak] {err}")

    return {
        "ok": True,
        "code": code,
        "warnings": warnings,
        "fixes_applied": {"startfile_replaced": replaced},
    }
