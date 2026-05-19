"""
CodeAgent v26 — Engenheiro Senior + Designer Senior + Roteador de Intent.

MUDANCAS v26 (vs v25):
- INTENT CLASSIFIER: o agente agora identifica o TIPO da tarefa antes de
  decidir o modo de geracao. Modos suportados:
    1. project_full       — projeto completo com pasta, README, etc (modo v25)
    2. single_file        — 1 arquivo solto (script, util, snippet ja resolvido)
    3. edit_existing      — modificar arquivo existente em path conhecido
    4. open_vscode_folder — apenas abrir VS Code em pasta dada (sem criar nada)
    5. website_simple     — site de 1 pagina (index.html + style.css)

- Prompts especializados por modo: tarefas simples NAO disparam o dual-pass
  pesado. Economia de tokens significativa.

- Princípios do briefing aplicados ao writer script:
  • Idempotencia / blast radius minimo: pasta existente NUNCA e
    sobrescrita silenciosamente. Anexa sufixo _2, _3 e avisa.
  • Read-before-write: modo edit_existing le o arquivo ANTES de modificar.
  • Falha rapida: erros sao printados com mensagem literal, nao mascarados.
  • Path absoluto entre agentes: writer expoe PASTA, ARQUIVO, RUN_ENTRY no
    stdout para consumo pelo orquestrador.

- Mantem 100% compatibilidade com BaseAgent, Maestro, etc.
"""

import json
import getpass
import re

from agents.base_agent import BaseAgent
from core.config import get_config
from core.json_validator import safe_parse

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


