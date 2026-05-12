"""
CodeAgent v25 — Engenheiro Senior + Designer Senior via LLM.

MUDANCAS v25 (vs v24):
- DESIGN BIBLE injetado no prompt: paletas reais, padroes visuais 2026
- DUAL PASS opcional: 1) gera spec de design + arquitetura, 2) gera codigo
  Isso forca a LLM a PENSAR no design ANTES de codar.
- Exemplos CONCRETOS de codigo feio vs codigo bonito (HTML+CSS e CTk)
- Catalogo de paletas de cores reais por dominio (10+ paletas testadas)
- Catalogo de tipografias (Google Fonts) por contexto
- Padroes de layout 2026: Bento Grid, Glassmorphism, Kinetic Type, Dark Mode
- Micro-interacoes obrigatorias (hover, transitions, animacoes)
- Reducao de max_tokens em pass 1 (planning) e expansao em pass 2 (code)
- Mantem 100% compatibilidade com BaseAgent, Maestro, etc.

Fluxo:
1. Pass 1 (DESIGN): LLM cria DESIGN_BRIEF detalhado (paleta, layout, componentes)
2. Pass 2 (CODE):  LLM recebe o DESIGN_BRIEF + tarefa e gera o codigo final
3. Convertemos em steps run_python que escrevem em disco
"""

import json
import getpass

from agents.base_agent import BaseAgent
from core.config import get_config
from core.json_validator import safe_parse

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


# ═══════════════════════════════════════════════════════════════════════
# DESIGN BIBLE — referencia visual injetada nos prompts
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
   - Cards de tamanhos VARIADOS em CSS Grid
   - Cantos arredondados generosos: border-radius: 24px
   - Espacamento generoso entre cards: gap: 1.5rem
   - Cada card como auto-contido com seu proprio "mini-conteudo"
   - Exemplo CSS Grid: grid-template-columns: repeat(12, 1fr);
     onde os cards usam grid-column: span 4/6/8/12 conforme prioridade

2. GLASSMORPHISM (UI moments — overlays, cards, navs):
   background: rgba(255, 255, 255, 0.06);
   backdrop-filter: blur(20px) saturate(180%);
   border: 1px solid rgba(255, 255, 255, 0.1);
   box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);

3. KINETIC TYPOGRAPHY (heroes que impactam):
   - Texto hero EXAGERADO (clamp 5rem-12vw)
   - Animacoes de letras entrando (transform translateY)
   - Gradiente em texto: background-clip: text
   - Cursor magnetico ou hover scale

4. SOFT SHADOWS COLORIDAS (ao inves de preto puro):
   box-shadow: 0 20px 50px -12px rgba(99, 102, 241, 0.25);
   (sombra com a cor do accent, nao preto)

5. MICRO-INTERACOES (NUNCA esqueca):
   - transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   - hover: transform: translateY(-4px); scale(1.02);
   - botoes com ripple ou glow
   - cards que "levantam" no hover

6. SCROLL REVEAL (em sites):
   - IntersectionObserver em JS
   - Elementos comecam com opacity:0 translateY(40px)
   - Animam para opacity:1 translateY(0) ao entrar viewport