# ═══════════════════════════════════════════════════════════════════════
# DESIGN BIBLE — referencia visual injetada nos prompts de projeto
# ═══════════════════════════════════════════════════════════════════════
DESIGN_BIBLE = """
═══════════════════════════════════════════════════════════════════════
DESIGN BIBLE — VOCE TAMBEM E DESIGNER SENIOR
═══════════════════════════════════════════════════════════════════════

REGRA DE OURO:
"Codigo sem design e prototipo. Design sem codigo e mockup.
 Voce entrega PRODUTO."

═══ PALETAS DE COR TESTADAS (use exatamente estes hex) ═══

DARK MODERN (default para sistemas tech / dashboards):
  bg_base    #0a0e1a    bg_surface #131826    bg_elevated #1a2138
  border     #252e48    text       #e6edf3    text_muted  #8b95a8
  accent     #6366f1    accent_2   #22d3ee    success     #10b981
  warning    #f59e0b    danger     #ef4444

DARK PREMIUM (financeiro / corporativo serio):
  bg_base    #0c0c0f    bg_surface #18181b    bg_elevated #27272a
  border     #3f3f46    text       #fafafa    text_muted  #a1a1aa
  accent     #fbbf24    accent_2   #f59e0b    success     #22c55e

DARK NEON (jogos / IA / cyberpunk / dev tools):
  bg_base    #050816    bg_surface #0b1024    bg_elevated #131a3a
  border     #2a3458    text       #eef2ff    text_muted  #a5b4fc
  accent     #22d3ee    accent_2   #8b5cf6    success     #06ffa5

LIGHT MINIMAL (Pantone 2026 Cloud Dancer / saude / educacao):
  bg_base    #fafaf7    bg_surface #ffffff    bg_elevated #f5f5f0
  border     #e5e5e0    text       #18181b    text_muted  #6b7280
  accent     #0ea5e9    accent_2   #6366f1    success     #10b981

EDITORIAL HISTORICO (sites historicos / culturais / museus):
  bg_base    #1b120d    bg_surface #2d1d15    bg_elevated #3a2419
  border     #5c3f2e    text       #f5ecde    text_muted  #d4c0a3
  accent     #d97706    accent_2   #fbbf24

NATURE WARM (eco / sustentavel / wellness / yoga):
  bg_base    #fdfcf7    bg_surface #ffffff    bg_elevated #f3efe5
  border     #e0d9c7    text       #2d3319    text_muted  #6b6754
  accent     #84a98c    accent_2   #cad2c5    danger      #bc4749

VIBRANT CORAL (varejo / fashion / startup criativa):
  bg_base    #ffffff    bg_surface #fef9f5    bg_elevated #fff5ee
  border     #fde4d3    text       #1a0f0a    text_muted  #6b5d54
  accent     #f97316    accent_2   #ec4899    success     #14b8a6

EDUCATIONAL FRESH (escola / lab / agendamento estudantil):
  bg_base    #0f172a    bg_surface #1e293b    bg_elevated #334155
  border     #475569    text       #f1f5f9    text_muted  #94a3b8
  accent     #3b82f6    accent_2   #06b6d4    success     #22c55e

MEDICAL CALM (saude / clinica / farmacia):
  bg_base    #f8fafc    bg_surface #ffffff    bg_elevated #f1f5f9
  border     #cbd5e1    text       #0f172a    text_muted  #64748b
  accent     #0ea5e9    accent_2   #14b8a6    danger      #ef4444

GAMING DARK (jogos / streaming / entretenimento):
  bg_base    #0d0d12    bg_surface #18181f    bg_elevated #25252e
  border     #3a3a45    text       #ffffff    text_muted  #9ca3af
  accent     #a855f7    accent_2   #ec4899    success     #84cc16

═══ TIPOGRAFIA (Google Fonts — sempre importar via @import ou <link>) ═══

Para WEB, combine 1 display + 1 body:
- Tech / SaaS         → Display: "Inter" 700/900   Body: "Inter" 400/500
- Editorial / Premium → Display: "Playfair Display" 700  Body: "Inter" 400
- Historico / Cultural→ Display: "Cinzel" 600  Body: "Cormorant Garamond" 400
- Moderno / Neutro    → Display: "Outfit" 700  Body: "Outfit" 400
- Tech / IA / Code    → Display: "Space Grotesk" 700  Body: "Space Grotesk" 400
                        Mono: "JetBrains Mono" 400
- Friendly / Startup  → Display: "Plus Jakarta Sans" 700  Body: "Plus Jakarta Sans" 400
- Luxury / Fashion    → Display: "Cormorant Garamond" 600  Body: "Inter" 300
- Brutalist / Bold    → Display: "Archivo Black" 900  Body: "Inter" 500

ESCALA TIPOGRAFICA (clamp para responsivo):
  Hero H1: clamp(2.5rem, 6vw, 5.5rem)  font-weight 800-900  line-height 1.05
  H2:      clamp(2rem, 4vw, 3.5rem)    font-weight 700      line-height 1.15
  H3:      clamp(1.5rem, 2.5vw, 2rem)  font-weight 600      line-height 1.3
  Body:    1.0625rem (17px)            font-weight 400      line-height 1.65
  Small:   0.875rem                    font-weight 500      line-height 1.5

═══ TENDENCIAS VISUAIS 2026 — APLICAR SEMPRE QUE COUBER ═══

1. BENTO GRID (PRIORIDADE MAXIMA para landing pages e dashboards)
2. GLASSMORPHISM (UI moments — overlays, cards, navs)
3. KINETIC TYPOGRAPHY (heroes que impactam)
4. SOFT SHADOWS COLORIDAS (com a cor do accent, nao preto)
5. MICRO-INTERACOES (hover, transitions cubic-bezier)
6. SCROLL REVEAL (IntersectionObserver)
7. GRADIENT MESHES / AURORA (backgrounds modernos)

═══ ANTI-PADROES (NUNCA FACA) ═══

NUNCA Tkinter padrao cinza/branco com ttk default
NUNCA HTML sem fontes customizadas (Times New Roman / Arial padrao)
NUNCA botoes quadrados sem border-radius
NUNCA sombras pretas duras (0 2px 5px black)
NUNCA texto centralizado em paragrafos longos
NUNCA fontes < 16px em corpo de texto
NUNCA mais de 3 cores de accent na mesma tela

═══════════════════════════════════════════════════════════════════════
FIM DA DESIGN BIBLE — APLIQUE TUDO ISSO COM CRITERIO
═══════════════════════════════════════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════════════
# INTENT CLASSIFIER — define o MODO antes de gerar codigo
# ═══════════════════════════════════════════════════════════════════════
INTENT_CLASSIFIER_PROMPT = (
    "Voce e um CLASSIFICADOR DE INTENT para tarefas de programacao.\n"
    "Recebe um pedido do usuario e devolve o MODO mais adequado.\n\n"

    "═══ MODOS POSSIVEIS ═══\n\n"

    "1. project_full\n"
    "   Quando: usuario pede SISTEMA, APP, DASHBOARD, PROJETO, PLATAFORMA,\n"
    "   ou descreve algo com MULTIPLAS funcionalidades/telas/entidades.\n"
    "   Exemplos:\n"
    "     - 'crie um sistema de agendamento de salas'\n"
    "     - 'dashboard de vendas com graficos'\n"
    "     - 'app desktop pra controlar tarefas'\n\n"

    "2. website_simple\n"
    "   Quando: usuario pede SITE/PAGINA/LANDING simples, 1-3 paginas HTML.\n"
    "   Exemplos:\n"
    "     - 'crie um site sobre cafe'\n"
    "     - 'pagina de portfolio pessoal'\n"
    "     - 'landing page pra um curso'\n\n"

    "3. single_file\n"
    "   Quando: usuario pede UM ARQUIVO ESPECIFICO — script python utilitario,\n"
    "   arquivo de configuracao, classe isolada, funcao, snippet utilizavel.\n"
    "   Exemplos:\n"
    "     - 'crie um arquivo python que renomeia imagens'\n"
    "     - 'script que le csv e gera relatorio'\n"
    "     - 'um arquivo .gitignore para Python'\n"
    "     - 'classe Calculadora em python'\n"
    "     - 'um helper.js com funcoes de validacao'\n\n"

    "4. edit_existing\n"
    "   Quando: usuario menciona ALTERAR/MODIFICAR/ADICIONAR/CORRIGIR\n"
    "   um arquivo que JA EXISTE em um path conhecido.\n"
    "   Exemplos:\n"
    "     - 'adicione uma rota /login em app.py'\n"
    "     - 'corrija o bug do main.py'\n"
    "     - 'edite o style.css pra escurecer o tema'\n"
    "   IMPORTANTE: so use este modo se o path for IDENTIFICAVEL.\n\n"

    "5. open_vscode_folder\n"
    "   Quando: usuario pede APENAS abrir VS Code em uma pasta especifica,\n"
    "   sem criar nem editar nada novo.\n"
    "   Exemplos:\n"
    "     - 'abra o VS Code na pasta Desktop/meu-projeto'\n"
    "     - 'abre meu projeto no vs code'\n\n"

    "═══ REGRAS ═══\n"
    "- Pense no MENOR escopo que atende a intencao real.\n"
    "- Em duvida entre project_full e single_file → escolha single_file.\n"
    "- Em duvida entre edit_existing e single_file → escolha single_file\n"
    "  (criar e mais seguro que modificar algo que pode nao existir).\n"
    "- 'arquivo' geralmente = single_file. 'sistema/app/dashboard' = project_full.\n"
    "- Se o pedido pode ser feito em 1 arquivo de 50-200 linhas → single_file.\n\n"

    "═══ FORMATO DE RESPOSTA (JSON puro, sem markdown) ═══\n"
    "{\n"
    '  "mode": "project_full | website_simple | single_file | edit_existing | open_vscode_folder",\n'
    '  "reason": "1 frase justificando a escolha",\n'
    '  "filename_hint": "nome de arquivo SUGERIDO (sem path) — para single_file/edit_existing",\n'
    '  "folder_hint": "nome de pasta SUGERIDO — para project_full/website_simple",\n'
    '  "target_path_hint": "path absoluto identificado — para edit_existing/open_vscode_folder",\n'
    '  "language_hint": "python | javascript | html | css | typescript | json | etc"\n'
    "}\n"
)


# ═══════════════════════════════════════════════════════════════════════
# PROMPT — SINGLE FILE (1 arquivo solto)
# ═══════════════════════════════════════════════════════════════════════
SINGLE_FILE_PROMPT = (
    "Voce e ENGENHEIRO SENIOR. Recebe um pedido e entrega UM UNICO ARQUIVO\n"
    "completo, idiomatic, pronto para usar. NADA de pasta com README, nada\n"
    "de requirements.txt, nada de .gitignore. SO o arquivo pedido.\n\n"

    "═══ REGRAS DE CODIGO ═══\n"
    "- Python: type hints onde fizer sentido, docstring curta no topo,\n"
    "  if __name__ == '__main__': quando for script executavel.\n"
    "- JS/TS: ES6+, sem var, sem 'function' classica em codigo moderno.\n"
    "- HTML: doctype + meta charset + viewport meta + lang.\n"
    "- CSS: variaveis no :root, mobile-first quando aplicavel.\n"
    "- SEMPRE codigo COMPLETO e executavel. Nao deixe TODOs nem '...'.\n"
    "- Comentarios: SOMENTE onde o porque nao for obvio.\n"
    "- Trate erros simples (FileNotFoundError, ValueError) quando relevante.\n"
    "- Sem dependencias externas se a stdlib resolver.\n\n"

    "═══ DESTINO DO ARQUIVO ═══\n"
    "- Por padrao: salvar em C:/Users/<user>/Desktop/<filename>.\n"
    "- Se o usuario deu um path absoluto: respeitar.\n"
    "- Nome do arquivo: o hint dado, ou inferir do pedido (snake_case + ext).\n\n"

    "═══ FORMATO DE RESPOSTA — JSON PURO ═══\n"
    "{\n"
    '  "filename": "rename_images.py",\n'
    '  "target_dir": "Desktop"          // ou path absoluto se usuario pediu\n'
    '  "language": "python",\n'
    '  "description": "1 linha do que o arquivo faz",\n'
    '  "content": "<codigo COMPLETO em string com \\n>",\n'
    '  "run_after_create": false,       // true so para scripts utilitarios obvios\n'
    '  "open_in_vscode": true           // abrir o arquivo no VS Code apos criar\n'
    "}\n\n"

    "JSON PURO. Sem ``` sem markdown. Escape aspas com \\\".\n"
)


# ═══════════════════════════════════════════════════════════════════════
# PROMPT — EDIT EXISTING (modificar arquivo existente)
# ═══════════════════════════════════════════════════════════════════════
EDIT_EXISTING_PROMPT = (
    "Voce e ENGENHEIRO SENIOR fazendo MODIFICACAO em arquivo existente.\n"
    "Voce vai receber o CONTEUDO ATUAL e o que precisa mudar.\n\n"

    "═══ REGRAS ═══\n"
    "1. LEIA o conteudo atual com atencao. Preserve tudo que NAO foi pedido\n"
    "   para mudar — formatacao, comentarios, ordem de imports.\n"
    "2. Faca a mudanca MINIMA que atende o pedido. Nada de refactor extra.\n"
    "3. Se o pedido for ambiguo (nao da pra saber ONDE inserir), devolva o\n"
    "   arquivo inalterado e escreva ambiguity_reason.\n"
    "4. Cite no campo 'changes' o que foi alterado (1 linha por mudanca).\n"
    "5. Mantenha o estilo do arquivo original (tabs vs spaces, snake vs camel).\n\n"

    "═══ FORMATO DE RESPOSTA — JSON PURO ═══\n"
    "{\n"
    '  "filename": "<mesmo nome do original>",\n'
    '  "target_path": "<path absoluto recebido>",\n'
    '  "new_content": "<arquivo COMPLETO com a mudanca aplicada>",\n'
    '  "changes": ["adicionada rota /login", "import bcrypt"],\n'
    '  "ambiguity_reason": "" ou descricao se nao deu pra modificar com seguranca\n'
    "}\n\n"

    "JSON PURO.\n"
)


# ═══════════════════════════════════════════════════════════════════════
# PROMPT PASS 1 — DESIGN PLANNING (modo project_full)
# ═══════════════════════════════════════════════════════════════════════
DESIGN_PLANNER_PROMPT = (
    "Voce e um DIRETOR DE ARTE + ARQUITETO DE SOFTWARE senior.\n"
    "Sua missao: ANTES de qualquer codigo, criar um BRIEF DE DESIGN denso\n"
    "para o projeto. Pense como se estivesse direcionando uma agencia.\n\n"

    + DESIGN_BIBLE +

    "\n\n═══ SUA TAREFA ═══\n"
    "Receba a tarefa do usuario e produza um JSON com brief completo.\n"
    "Pense profundamente no DOMINIO REAL antes de escolher paleta/layout.\n"
    "Nao seja generico. Seja ESPECIFICO e CRIATIVO.\n\n"

    "FORMATO DE RESPOSTA — JSON PURO (sem markdown):\n"
    "{\n"
    '  "domain_analysis": "1-2 frases sobre o dominio REAL da tarefa",\n'
    '  "target_audience": "quem usa isso",\n'
    '  "emotion": "como o usuario deve SENTIR (confianca/energia/calma/etc)",\n'
    '  "project_type": "desktop_app | web_site | web_app | game | api | data_viz",\n'
    '  "stack": "ex: customtkinter+sqlite | html+css+js | flask+sqlite",\n'
    '  "folder": "nome_pasta_snake_case",\n'
    '  "title": "Nome bonito do produto",\n'
    '  "tagline": "1 frase de marketing",\n'
    '  "palette_name": "DARK MODERN | DARK PREMIUM | EDITORIAL HISTORICO | etc",\n'
    '  "palette": {"bg_base":"#xxxxxx","bg_surface":"#xxxxxx","bg_elevated":"#xxxxxx","border":"#xxxxxx","text":"#xxxxxx","text_muted":"#xxxxxx","accent":"#xxxxxx","accent_2":"#xxxxxx","success":"#xxxxxx","danger":"#xxxxxx"},\n'
    '  "typography": {"display_font":"...","body_font":"...","mono_font":"JetBrains Mono"},\n'
    '  "visual_trends": ["bento_grid","glassmorphism","kinetic_type","soft_shadows","scroll_reveal"],\n'
    '  "entities": [{"name":"...","fields":["..."]}],\n'
    '  "screens_or_sections": [{"name":"...","purpose":"..."}],\n'
    '  "key_features": ["..."],\n'
    '  "seed_data_plan": "Descrever 5-15 registros realistas",\n'
    '  "file_structure": ["main.py","config.py","..."],\n'
    '  "open_in_browser": false,\n'
    '  "browser_entry": null,\n'
    '  "run_entry": "main.py"\n'
    "}\n\n"

    "REGRAS:\n"
    "- Escolha palette do catalogo da DESIGN BIBLE (use os hex EXATOS)\n"
    "- Para sistemas: project_type='desktop_app', stack inclui 'customtkinter'\n"
    "- Para sites: project_type='web_site', stack depende do que o usuario pediu\n"
    "- file_structure deve ter 3-15 arquivos com paths reais\n"
    "- Pelo menos 2 visual_trends por projeto\n"
    "- JSON PURO. Sem ``` sem markdown sem texto antes/depois.\n\n"

    "═══ REGRA DE STACK = LITERAL DO USUARIO (PRIORIDADE MAXIMA) ═══\n"
    "Leia a tarefa e identifique TECH que o usuario MENCIONOU explicitamente.\n"
    "Sua file_structure DEVE conter apenas extensoes que ele pediu (+ README/\n"
    "requirements/gitignore quando aplicavel).\n\n"
    "EXEMPLOS — siga LITERALMENTE:\n"
    "- 'site em HTML e CSS sobre X':\n"
    "    stack='html+css', file_structure=['index.html', 'style.css', 'README.md']\n"
    "    PROIBIDO incluir script.js ou qualquer .js.\n"
    "- 'site em HTML, CSS e JS sobre X':\n"
    "    stack='html+css+js', file_structure=['index.html', 'style.css', 'script.js', 'README.md']\n"
    "- 'site sobre X' (sem mencionar tech):\n"
    "    stack='html+css+js', file_structure pode incluir os 3 + README.\n"
    "- 'sistema em python para X':\n"
    "    stack='python+sqlite', file_structure=['main.py', 'database.py', ...]\n"
    "    PROIBIDO incluir .html/.css/.js a menos que o sistema seja web.\n"
    "- 'sistema flask para X':\n"
    "    stack='flask+sqlite', file_structure=['app.py', 'templates/*.html', 'static/*.css', ...]\n"
    "Resumo: SE o usuario LISTOU as tecnologias, o file_structure NAO pode\n"
    "ter extensao fora dessa lista (exceto docs/config padrao).\n"
)


# ═══════════════════════════════════════════════════════════════════════
# PROMPT PASS 2 — CODE GENERATION (modo project_full)
# ═══════════════════════════════════════════════════════════════════════
CODE_BUILDER_PROMPT = (
    "Voce e um ENGENHEIRO SENIOR + DESIGNER que executa o BRIEF entregue.\n"
    "Seu codigo e bonito, modular, e RODA na primeira tentativa.\n\n"

    + DESIGN_BIBLE +

    "\n\n═══ COMO USAR O BRIEF ═══\n"
    "Voce recebera um JSON DESIGN_BRIEF. Use TODOS os valores dele:\n"
    "- palette: hex codes EXATOS no codigo\n"
    "- typography: importe Google Fonts via @import url(...) ou <link>\n"
    "- visual_trends: implemente CADA tendencia listada\n"
    "- entities: vire schema SQLite + classes Python\n"
    "- seed_data_plan: popule no primeiro run\n"
    "- file_structure: gere TODOS os arquivos listados\n\n"

    "═══ REGRAS DE CODIGO ═══\n"
    "- HTML: semantica (header, nav, main, section, article, footer)\n"
    "- CSS: variaveis no :root com TODA a paleta do brief\n"
    "- CSS: clamp() para responsivo, grid/flex modernos, transitions\n"
    "- JS: vanilla ES6+, IntersectionObserver para scroll reveal\n"
    "- Python: type hints, dataclasses, context managers para DB\n"
    "- CTk: classes customizadas para cards/sidebar/header\n"
    "- SEMPRE README.md, requirements.txt, .gitignore\n"
    "- SEMPRE seed data executado no primeiro start\n\n"

    "═══ INTEGRIDADE OBRIGATORIA (NUNCA QUEBRE) ═══\n"
    "1. CODIGO COMPLETO: cada arquivo precisa abrir e fechar TODAS as aspas,\n"
    "   parenteses, chaves, colchetes, f-strings, blocos try/with/if. NUNCA\n"
    "   deixe 'print(f\"...' sem fechar a aspas e o parenteses.\n"
    "2. NADA DE PLACEHOLDERS: proibido '...', 'TODO', 'pass # implementar',\n"
    "   'continuar aqui'. Cada funcao tem implementacao real.\n"
    "3. IMPORTS COERENTES: todo 'from X.Y import Z' precisa ter o arquivo\n"
    "   X/Y.py LISTADO em files. Se voce importou 'database.db_manager',\n"
    "   ENTAO inclua 'database/db_manager.py' com a classe DatabaseManager.\n"
    "   Faltar arquivo = ModuleNotFoundError em runtime.\n"
    "4. ASSETS NO HTML: todo <link href=\"X.css\"> e <script src=\"X.js\">\n"
    "   precisa apontar pra arquivo presente em files (path RELATIVO certo).\n"
    "   E o INVERSO tambem: se voce listou style.css em files, o HTML PRECISA\n"
    "   referenciar via <link rel=\"stylesheet\" href=\"style.css\">.\n"
    "5. RESPEITE A TECH DO USUARIO (CRITICO):\n"
    "   - 'apenas HTML' / 'so HTML': files = {'index.html': '...'}\n"
    "     (CSS inline em <style>, JS inline em <script>)\n"
    "   - 'HTML e CSS' / 'HTML, CSS' / 'HTML+CSS':\n"
    "     files = {'index.html': '...', 'style.css': '...', 'README.md': '...'}\n"
    "     PROIBIDO chave terminando em '.js' no files dict.\n"
    "   - 'HTML, CSS, JS' / 'HTML, CSS e JavaScript':\n"
    "     files = {'index.html', 'style.css', 'script.js', 'README.md'}\n"
    "   - 'sistema em python': zero .html/.css/.js (a menos que seja web).\n"
    "6. AUTO-CHECK ANTES DE RESPONDER: pra cada arquivo Python, releia\n"
    "   mentalmente verificando parens/aspas balanceadas. Pra cada import,\n"
    "   confira que o arquivo correspondente esta no dict. Pra cada extensao\n"
    "   no files dict, confira que o usuario MENCIONOU aquela tech.\n\n"

    "═══ FORMATO DE RESPOSTA — JSON PURO ═══\n"
    "{\n"
    '  "folder": "<copia do brief>",\n'
    '  "description": "Sistema X com Y para Z",\n'
    '  "stack": "<copia do brief>",\n'
    '  "theme": "<palette_name do brief>",\n'
    '  "files": {\n'
    '    "main.py": "<codigo COMPLETO>",\n'
    '    "config.py": "<codigo>",\n'
    '    "README.md": "<markdown completo>",\n'
    '    "requirements.txt": "<libs com versoes>",\n'
    '    ".gitignore": "<gitignore>"\n'
    "  },\n"
    '  "run_entry": "main.py",\n'
    '  "browser_entry": null,\n'
    '  "open_in_browser": false,\n'
    '  "open_in_vscode": true\n'
    "}\n\n"

    "JSON PURO. Sem ``` sem markdown. Use \\n para quebras de linha nos arquivos.\n"
    "Escape aspas internas com \\\". Cada arquivo COMPLETO e funcional.\n"
)


# Fallback single-pass (modo project_full quando dual_pass desligado)
SINGLE_PASS_PROMPT = (
    "Voce e ENGENHEIRO SENIOR + DESIGNER SENIOR.\n"
    "Voce gera codigo profissional E visualmente impressionante.\n\n"

    + DESIGN_BIBLE +

    "\n\n═══ SUA TAREFA ═══\n"
    "Analise PROFUNDAMENTE o dominio. Escolha paleta, fontes e layout do\n"
    "catalogo da DESIGN BIBLE. Gere codigo modular, bonito, funcional.\n\n"

    "REGRAS ABSOLUTAS:\n"
    "1. NUNCA Tkinter cinza generico — sempre CustomTkinter com tema\n"
    "2. NUNCA HTML sem fontes Google — sempre @import\n"
    "3. SEMPRE micro-interacoes (hover, transitions)\n"
    "4. SEMPRE seed data realista (5-15 registros)\n"
    "5. SEMPRE README, requirements.txt, .gitignore\n"
    "6. SEMPRE pelo menos 2 tendencias visuais 2026 (bento, glass, etc)\n\n"

    "═══ INTEGRIDADE OBRIGATORIA ═══\n"
    "- CODIGO COMPLETO: zero placeholders, zero '...', zero TODO.\n"
    "  Toda aspas/parenteses/chaves abertas precisam fechar.\n"
    "- IMPORTS COERENTES: 'from X.Y import Z' EXIGE 'X/Y.py' presente em files.\n"
    "- ASSETS COERENTES: <link href='X.css'> EXIGE 'X.css' presente em files.\n"
    "- RESPEITE A TECH DO USUARIO: se pediu 'HTML apenas', estilo INLINE\n"
    "  em <style>...</style>; nada de arquivo .css separado.\n\n"

    "FORMATO — JSON PURO:\n"
    "{\n"
    '  "folder": "snake_case",\n'
    '  "description": "1 linha do que e",\n'
    '  "stack": "tech usada",\n'
    '  "theme": "nome da paleta",\n'
    '  "files": {"main.py": "...", "...": "..."},\n'
    '  "run_entry": "main.py",\n'
    '  "browser_entry": "" ou "index.html",\n'
    '  "open_in_browser": true ou false,\n'
    '  "open_in_vscode": true\n'
    "}\n"
)


# ═══════════════════════════════════════════════════════════════════════
# Heuristicas determinsticas — economizam 1 chamada LLM em casos obvios
# ═══════════════════════════════════════════════════════════════════════
_PROJECT_KEYWORDS = (
    "sistema", "dashboard", "aplicativo", "plataforma", "projeto completo",
    "fullstack", "full-stack", "app desktop", "app web", "tela de login",
    "crud", "admin panel", "gerenciador de", "gestao de", "controle de",
)
_SITE_KEYWORDS = (
    "site sobre", "site para", "landing page", "pagina sobre", "site de",
    "portfolio", "site historico", "site institucional", "site da",
)
# Quando o usuario EXPLICITAMENTE diz que quer SO HTML (sem CSS/JS separados),
# trate como single_file pra evitar a expansao do design planner em multi-file.
_HTML_ONLY_MARKERS = (
    "apenas html", "apenas em html", "so html", "só html", "somente html",
    "html simples", "html puro", "html sem css", "html sem js",
    "1 arquivo html", "um arquivo html", "arquivo html unico",
)
_SINGLE_FILE_KEYWORDS = (
    "um arquivo", "uma classe", "uma funcao", "um script", "um snippet",
    "um helper", "um util", "arquivo python", "arquivo .py", "arquivo .js",
    ".gitignore", "regex", "expressao regular", "func ", "function ",
)
_EDIT_KEYWORDS = (
    "edite o arquivo", "edita o arquivo", "modifique o arquivo",
    "modifica o arquivo", "altere o arquivo", "altera o arquivo",
    "corrija no arquivo", "adicione em ", "adiciona em ", "remove de ",
    "remova de ", "atualize o arquivo", "atualiza o arquivo",
)
_OPEN_FOLDER_KEYWORDS = (
    "abra o vs code na pasta", "abra o vscode na pasta",
    "abra a pasta no vs code", "abra a pasta no vscode",
    "abre meu projeto no vs code", "abre meu projeto no vscode",
)


_EXT_DOCS = {"md", "txt", "gitignore", "env"}      # sempre permitidas
_EXT_CONFIG = {"yaml", "yml", "json", "cfg", "ini", "toml"}


def _detect_tech_spec(task_text: str) -> dict:
    """
    Examina o texto do usuario procurando tech declarada EXPLICITAMENTE.
    Retorna:
      {
        "specified": bool,    # True se o usuario listou tech
        "allowed_exts": set,  # extensoes permitidas no projeto final
        "summary": str,       # descricao curta da spec detectada
      }

    Se nada for detectado, o LLM tem liberdade total (specified=False).
    """
    t = (task_text or "").lower()
    if not t:
        return {"specified": False, "allowed_exts": set(), "summary": ""}

    has_html = bool(re.search(r"\bhtml\b", t))
    has_css = bool(re.search(r"\bcss\b", t))
    has_js = bool(re.search(r"\b(js|javascript|jscript)\b", t))
    has_py = bool(re.search(r"\bpython\b", t))
    has_react = bool(re.search(r"\breact\b", t))
    has_vue = bool(re.search(r"\bvue\b", t))
    has_flask = bool(re.search(r"\bflask\b", t))
    has_django = bool(re.search(r"\bdjango\b", t))
    has_fastapi = bool(re.search(r"\bfastapi\b", t))

    allowed = set(_EXT_DOCS) | set(_EXT_CONFIG)
    parts = []

    if has_html or has_css or has_js or has_react or has_vue:
        allowed.add("html")
        parts.append("html")
        if has_css:
            allowed.add("css")
            parts.append("css")
        if has_js or has_react or has_vue:
            allowed.add("js")
            parts.append("js")
        if has_react or has_vue:
            allowed.add("jsx")
            allowed.add("tsx")
            allowed.add("ts")
            parts.append(has_react and "react" or "vue")

    if has_py or has_flask or has_django or has_fastapi:
        allowed.add("py")
        parts.append("python")
        if has_flask or has_django or has_fastapi:
            # web framework Python = pode ter templates html/css
            allowed.add("html")
            allowed.add("css")
            parts.append(has_flask and "flask" or has_django and "django" or "fastapi")
        allowed.add("sql")

    specified = bool(parts)
    summary = "+".join(parts) if parts else "(livre)"
    return {
        "specified": specified,
        "allowed_exts": allowed,
        "summary": summary,
    }


def _filter_files_by_tech(files: dict, tech: dict, logger=None) -> tuple[dict, list]:
    """
    Remove do dict 'files' quaisquer chaves com extensao FORA da spec do usuario.
    Retorna (novo_files, removed_paths).
    Nao faz nada se tech['specified'] for False.
    """
    if not tech.get("specified") or not isinstance(files, dict):
        return files, []
    allowed = tech.get("allowed_exts", set())
    filtered = {}
    removed = []
    for path, content in files.items():
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        # arquivos sem extensao (ex: .gitignore tratado separadamente)
        name = path.split("/")[-1].lower()
        if name == ".gitignore" or name == "license" or name == "dockerfile":
            filtered[path] = content
            continue
        if ext in allowed:
            filtered[path] = content
        else:
            removed.append(path)
    if removed and logger:
        logger.info(
            f"Tech filter removeu {len(removed)} arquivo(s) fora da spec "
            f"({tech['summary']}): {removed}"
        )
    return filtered, removed


def _classify_intent_heuristic(task_text: str) -> dict | None:
    """
    Tenta classificar o intent SEM chamar LLM. Retorna None se nao confiante.
    Economia: 1 chamada LLM em ~40% dos casos.
    """
    t = (task_text or "").lower().strip()
    if not t:
        return None

    # "apenas HTML" / "so HTML" — usuario quer 1 arquivo, inline tudo.
    # Tem prioridade sobre website_simple e single_file genericos.
    for kw in _HTML_ONLY_MARKERS:
        if kw in t:
            return {
                "mode": "single_file",
                "reason": f"usuario pediu HTML inline ({kw})",
                "language_hint": "html",
                "filename_hint": "index.html",
                "inline_assets": True,
            }

    # open_vscode_folder — match de frase explicita
    for kw in _OPEN_FOLDER_KEYWORDS:
        if kw in t:
            path_match = re.search(
                r'(?:pasta|projeto|diretorio)\s+([\w\-./:\\]+)', t
            )
            return {
                "mode": "open_vscode_folder",
                "reason": f"keyword match: {kw}",
                "target_path_hint": path_match.group(1) if path_match else "",
            }

    # edit_existing — palavras-chave fortes + arquivo identificavel
    for kw in _EDIT_KEYWORDS:
        if kw in t:
            file_match = re.search(r'([\w\-/.]+\.[a-zA-Z]{1,5})', task_text)
            if file_match:
                return {
                    "mode": "edit_existing",
                    "reason": f"keyword match: {kw}",
                    "filename_hint": file_match.group(1),
                }

    # project_full — keywords fortes
    for kw in _PROJECT_KEYWORDS:
        if kw in t:
            return {"mode": "project_full", "reason": f"keyword match: {kw}"}

    # website_simple
    for kw in _SITE_KEYWORDS:
        if kw in t:
            return {"mode": "website_simple", "reason": f"keyword match: {kw}"}

    # single_file
    for kw in _SINGLE_FILE_KEYWORDS:
        if kw in t:
            return {"mode": "single_file", "reason": f"keyword match: {kw}"}

    return None  # incerto — cai no classificador LLM


# ═══════════════════════════════════════════════════════════════════════
# CodeAgent
# ═══════════════════════════════════════════════════════════════════════
class CodeAgent(BaseAgent):
    """
    CodeAgent v26 — roteia entre modos antes de gerar.

    Fluxo:
      task → classify intent (heuristica → LLM) → modo
        ├─ project_full       → dual-pass design+code (DESIGN_BIBLE)
        ├─ website_simple     → single-pass com DESIGN_BIBLE focado em web
        ├─ single_file        → SINGLE_FILE_PROMPT (sem README/requirements)
        ├─ edit_existing      → read file → EDIT_EXISTING_PROMPT
        └─ open_vscode_folder → sem LLM, so abre VS Code
    """

    def __init__(self):
        super().__init__(name="CODE", system_prompt=DESIGN_PLANNER_PROMPT)
        self._config = get_config()
        self._use_dual_pass = self._config.get("agents.code.dual_pass", True)

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------
    def _classify_intent(self, task_text: str) -> dict:
        """Heuristica primeiro, LLM como fallback."""
        h = _classify_intent_heuristic(task_text)
        if h:
            self.logger.info(
                f"Intent (heuristica): mode={h['mode']} | reason={h.get('reason','')}"
            )
            return h

        # Fallback LLM — usa modelo rapido (Haiku) pra economizar
        try:
            fast_model = self._config.get("models.fast", self.model)
            raw = self._client.message(
                model=fast_model,
                system=INTENT_CLASSIFIER_PROMPT,
                user_content=f"TAREFA: {task_text}\nJSON puro.",
                max_tokens=500,
            )
            intent = safe_parse(raw, fast_model)
            if not isinstance(intent, dict) or "mode" not in intent:
                raise ValueError("intent invalido")
            self.logger.info(
                f"Intent (LLM): mode={intent.get('mode')} | "
                f"reason={intent.get('reason','')}"
            )
            return intent
        except Exception as e:
            self.logger.warning(
                f"Classificador LLM falhou ({e}); assumindo project_full"
            )
            return {"mode": "project_full", "reason": "fallback default"}

    # ------------------------------------------------------------------
    # PASS 1 — Design Brief (modo project_full)
    # ------------------------------------------------------------------
    def _generate_design_brief(self, task_text: str, context_str: str) -> dict:
        raw = self._client.message(
            model=self.model,
            system=DESIGN_PLANNER_PROMPT,
            user_content=(
                f"TAREFA: {task_text}{context_str}\n\n"
                "Gere o DESIGN BRIEF completo conforme as regras.\n"
                "Pense como diretor de arte: emocao, paleta, tipografia, layout.\n"
                "JSON puro."
            ),
            max_tokens=self._config.get("limits.max_tokens_fast", 2500),
        )
        brief = safe_parse(raw, self.model)
        if not isinstance(brief, dict):
            raise ValueError("DESIGN_BRIEF nao e dict")
        return brief

    def _generate_code_from_brief(self, task_text: str, brief: dict) -> dict:
        brief_str = json.dumps(brief, ensure_ascii=False, indent=2)
        raw = self._client.message(
            model=self.model,
            system=CODE_BUILDER_PROMPT,
            user_content=(
                f"TAREFA ORIGINAL: {task_text}\n\n"
                f"DESIGN_BRIEF (siga RIGOROSAMENTE):\n{brief_str}\n\n"
                "Gere TODOS os arquivos da file_structure do brief.\n"
                "Use as cores EXATAS da palette. Importe as fontes do brief.\n"
                "Implemente CADA visual_trend listada.\n"
                "Popule com seed_data realista no primeiro run.\n"
                "JSON puro."
            ),
            max_tokens=self._config.get("limits.max_tokens_long", 12000),
        )
        plan = safe_parse(raw, self.model)
        if not isinstance(plan, dict):
            raise ValueError("Plano de codigo nao e dict")
        return plan

    def _generate_single_pass(self, task_text: str, context_str: str) -> dict:
        raw = self._client.message(
            model=self.model,
            system=SINGLE_PASS_PROMPT,
            user_content=(
                f"TAREFA: {task_text}{context_str}\n\n"
                "Gere projeto profissional + bonito. JSON puro."
            ),
            max_tokens=self._config.get("limits.max_tokens_long", 10000),
        )
        plan = safe_parse(raw, self.model)
        if not isinstance(plan, dict):
            raise ValueError("Plano single-pass nao e dict")
        return plan

    # ------------------------------------------------------------------
    # SINGLE FILE
    # ------------------------------------------------------------------
    def _generate_single_file(self, task_text: str, intent: dict, context_str: str) -> dict:
        filename_hint = intent.get("filename_hint", "")
        lang_hint = intent.get("language_hint", "")
        inline = bool(intent.get("inline_assets"))

        hint_str = ""
        if filename_hint:
            hint_str += f"\nSUGESTAO DE NOME: {filename_hint}"
        if lang_hint:
            hint_str += f"\nLINGUAGEM SUGERIDA: {lang_hint}"
        if inline and lang_hint == "html":
            hint_str += (
                "\nUSUARIO PEDIU 1 ARQUIVO HTML INLINE — coloque TODO o CSS"
                " dentro de <style> e TODO o JS dentro de <script> no mesmo"
                " index.html. PROIBIDO criar arquivos .css ou .js separados."
                " Aplique design moderno (paleta, fontes Google via @import,"
                " responsivo, hover transitions) mas TUDO em um unico arquivo."
            )

        max_tokens = self._config.get("limits.max_tokens_strong", 4000)
        if inline and lang_hint == "html":
            # HTML inline com design rico precisa de orcamento maior
            max_tokens = self._config.get("limits.max_tokens_long", 10000)

        raw = self._client.message(
            model=self.model,
            system=SINGLE_FILE_PROMPT,
            user_content=(
                f"TAREFA: {task_text}{context_str}{hint_str}\n\n"
                "Gere o arquivo unico COMPLETO (zero TODO, zero '...'). JSON puro."
            ),
            max_tokens=max_tokens,
        )
        result = safe_parse(raw, self.model)
        if not isinstance(result, dict) or "content" not in result:
            raise ValueError("Resposta single_file invalida")
        return result

    # ------------------------------------------------------------------
    # EDIT EXISTING
    # ------------------------------------------------------------------
    def _generate_edit_existing(
        self, task_text: str, intent: dict, context_str: str
    ) -> dict:
        """
        Le arquivo do disco ANTES de pedir modificacao ao LLM.
        Aplica principio 2 (ler antes de escrever) e 11 (conteudo = dado).
        """
        path_hint = intent.get("target_path_hint", "") or intent.get(
            "filename_hint", ""
        )
        if not path_hint:
            raise ValueError("edit_existing sem path identificavel")

        # Read-before-write delegado ao writer script (executa em sandbox
        # com BASE/Desktop como root quando o path for relativo).
        return {
            "mode": "edit_existing",
            "target_path_hint": path_hint,
            "instruction": task_text,
            "context": context_str,
        }

    # ------------------------------------------------------------------
    # Writer scripts por modo
    # ------------------------------------------------------------------
    def _build_writer_project(
        self,
        folder_name: str,
        files_dict: dict,
        open_browser: bool = False,
        browser_file: str = "",
        run_file: str = "",
        open_vscode: bool = True,
    ) -> str:
        if not isinstance(files_dict, dict):
            raise TypeError(
                f"files_dict deve ser dict, recebido: {type(files_dict).__name__}"
            )

        files_json = json.dumps(files_dict, ensure_ascii=False)

        return f"""
import os
import re
import ast
import json
import sys
import webbrowser
import subprocess

base = os.path.join(r"{BASE}", "Desktop")
folder_name = {folder_name!r}
project_dir = os.path.join(base, folder_name)

# Princípio 1 (verificar antes de destrutivo) + cenario D (colisao de nomes):
# se a pasta ja existe e tem conteudo, NUNCA sobrescreve — usa sufixo.
if os.path.isdir(project_dir):
    try:
        existing = os.listdir(project_dir)
    except OSError:
        existing = []
    if existing:
        i = 2
        while i <= 99:
            candidate = os.path.join(base, f"{{folder_name}}_{{i}}")
            if not os.path.isdir(candidate) or not os.listdir(candidate):
                print(f"AVISO_COLISAO: '{{folder_name}}' ja existia. Usando: {{os.path.basename(candidate)}}")
                project_dir = candidate
                break
            i += 1
        else:
            raise RuntimeError("Nenhum nome livre encontrado para a pasta")

files = json.loads({files_json!r})

if not isinstance(files, dict):
    raise TypeError("files deveria ser dict apos json.loads")

# ── PRE-VALIDACAO (em memoria, antes de gravar nada) ───────────────
# Briefing principio 3 (falha rapida) e 10 (blast radius minimo).
# Se algum .py nao compila, ABORTAMOS antes de poluir o disco com
# codigo quebrado e antes de abrir VS Code num projeto invalido.