7. GRADIENT MESHES / AURORA (backgrounds modernos):
   background: radial-gradient(at 0% 0%, #6366f1 0%, transparent 50%),
               radial-gradient(at 100% 100%, #ec4899 0%, transparent 50%),
               #0a0e1a;

═══ ANTI-PADROES (NUNCA FACA) ═══

❌ Tkinter padrao cinza/branco com ttk default
❌ HTML sem fontes customizadas (Times New Roman / Arial padrao)
❌ Botoes quadrados sem border-radius
❌ Sombras pretas duras (0 2px 5px black)
❌ Layouts flexbox de 1 coluna em pagina inteira
❌ Cores #FFFFFF puro em backgrounds (use #fafaf7 ou similar)
❌ Cores #000000 puro em texto dark (use #18181b ou #0f172a)
❌ Espacamento apertado (padding < 1rem em cards)
❌ Sem hover states em elementos clicaveis
❌ Sem dados de exemplo / sem estado vazio bonito
❌ Texto centralizado em paragrafos longos
❌ Fontes < 16px em corpo de texto
❌ Mais de 3 cores de accent na mesma tela

═══ EXEMPLO 1: SITE HERO (HTML + CSS) ═══

❌ FEIO (nao faca):
<div class="hero">
  <h1>Bem vindo</h1>
  <p>Lorem ipsum</p>
  <button>Clique</button>
</div>
.hero { background: gray; padding: 20px; text-align: center; }

✅ BONITO (faca assim):
<section class="hero">
  <div class="hero__bg-mesh"></div>
  <div class="hero__container">
    <span class="hero__kicker">PRODUTO 2026</span>
    <h1 class="hero__title">
      O futuro do
      <span class="hero__title--gradient">agendamento</span>
      comeca aqui
    </h1>
    <p class="hero__subtitle">
      Plataforma completa que transforma o caos em fluxo natural.
    </p>
    <div class="hero__cta-group">
      <a href="#" class="btn btn--primary">Comecar agora →</a>
      <a href="#" class="btn btn--ghost">Ver demo</a>
    </div>
  </div>
</section>

CSS correspondente (resumo):
.hero {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #0a0e1a;
  overflow: hidden;
}
.hero__bg-mesh {
  position: absolute; inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(99,102,241,0.25) 0%, transparent 40%),
    radial-gradient(circle at 80% 80%, rgba(236,72,153,0.20) 0%, transparent 40%);
  filter: blur(40px);
}
.hero__title {
  font-family: 'Inter', sans-serif;
  font-size: clamp(3rem, 8vw, 7rem);
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.04em;
  color: #e6edf3;
}
.hero__title--gradient {
  background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.btn--primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 30px -8px rgba(99,102,241,0.5);
}
.btn--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -8px rgba(99,102,241,0.6);
}

═══ EXEMPLO 2: CARD CUSTOMTKINTER ═══

❌ FEIO (nao faca):
frame = ctk.CTkFrame(root)
label = ctk.CTkLabel(frame, text="Cliente: Joao")
label.pack()
btn = ctk.CTkButton(frame, text="Ver")
btn.pack()

✅ BONITO (faca assim):
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, subtitle, accent="#6366f1"):
        super().__init__(
            parent,
            fg_color="#131826",
            corner_radius=16,
            border_width=1,
            border_color="#252e48",
        )
        # Linha de accent no topo
        accent_bar = ctk.CTkFrame(self, fg_color=accent, height=3, corner_radius=2)
        accent_bar.pack(fill="x", padx=20, pady=(20, 0))

        # Titulo pequeno em cima
        ctk.CTkLabel(
            self, text=title.upper(),
            font=("Inter", 11, "bold"),
            text_color="#8b95a8",
        ).pack(anchor="w", padx=20, pady=(16, 4))

        # Valor grande destacado
        ctk.CTkLabel(
            self, text=value,
            font=("Inter", 32, "bold"),
            text_color="#e6edf3",
        ).pack(anchor="w", padx=20)

        # Subtitulo discreto
        ctk.CTkLabel(
            self, text=subtitle,
            font=("Inter", 12),
            text_color="#10b981",  # verde para indicar crescimento
        ).pack(anchor="w", padx=20, pady=(0, 20))

═══ ESTRUTURA DE LAYOUT POR TIPO DE APP ═══