py_files = {{p: c for p, c in files.items() if p.endswith(".py")}}
syntax_errors = []
for rel_path, content in py_files.items():
    if not isinstance(content, str) or not content.strip():
        syntax_errors.append((rel_path, "arquivo vazio ou nao-string", 0))
        continue
    try:
        ast.parse(content, filename=rel_path)
    except SyntaxError as e:
        # Detecta truncamento: ultima linha sem fechamento de aspas/chaves
        snippet = content.splitlines()[(e.lineno or 1) - 1] if content.splitlines() else ""
        syntax_errors.append((rel_path, f"{{e.msg}} (linha {{e.lineno}}: {{snippet[:80]!r}})", e.lineno))

# Detecta imports relativos que NAO apontam pra arquivos no dict
# (causa do ModuleNotFoundError em runtime)
all_paths = set(p.replace("\\\\", "/") for p in files.keys())
module_paths = {{p[:-3].replace("/", ".") for p in all_paths if p.endswith(".py")}}
package_paths = set()
for p in module_paths:
    parts = p.split(".")
    for i in range(1, len(parts)):
        package_paths.add(".".join(parts[:i]))

unresolved_imports = []
import_re = re.compile(r"^\\s*(?:from\\s+([\\w.]+)\\s+import|import\\s+([\\w.]+))", re.MULTILINE)
KNOWN_STDLIB = {{
    "os","sys","re","json","ast","subprocess","webbrowser","time","datetime",
    "pathlib","collections","itertools","functools","math","random","sqlite3",
    "typing","dataclasses","enum","logging","argparse","csv","io","traceback",
    "shutil","tempfile","hashlib","uuid","threading","asyncio","unittest",
    "tkinter","customtkinter","ctk","PIL","openpyxl","flask","fastapi","requests",
    "anthropic","playwright","pyautogui","pygetwindow","pywinauto","easyocr",
}}
for rel_path, content in py_files.items():
    if not isinstance(content, str):
        continue
    for m in import_re.finditer(content):
        mod = (m.group(1) or m.group(2) or "").split(".")[0]
        if not mod or mod in KNOWN_STDLIB:
            continue
        full = m.group(1) or m.group(2)
        if full in module_paths or full in package_paths or mod in module_paths or mod in package_paths:
            continue
        # ainda nao bate — possivelmente lib externa nao listada
        unresolved_imports.append((rel_path, full or mod))

if syntax_errors:
    print("ABORT_SYNTAX_ERROR: codigo gerado tem erros — arquivos NAO foram criados")
    for path, msg, line in syntax_errors:
        print(f"  {{path}}: {{msg}}")
    print("Sugestao: re-execute a tarefa (LLM provavelmente truncou o output)")
    sys.exit(2)

if unresolved_imports:
    # Nao aborta — pode ser lib externa nao listada na whitelist. Mas avisa.
    print("AVISO_IMPORT_NAO_RESOLVIDO: possivel ModuleNotFoundError em runtime")
    for path, mod in unresolved_imports[:10]:
        print(f"  {{path}}: import '{{mod}}'")

# ── GRAVACAO (so chega aqui se nao houve erro de sintaxe) ──────────
os.makedirs(project_dir, exist_ok=True)
created = []
for rel_path, content in files.items():
    rel_path = rel_path.replace("\\\\", "/").lstrip("/")
    full_path = os.path.join(project_dir, *rel_path.split("/"))
    parent = os.path.dirname(full_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if "/" in rel_path and rel_path.endswith(".py"):
        pkg_dir = parent
        init_file = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("")

    with open(full_path, "w", encoding="utf-8", newline="\\n") as f:
        f.write(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2))
    created.append(full_path)

print("PASTA:", project_dir)
for p in created:
    print("ARQUIVO:", p)