DESKTOP DASHBOARD (CustomTkinter):
  +-------------------------------------------------------+
  |  [LOGO]   Sidebar    |    HEADER (titulo + acoes)     |
  |  ─────────────       |    ────────────────────────    |
  |  ▣ Dashboard         |  +--------+ +--------+ +-----+ |
  |  ◉ Reservas          |  | KPI    | | KPI    | | KPI | |
  |  ○ Computadores      |  +--------+ +--------+ +-----+ |
  |  ○ Usuarios          |  +--------------+ +-----------+|
  |  ○ Relatorios        |  | Grafico      | | Lista     ||
  |                      |  +--------------+ +-----------+|
  |  [Configuracoes]     |  +-----------------------------+|
  |  [Sair]              |  | Tabela com filtros          ||
  +-------------------------------------------------------+

  Sidebar: 240px width, dark, com icones + texto
  Header: 70px height, com breadcrumb / titulo + busca + avatar
  Main: scroll vertical com cards/graficos em grid

LANDING PAGE (HTML/CSS/JS):
  - Nav fixo translucido (glassmorphism)
  - Hero full-height com mesh gradient + CTA dual
  - Bento grid de features (6-8 cards de tamanhos variados)
  - Secao "Como funciona" com timeline ou steps
  - Social proof (logos / numeros / depoimentos)
  - CTA final em destaque
  - Footer minimal

═══ DADOS DE EXEMPLO (SEED) — SEMPRE INCLUA ═══

Sistemas vazios sao tristes. SEMPRE popule com 5-15 registros realistas:
- Sistema de biblioteca: 10 livros de verdade (1984, Dom Casmurro, etc)
- Sistema de vendas: 8 produtos com precos plausiveis
- Sistema de agendamento: 6 reservas distribuidas na semana
- CRM: 5 clientes com nomes e empresas brasileiras
- Site historico: conteudo REAL sobre o tema

═══ ICONS / EMOJI ═══
Use emoji unicode em UIs desktop quando nao tiver biblioteca de icones:
  ▣ ◉ ○ ▤ ⚙ ✓ ✗ → ← ↑ ↓ ★ ♥ ⚡ 🔍 📊 📅 👤 ⚠
Em web, use Lucide via CDN ou Heroicons inline SVG.

═══════════════════════════════════════════════════════════════════════
FIM DA DESIGN BIBLE — APLIQUE TUDO ISSO COM CRITERIO
═══════════════════════════════════════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════════════
# PROMPT PASS 1 — DESIGN PLANNING
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
    '  "palette": {\n'
    '    "bg_base": "#xxxxxx",\n'
    '    "bg_surface": "#xxxxxx",\n'
    '    "bg_elevated": "#xxxxxx",\n'
    '    "border": "#xxxxxx",\n'
    '    "text": "#xxxxxx",\n'
    '    "text_muted": "#xxxxxx",\n'
    '    "accent": "#xxxxxx",\n'
    '    "accent_2": "#xxxxxx",\n'
    '    "success": "#xxxxxx",\n'
    '    "danger": "#xxxxxx"\n'
    "  },\n"
    '  "typography": {\n'
    '    "display_font": "ex: Inter, Playfair Display",\n'
    '    "body_font": "ex: Inter",\n'
    '    "mono_font": "JetBrains Mono"\n'
    "  },\n"
    '  "visual_trends": ["bento_grid", "glassmorphism", "kinetic_type", "soft_shadows", "scroll_reveal"],\n'
    '  "entities": [\n'
    '    {"name": "Computador", "fields": ["id", "nome", "specs", "sala", "status"]},\n'
    '    {"name": "Reserva",    "fields": ["id", "computador_id", "usuario", "inicio", "fim"]}\n'
    "  ],\n"
    '  "screens_or_sections": [\n'
    '    {"name": "Dashboard", "purpose": "Visao geral com KPIs e calendario"},\n'
    '    {"name": "Reservas",  "purpose": "CRUD com calendario visual"}\n'
    "  ],\n"
    '  "key_features": [\n'
    '    "Calendario visual semanal com slots",\n'
    '    "Validacao de conflitos em tempo real",\n'
    '    "Dashboard com graficos matplotlib"\n'
    "  ],\n"
    '  "seed_data_plan": "Descrever que dados de exemplo populare (5-15 registros realistas)",\n'
    '  "file_structure": ["main.py", "config.py", "database/connection.py", "ui/main_window.py", "..."],\n'
    '  "open_in_browser": false,\n'
    '  "browser_entry": null,\n'
    '  "run_entry": "main.py"\n'
    "}\n\n"

    "REGRAS:\n"
    "- Escolha palette do catalogo da DESIGN BIBLE (use os hex EXATOS)\n"
    "- Para sistemas: project_type='desktop_app', stack inclui 'customtkinter'\n"
    "- Para sites: project_type='web_site', stack='html+css+js', open_in_browser=true\n"
    "- Para web apps: project_type='web_app', stack='flask+sqlite'\n"
    "- file_structure deve ter 5-15 arquivos com paths reais\n"
    "- Pelo menos 2 visual_trends por projeto\n"
    "- JSON PURO. Sem ``` sem markdown sem texto antes/depois.\n"
)