if {open_vscode!r}:
    try:
        subprocess.Popen(["code", project_dir], shell=True)
    except Exception as e:
        print("VS_CODE_ERRO:", e)

# Para HTML, forca abrir no navegador padrao (e nao no app associado
# a extensao, que em maquinas mal configuradas pode ser bloco de notas)
if {open_browser!r} and {browser_file!r}:
    try:
        target = os.path.join(project_dir, {browser_file!r})
        if target.lower().endswith((".html", ".htm")):
            webbrowser.open("file:///" + target.replace("\\\\", "/"))
        else:
            os.startfile(target)
    except Exception as e:
        print("BROWSER_ERRO:", e)

if {bool(run_file)!r}:
    try:
        target = os.path.join(project_dir, {run_file!r})
        subprocess.Popen(["python", target], cwd=project_dir, shell=True)
    except Exception as e:
        print("PYTHON_RUN_ERRO:", e)
"""

    def _build_writer_single_file(
        self,
        filename: str,
        content: str,
        target_dir: str = "Desktop",
        run_after: bool = False,
        open_vscode: bool = True,
    ) -> str:
        """
        Cria UM arquivo. Detecta colisao e renomeia com sufixo antes de
        sobrescrever (principio 1 e cenario D do briefing).
        """
        content_json = json.dumps(content, ensure_ascii=False)
        return f"""
import os
import ast
import sys
import json
import webbrowser
import subprocess

filename = {filename!r}
target_dir = {target_dir!r}

# Aceita 'Desktop', 'Downloads' como alias, ou path absoluto.
if os.path.isabs(target_dir):
    base_dir = target_dir
else:
    alias_map = {{
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "documentos": os.path.join(os.path.expanduser("~"), "Documents"),
    }}
    base_dir = alias_map.get(target_dir.lower(), os.path.join(os.path.expanduser("~"), "Desktop"))

content = json.loads({content_json!r})

# Pre-validacao: se for .py, garante que compila ANTES de gravar.
if filename.endswith(".py"):
    if not isinstance(content, str) or not content.strip():
        print("ABORT_SYNTAX_ERROR: conteudo vazio")
        sys.exit(2)
    try:
        ast.parse(content, filename=filename)
    except SyntaxError as e:
        print(f"ABORT_SYNTAX_ERROR: {{filename}} linha {{e.lineno}}: {{e.msg}}")
        print("Codigo gerado tem erro de sintaxe — arquivo NAO foi criado")
        sys.exit(2)

os.makedirs(base_dir, exist_ok=True)
full_path = os.path.join(base_dir, filename)

# Princípio 1: nao sobrescrever silenciosamente
if os.path.exists(full_path):
    name, ext = os.path.splitext(filename)
    i = 2
    while i <= 99:
        candidate = os.path.join(base_dir, f"{{name}}_{{i}}{{ext}}")
        if not os.path.exists(candidate):
            print(f"AVISO_COLISAO: '{{filename}}' ja existia. Salvando como: {{os.path.basename(candidate)}}")
            full_path = candidate
            break
        i += 1
    else:
        raise RuntimeError("Nenhum nome livre encontrado para o arquivo")

with open(full_path, "w", encoding="utf-8", newline="\\n") as f:
    f.write(content)

print("ARQUIVO:", full_path)

if {open_vscode!r}:
    try:
        subprocess.Popen(["code", "--reuse-window", full_path], shell=True)
    except Exception as e:
        print("VS_CODE_ERRO:", e)

# HTML solto: abrir no navegador padrao (nao no app associado a extensao)
if full_path.lower().endswith((".html", ".htm")):
    try:
        webbrowser.open("file:///" + full_path.replace("\\\\", "/"))
    except Exception as e:
        print("BROWSER_ERRO:", e)

if {bool(run_after)!r} and full_path.endswith(".py"):
    try:
        subprocess.Popen(["python", full_path], cwd=os.path.dirname(full_path), shell=True)
    except Exception as e:
        print("PYTHON_RUN_ERRO:", e)