# ═══════════════════════════════════════════════════════════════════════
# PROMPT PASS 2 — CODE GENERATION (com brief em mao)
# ═══════════════════════════════════════════════════════════════════════
CODE_BUILDER_PROMPT = (
    "Voce e um ENGENHEIRO SENIOR + DESIGNER que executa o BRIEF entregue.\n"
    "Seu codigo e bonito, modular, e RODA na primeira tentativa.\n\n"

    + DESIGN_BIBLE +

    "\n\n═══ COMO USAR O BRIEF ═══\n"
    "Voce recebera um JSON DESIGN_BRIEF. Use TODOS os valores dele:\n"
    "- palette: hex codes EXATOS no codigo (nada de 'similar')\n"
    "- typography: importe Google Fonts via @import url(...) ou <link>\n"
    "- visual_trends: implemente CADA tendencia listada\n"
    "- entities: vire schema SQLite + classes Python\n"
    "- seed_data_plan: popule no primeiro run\n"
    "- file_structure: gere TODOS os arquivos listados\n\n"

    "═══ REGRAS DE CODIGO ═══\n"
    "- HTML: semantica (header, nav, main, section, article, footer)\n"
    "- CSS: variaveis CSS no :root com TODA a paleta do brief\n"
    "- CSS: clamp() para responsivo, grid/flex modernos, transitions em tudo\n"
    "- JS: vanilla ES6+, IntersectionObserver para scroll reveal\n"
    "- Python: type hints, dataclasses, context managers para DB\n"
    "- CTk: classes customizadas para cards/sidebar/header (nao widgets soltos)\n"
    "- CTk: cores do brief via dicionario THEME importado de config.py\n"
    "- SEMPRE README.md (com features, screenshot ASCII opcional, como rodar)\n"
    "- SEMPRE requirements.txt com versoes\n"
    "- SEMPRE .gitignore\n"
    "- SEMPRE seed data executado no primeiro start (verifique se DB vazio)\n\n"

    "═══ FORMATO DE RESPOSTA — JSON PURO ═══\n"
    "{\n"
    '  "folder": "<copia do brief>",\n'
    '  "description": "Sistema X com Y para Z",\n'
    '  "stack": "<copia do brief>",\n'
    '  "theme": "<palette_name do brief>",\n'
    '  "files": {\n'
    '    "main.py": "<codigo COMPLETO>",\n'
    '    "config.py": "<codigo>",\n'
    '    "database/connection.py": "<codigo>",\n'
    '    "ui/main_window.py": "<codigo>",\n'
    '    "ui/components.py": "<codigo>",\n'
    '    "ui/theme.py": "<codigo com cores do brief>",\n'
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


# Fallback single-pass (caso o budget seja apertado)
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


class CodeAgent(BaseAgent):
    """
    CodeAgent v25 — Engenheiro + Designer Senior.

    Estrategia DUAL PASS por padrao:
      1. Brief de design (rapido, ~2k tokens)
      2. Codigo final (extenso, ate 12k tokens)

    Cai para SINGLE PASS se a config indicar ou se o budget for limitado.
    """

    def __init__(self):
        super().__init__(name="CODE", system_prompt=DESIGN_PLANNER_PROMPT)
        self._config = get_config()
        # Permite desabilitar dual pass via config se quiser economizar tokens
        self._use_dual_pass = self._config.get("agents.code.dual_pass", True)

    # ------------------------------------------------------------------
    # PASS 1 — Design Brief
    # ------------------------------------------------------------------
    def _generate_design_brief(self, task_text: str, context_str: str) -> dict:
        """LLM produz brief de design ANTES de gerar codigo."""
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

    # ------------------------------------------------------------------
    # PASS 2 — Code Generation com Brief
    # ------------------------------------------------------------------
    def _generate_code_from_brief(self, task_text: str, brief: dict) -> dict:
        """LLM gera codigo final usando o brief como guia rigido."""
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

    # ------------------------------------------------------------------
    # SINGLE PASS (fallback)
    # ------------------------------------------------------------------
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
    # Writer script (mesmo da v24, robusto)
    # ------------------------------------------------------------------
    def _build_writer_script(
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
import json
import subprocess

base = os.path.join(r"{BASE}", "Desktop")
project_dir = os.path.join(base, {folder_name!r})
os.makedirs(project_dir, exist_ok=True)

files = json.loads({files_json!r})

if not isinstance(files, dict):
    raise TypeError("files deveria ser dict apos json.loads")

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

if {open_browser!r} and {browser_file!r}:
    try:
        target = os.path.join(project_dir, {browser_file!r})
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

    # ------------------------------------------------------------------
    # Normalizacao
    # ------------------------------------------------------------------
    def _normalize_plan(self, plan: dict, brief: dict = None) -> dict:
        if not isinstance(plan, dict):
            raise TypeError("Plano da LLM nao e dict")

        # Pega folder/description do brief se faltar no plano
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

        # Auto-add README/requirements/gitignore para Python
        if run_entry and run_entry.endswith(".py"):
            if "README.md" not in files:
                title = (brief.get("title") if brief else folder.replace("_", " ").title())
                tagline = (brief.get("tagline") if brief else "")
                files["README.md"] = (
                    f"# {title}\n\n"
                    f"_{tagline}_\n\n"
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

        # Auto-add README para sites
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
    # API publica
    # ------------------------------------------------------------------
    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)
        ctx_str = ""
        if context:
            ctx_str = "\nCONTEXTO ADICIONAL: " + json.dumps(context, ensure_ascii=False)

        try:
            brief = None
            if self._use_dual_pass:
                # PASS 1: Design brief
                self.logger.info("Pass 1/2: gerando DESIGN BRIEF...")
                brief = self._generate_design_brief(task_text, ctx_str)
                self.logger.info(
                    f"Brief OK | palette={brief.get('palette_name')} | "
                    f"stack={brief.get('stack')} | "
                    f"trends={brief.get('visual_trends', [])}"
                )

                # PASS 2: Codigo
                self.logger.info("Pass 2/2: gerando CODIGO a partir do brief...")
                plan = self._generate_code_from_brief(task_text, brief)
            else:
                self.logger.info("Single pass mode")
                plan = self._generate_single_pass(task_text, ctx_str)

            project = self._normalize_plan(plan, brief)

            self.logger.info(
                f"Projeto | folder={project['folder']} | "
                f"stack={project['stack']} | "
                f"files={len(project['files'])} | "
                f"theme={project['theme']}"
            )

            writer_code = self._build_writer_script(
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

        except Exception as e:
            self.logger.error(f"Erro ao gerar plano: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {
                "steps": [],
                "error": str(e),
                "agent": "CODE",
            }