"""

    def _build_writer_edit_existing(
        self,
        target_path_hint: str,
        instruction: str,
        open_vscode: bool = True,
    ) -> str:
        """
        Resolve o path, le o arquivo, envia conteudo + instrucao para uma
        chamada Anthropic, escreve a versao nova. Backup .bak antes de
        sobrescrever (blast radius minimo).
        """
        sys_prompt = EDIT_EXISTING_PROMPT.replace('"""', '\\"\\"\\"')
        instruction_json = json.dumps(instruction, ensure_ascii=False)
        sys_prompt_json = json.dumps(sys_prompt, ensure_ascii=False)
        path_json = json.dumps(target_path_hint, ensure_ascii=False)
        model = self.model

        return f"""
import os
import json
import shutil
import subprocess
from anthropic import Anthropic

target_hint = json.loads({path_json!r})
instruction = json.loads({instruction_json!r})

# Resolucao de path: absoluto vence; senao tenta Desktop, depois cwd.
candidates = []
if os.path.isabs(target_hint):
    candidates = [target_hint]
else:
    candidates = [
        os.path.join(os.path.expanduser("~"), "Desktop", target_hint),
        os.path.join(os.getcwd(), target_hint),
    ]
    # busca recursiva na Desktop como ultimo recurso
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    for root, _, files in os.walk(desktop):
        if os.path.basename(target_hint) in files:
            candidates.append(os.path.join(root, os.path.basename(target_hint)))
            break

resolved = None
for c in candidates:
    if os.path.isfile(c):
        resolved = c
        break

if not resolved:
    raise FileNotFoundError(f"Arquivo nao encontrado para edicao: {{target_hint}}")

# Read-before-write
with open(resolved, "r", encoding="utf-8", errors="replace") as f:
    original = f.read()

print(f"LIDO: {{resolved}} ({{len(original)}} chars)")

# Backup .bak (blast radius minimo)
backup_path = resolved + ".bak"
shutil.copy2(resolved, backup_path)
print(f"BACKUP: {{backup_path}}")

# Chama LLM com sys prompt de edicao
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
sys_prompt = json.loads({sys_prompt_json!r})
user_msg = (
    f"PATH: {{resolved}}\\n"
    f"INSTRUCAO: {{instruction}}\\n\\n"
    f"CONTEUDO ATUAL:\\n```\\n{{original}}\\n```\\n\\n"
    "Devolva JSON puro."
)
resp = client.messages.create(
    model={model!r},
    max_tokens=8000,
    system=sys_prompt,
    messages=[{{"role": "user", "content": user_msg}}],
)
raw = resp.content[0].text.strip()
import re
raw = re.sub(r'```json|```', '', raw).strip()
s, e = raw.find('{{'), raw.rfind('}}')
if s == -1 or e == -1:
    raise ValueError("LLM nao retornou JSON valido")
data = json.loads(raw[s:e+1])

if data.get("ambiguity_reason"):
    print(f"AMBIGUIDADE: {{data['ambiguity_reason']}}")
    print("ARQUIVO NAO MODIFICADO. Backup mantido.")
else:
    new_content = data.get("new_content", original)
    with open(resolved, "w", encoding="utf-8", newline="\\n") as f:
        f.write(new_content)
    print(f"GRAVADO: {{resolved}}")
    for ch in data.get("changes", []):
        print(f"MUDANCA: {{ch}}")
    # Validacao pos-edicao para .py — rollback automatico do backup se quebrou
    if resolved.endswith(".py"):
        import py_compile
        try:
            py_compile.compile(resolved, doraise=True)
            print("VALID_PY:", os.path.basename(resolved))
        except py_compile.PyCompileError as syn_err:
            print(f"SYNTAX_ERROR_POS_EDIT: {{syn_err.msg.strip()}}")
            print("ROLLBACK_AUTO: restaurando backup pois nova versao nao compila")
            shutil.copy2(backup_path, resolved)

if {open_vscode!r}:
    try:
        subprocess.Popen(["code", "--reuse-window", resolved], shell=True)
    except Exception as e:
        print("VS_CODE_ERRO:", e)
"""

    def _build_open_folder_script(self, target_path_hint: str) -> str:
        path_json = json.dumps(target_path_hint or "", ensure_ascii=False)
        return f"""
import os
import json
import subprocess

target = json.loads({path_json!r}).strip()

if not target:
    target = os.path.join(os.path.expanduser("~"), "Desktop")
elif not os.path.isabs(target):
    candidate = os.path.join(os.path.expanduser("~"), "Desktop", target)
    if os.path.isdir(candidate):
        target = candidate

if not os.path.isdir(target):
    raise FileNotFoundError(f"Pasta nao encontrada: {{target}}")

print(f"ABRINDO_VSCODE: {{target}}")
subprocess.Popen(["code", target], shell=True)
"""

    # ------------------------------------------------------------------
    # Normalizacao de plano project_full (mantida da v25)
    # ------------------------------------------------------------------
    def _normalize_project(self, plan: dict, brief: dict = None) -> dict:
        if not isinstance(plan, dict):
            raise TypeError("Plano da LLM nao e dict")

        folder = plan.get("folder") or (brief.get("folder") if brief else None) or "projeto_gerado"
        folder = "".join(c if c.isalnum() or c in "_-" else "_" for c in folder)
        folder = folder.strip("_") or "projeto_gerado"

        files = plan.get("files", {})
        if isinstance(files, str):
            files = {plan.get("run_entry") or "main.py": files}
        if not isinstance(files, dict) or not files:
            raise ValueError("Plano nao contem 'files' valido")

        run_entry = plan.get("run_entry") or ""
        browser_entry = plan.get("browser_entry") or ""

        if run_entry and run_entry.endswith(".py"):
            if "README.md" not in files:
                title = (brief.get("title") if brief else folder.replace("_", " ").title())
                tagline = (brief.get("tagline") if brief else "")
                files["README.md"] = (
                    f"# {title}\n\n_{tagline}_\n\n"
                    f"{plan.get('description', 'Projeto gerado pelo AI Farm Agent.')}\n\n"
                    "## Como rodar\n\n"
                    "```bash\n"
                    "pip install -r requirements.txt\n"
                    f"python {run_entry}\n"
                    "```\n"
                )
            if "requirements.txt" not in files:
                files["requirements.txt"] = "customtkinter>=5.2.0\npillow>=10.0.0\n"
            if ".gitignore" not in files:
                files[".gitignore"] = (
                    "__pycache__/\n*.pyc\n*.pyo\n.venv/\nvenv/\n"
                    "*.db\n*.sqlite\n*.sqlite3\n.env\n.idea/\n.vscode/\n.DS_Store\n"
                )

        if browser_entry and "README.md" not in files:
            title = (brief.get("title") if brief else folder.replace("_", " ").title())
            tagline = (brief.get("tagline") if brief else "")
            files["README.md"] = (
                f"# {title}\n\n_{tagline}_\n\n"
                f"Abra `{browser_entry}` no navegador para visualizar.\n"
            )

        return {
            "folder": folder,
            "description": plan.get("description") or (brief.get("title") if brief else "Projeto profissional"),
            "stack": plan.get("stack") or (brief.get("stack") if brief else "python"),
            "theme": plan.get("theme") or (brief.get("palette_name") if brief else "dark"),
            "files": files,
            "run_entry": run_entry,
            "browser_entry": browser_entry,
            "open_in_browser": bool(plan.get("open_in_browser", False)),
            "open_in_vscode": bool(plan.get("open_in_vscode", True)),
        }

    # ------------------------------------------------------------------
    # API publica — roteia por modo
    # ------------------------------------------------------------------
    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)
        ctx_str = ""
        if context:
            ctx_str = "\nCONTEXTO ADICIONAL: " + json.dumps(context, ensure_ascii=False)

        try:
            intent = self._classify_intent(task_text)
            mode = intent.get("mode", "project_full")

            if mode == "open_vscode_folder":
                return self._plan_open_folder(task_text, intent)

            if mode == "single_file":
                return self._plan_single_file(task_text, intent, ctx_str)

            if mode == "edit_existing":
                return self._plan_edit_existing(task_text, intent)

            # project_full / website_simple ambos passam pelo fluxo de projeto
            return self._plan_project(task_text, ctx_str, intent)

        except Exception as e:
            self.logger.error(f"Erro ao gerar plano: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {
                "steps": [],
                "error": str(e),
                "agent": "CODE",
            }

    # ── sub-planners por modo ─────────────────────────────────────────

    def _plan_project(self, task_text: str, ctx_str: str, intent: dict) -> dict:
        # Detecta tech declarada pelo usuario ANTES de chamar o LLM
        tech = _detect_tech_spec(task_text)
        if tech["specified"]:
            tech_note = (
                f"\n\nTECH_REQUERIDA_PELO_USUARIO: {tech['summary']}\n"
                f"O file_structure DEVE conter SOMENTE arquivos com essas "
                f"tecnologias (+ README/requirements/gitignore quando aplicavel). "
                f"NUNCA inclua extensoes fora da lista (.js, .ts, etc) se o "
                f"usuario nao mencionou."
            )
            ctx_str = ctx_str + tech_note
            self.logger.info(f"Tech detectada: {tech['summary']}")

        brief = None
        if self._use_dual_pass:
            self.logger.info("Pass 1/2: gerando DESIGN BRIEF...")
            brief = self._generate_design_brief(task_text, ctx_str)
            self.logger.info(
                f"Brief OK | palette={brief.get('palette_name')} | "
                f"stack={brief.get('stack')} | "
                f"trends={brief.get('visual_trends', [])}"
            )
            self.logger.info("Pass 2/2: gerando CODIGO a partir do brief...")
            plan = self._generate_code_from_brief(task_text, brief)
        else:
            self.logger.info("Single pass mode")
            plan = self._generate_single_pass(task_text, ctx_str)

        project = self._normalize_project(plan, brief)

        # Filtro deterministico pos-LLM: remove arquivos fora da tech declarada
        if tech["specified"]:
            filtered, removed = _filter_files_by_tech(
                project["files"], tech, self.logger
            )
            if removed:
                project["files"] = filtered
                # Se o browser_entry foi removido, recalcula
                if project.get("browser_entry") and project["browser_entry"] not in filtered:
                    project["browser_entry"] = next(
                        (p for p in filtered if p.endswith((".html", ".htm"))),
                        "",
                    )
                # Se o run_entry foi removido, recalcula
                if project.get("run_entry") and project["run_entry"] not in filtered:
                    project["run_entry"] = next(
                        (p for p in filtered if p.endswith(".py")),
                        "",
                    )

        self.logger.info(
            f"Projeto | folder={project['folder']} | "
            f"stack={project['stack']} | "
            f"files={len(project['files'])} | "
            f"theme={project['theme']}"
        )

        writer_code = self._build_writer_project(
            folder_name=project["folder"],
            files_dict=project["files"],
            open_browser=project["open_in_browser"],
            browser_file=project["browser_entry"],
            run_file=project["run_entry"],
            open_vscode=project["open_in_vscode"],
        )

        steps = [
            {
                "step": 1,
                "description": project["description"],
                "action": "run_python",
                "params": {
                    "code": writer_code,
                    "description": project["description"],
                },
                "agent": "CODE",
            },
            {
                "step": 2,
                "description": "Validar arquivos criados",
                "action": "list_files",
                "params": {
                    "path": f"{BASE}/Desktop/{project['folder']}",
                },
                "agent": "CODE",
            },
        ]

        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1

        return {
            "steps": steps,
            "agent": "CODE",
            "mode": intent.get("mode", "project_full"),
            "design_brief": brief,
            "project_manifest": {
                "folder": project["folder"],
                "stack": project["stack"],
                "theme": project["theme"],
                "files": list(project["files"].keys()),
                "description": project["description"],
            },
            "expected_outputs": {"files": True, "text": True},
            "success_criteria": [
                "Arquivos criados fisicamente no disco",
                "Estrutura modular real",
                "Tema visual coerente com o dominio",
                "Pelo menos 2 tendencias visuais 2026 aplicadas",
                "Seed data realista populado",
                "README, requirements e gitignore presentes",
            ],
            "failure_recovery_hint": (
                "Se LLM gerou JSON invalido, tentar single_pass=True. "
                "Se design ficou generico, reforce no contexto a paleta/dominio."
            ),
            "confidence_score": 0.96,
        }

    def _plan_single_file(self, task_text: str, intent: dict, ctx_str: str) -> dict:
        result = self._generate_single_file(task_text, intent, ctx_str)
        filename = result.get("filename") or intent.get("filename_hint") or "arquivo.txt"
        # higieniza filename
        filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        content = result.get("content", "")
        target_dir = result.get("target_dir") or "Desktop"
        run_after = bool(result.get("run_after_create", False))
        open_vscode = bool(result.get("open_in_vscode", True))

        writer = self._build_writer_single_file(
            filename=filename,
            content=content,
            target_dir=target_dir,
            run_after=run_after,
            open_vscode=open_vscode,
        )

        self.logger.info(
            f"SingleFile | filename={filename} | dir={target_dir} | "
            f"len={len(content)} | run_after={run_after}"
        )

        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1

        return {
            "steps": [{
                "step": 1,
                "description": result.get("description") or f"Criar {filename}",
                "action": "run_python",
                "params": {
                    "code": writer,
                    "description": f"Gerar arquivo {filename}",
                },
                "agent": "CODE",
            }],
            "agent": "CODE",
            "mode": "single_file",
            "project_manifest": {
                "files": [filename],
                "description": result.get("description", ""),
            },
            "success_criteria": [
                f"Arquivo {filename} criado",
                "Conteudo do arquivo nao vazio",
                "Sem sobrescrita silenciosa (sufixo aplicado em colisao)",
            ],
            "confidence_score": 0.92,
        }

    def _plan_edit_existing(self, task_text: str, intent: dict) -> dict:
        edit = self._generate_edit_existing(task_text, intent, "")
        writer = self._build_writer_edit_existing(
            target_path_hint=edit["target_path_hint"],
            instruction=edit["instruction"],
            open_vscode=True,
        )

        self.logger.info(
            f"EditExisting | target={edit['target_path_hint']}"
        )

        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1

        return {
            "steps": [{
                "step": 1,
                "description": f"Editar {edit['target_path_hint']}",
                "action": "run_python",
                "params": {
                    "code": writer,
                    "description": "Edit existing file (read-before-write + backup .bak)",
                },
                "agent": "CODE",
            }],
            "agent": "CODE",
            "mode": "edit_existing",
            "success_criteria": [
                "Arquivo original lido antes da modificacao",
                "Backup .bak criado",
                "Arquivo modificado conforme instrucao OU ambiguity_reason reportada",
            ],
            "confidence_score": 0.85,
        }

    def _plan_open_folder(self, task_text: str, intent: dict) -> dict:
        writer = self._build_open_folder_script(intent.get("target_path_hint", ""))
        self.logger.info(
            f"OpenFolder | target={intent.get('target_path_hint','(default Desktop)')}"
        )
        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1
        return {
            "steps": [{
                "step": 1,
                "description": "Abrir pasta no VS Code",
                "action": "run_python",
                "params": {
                    "code": writer,
                    "description": "Abrir VS Code apontando para a pasta solicitada",
                },
                "agent": "CODE",
            }],
            "agent": "CODE",
            "mode": "open_vscode_folder",
            "success_criteria": ["VS Code aberto na pasta indicada"],
            "confidence_score": 0.99,
        }
