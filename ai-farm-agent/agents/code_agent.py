"""
CodeAgent v18 — volta para a logica simples do v17 com guard-rails minimos.

POR QUE VOLTAMOS:
v17 funcionava bem: o LLM gera UM script Python que escreve os arquivos.
v25/v26 introduziram dual-pass + files-dict + DESIGN_BIBLE de 200 linhas
que constrangeu o LLM a devolver fragmentos truncados ('/* placeholder */',
sistemas Python virando 1 arquivo, etc). Voltamos a confianca v17.

GUARD-RAILS QUE FICARAM:
- Regras explicitas no SYSTEM_PROMPT contra os 3 bugs reportados:
  * CSS vazio / placeholder
  * Sistema profissional virando 1 arquivo
  * .js criado sem ser pedido / .css/.js inline quando deveria ser separado
- Webbrowser.open() em vez de os.startfile (evita notepad como handler de .html)
- Colisao de nomes resolve com sufixo _2, _3 (briefing seccao 5 — blast radius)

OUTROS AGENTES NAO PRECISAM MUDAR — Maestro, Web, Data, File etc continuam
com as evolucoes do briefing (ambiguity gate, circuit breaker, etc).
"""

import getpass
from agents.base_agent import BaseAgent
from core.config import get_config

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


SYSTEM_PROMPT = (
    "Voce e ENGENHEIRO + DESIGNER SENIOR. Sua tarefa: gerar UM script Python\n"
    "que cria um projeto de arquivos no disco. O script roda EM run_python.\n\n"

    "═══ O SCRIPT QUE VOCE GERA DEVE ═══\n"
    "1. import os, subprocess, webbrowser\n"
    "2. base = os.path.join(os.path.expanduser('~'), 'Desktop')\n"
    "3. project_dir = os.path.join(base, '<nome_projeto_snake_case>')\n"
    "4. COLISAO: se project_dir existe e tem conteudo, anexar sufixo _2/_3...\n"
    "5. os.makedirs(project_dir, exist_ok=True)\n"
    "6. Para CADA arquivo do projeto, criar pasta-pai se necessario e gravar\n"
    "   com open(..., 'w', encoding='utf-8') e f.write(conteudo_completo)\n"
    "7. subprocess.Popen(['code', project_dir], shell=True)  # abre VS Code\n"
    "8. Se houver index.html, abrir no NAVEGADOR (NUNCA notepad):\n"
    "     webbrowser.open('file:///' + index_path.replace('\\\\', '/'))\n"
    "   NUNCA use os.startfile para .html — em algumas maquinas abre Notepad.\n"
    "9. print() resultado: 'PASTA: ...' e 'ARQUIVO: ...' por arquivo criado.\n\n"

    "═══ CONTEUDO DOS ARQUIVOS — REGRAS ABSOLUTAS ═══\n\n"

    "REGRA 1: ZERO PLACEHOLDER\n"
    "  PROIBIDO escrever arquivos com:\n"
    "  - '/* Styles CSS placeholder */' ou similar (CSS DEVE ter codigo real)\n"
    "  - '// TODO', '...', 'pass # implementar', 'continuar aqui'\n"
    "  - Lorem ipsum / texto generico tipo 'Conteudo aqui'\n"
    "  - Arquivo CSS com menos de 80 linhas de regras reais\n"
    "  Se voce nao tem 'espaco' pra escrever o conteudo, ESCOLHA gerar\n"
    "  MENOS arquivos mas com conteudo COMPLETO em cada um.\n\n"

    "REGRA 2: RESPEITE A TECH QUE O USUARIO PEDIU\n"
    "  Leia a tarefa LITERALMENTE. Se ele disse:\n"
    "  - 'em HTML e CSS' / 'HTML, CSS' / 'HTML + CSS':\n"
    "      Crie EXATAMENTE: index.html + style.css (+ README opcional).\n"
    "      PROIBIDO criar script.js ou qualquer .js.\n"
    "      O <head> do HTML referencia style.css com <link rel='stylesheet'>.\n"
    "  - 'HTML, CSS e JS' / 'HTML, CSS, JavaScript':\n"
    "      Pode criar script.js, com interatividade real.\n"
    "  - 'apenas HTML' / 'so HTML' / 'HTML simples':\n"
    "      UM arquivo index.html com CSS no <style> e JS no <script>.\n"
    "      NAO crie .css nem .js separados.\n"
    "  - 'sistema em python' / 'app em python' / 'plataforma em python':\n"
    "      OBRIGATORIO multi-arquivo. Minimo 6 arquivos:\n"
    "        main.py, config.py, database/connection.py, database/models.py,\n"
    "        ui/main_window.py, ui/components.py, ui/theme.py,\n"
    "        utils.py, requirements.txt, README.md, .gitignore\n"
    "      PROIBIDO entregar apenas main.py para sistema profissional.\n"
    "  - 'flask' / 'fastapi' / 'django':\n"
    "      app.py + templates/*.html + static/*.css + models.py + requirements.txt\n\n"

    "REGRA 3: CONTEUDO EXATAMENTE SOBRE O TEMA\n"
    "  Se usuario disse 'site sobre buda', o site fala SOBRE BUDA — historia,\n"
    "  ensinamentos, citacoes reais. NUNCA 'Bem-vindo ao meu site' ou 'Lorem'.\n"
    "  Se disse 'sistema dentista', as entidades sao Paciente, Consulta,\n"
    "  Dentista — nao 'User', 'Item'.\n\n"

    "REGRA 4: DESIGN MODERNO (sites)\n"
    "  CSS DEVE ter:\n"
    "  - @import url('https://fonts.googleapis.com/css2?family=Inter:...') ou similar\n"
    "    (Inter / Playfair Display / Outfit / Cinzel / Cormorant — escolha 1-2)\n"
    "  - Variaveis :root com 6-10 cores (bg, surface, text, accent, etc)\n"
    "  - Layout responsivo com clamp(), grid, flex\n"
    "  - transitions em hover (transition: all 0.3s cubic-bezier(...))\n"
    "  - border-radius 12-24px em cards/botoes\n"
    "  - sombras com cor do accent (nao preto puro)\n"
    "  Sistemas Python DESKTOP: SEMPRE CustomTkinter (ctk), nunca Tkinter puro.\n\n"

    "REGRA 5: CODIGO QUE RODA NA PRIMEIRA TENTATIVA\n"
    "  - Python: imports validos, type hints quando ajudar, if __name__\n"
    "  - HTML: doctype + meta charset + meta viewport + lang='pt-BR'\n"
    "  - JS (so se pedido): vanilla ES6+, sem dependencias externas\n"
    "  - Toda aspas/parenteses/chave aberta DEVE fechar. NUNCA truncar.\n\n"

    "═══ PROIBIDO (NUNCA FACA) ═══\n"
    "- CSS inline quando user nao disse 'apenas HTML'\n"
    "- os.startfile() para abrir HTML (use webbrowser.open)\n"
    "- Sobrescrever pasta existente sem sufixo\n"
    "- Texto generico tipo 'Bem-vindo' / 'Meu Site' / 'Conteudo Principal'\n"
    "- Mais arquivos que o necessario quando user pediu poucas tecnologias\n"
    "- Menos arquivos que o necessario quando user pediu 'sistema profissional'\n\n"

    "═══ FORMATO DA RESPOSTA ═══\n"
    "JSON puro (sem markdown, sem ```), no formato:\n"
    '{"steps":[{"step":1,"description":"<1 linha>","code":"<script python completo>"}]}\n\n'

    "O <script python completo> e o codigo que cria TUDO no disco.\n"
    "Use \\n para quebras de linha. Escape aspas internas com \\\".\n"
)


# Modelo: Sonnet para conteudo especifico (sistemas/sites grandes com tema real),
# Haiku para tarefas mais genericas/curtas.
_SONNET_INDICATORS = [
    "titulo", "title", "github.com", "desenvolvido por", "apresentacao",
    "sobre o", "about", "secoes", "sections", "sistema", "dashboard", "app",
    "conteudo", "content", "texto", "escreva", "coloque",
    "nome", "link", "url", "http", "logo", "completo", "profissional",
    "plataforma", "gerenciador", "controle", "agendamento",
]


def _needs_sonnet(task):
    """Detecta se a tarefa precisa de Sonnet (conteudo rico) ou Haiku (simples)."""
    t = str(task).lower()
    return any(ind in t for ind in _SONNET_INDICATORS)


class CodeAgent(BaseAgent):
    """
    Agente especialista em codigo. v18 = v17 (logica simples) + guard-rails.

    Fluxo:
      1. Recebe task (str ou dict).
      2. Escolhe modelo (Sonnet para sistemas grandes, Haiku para tarefas curtas).
      3. Envia SYSTEM_PROMPT + task para o LLM.
      4. LLM responde com {steps:[{code: <script python>}]}.
      5. Empacota como step run_python — orquestrador roda o script no Python local.

    NAO HA writer-script proprio: o LLM e quem decide a estrutura do projeto.
    Isso evita a constrangedora gaiola do v25/v26 que truncava em placeholder.
    """

    def __init__(self):
        super().__init__(name="CODE", system_prompt=SYSTEM_PROMPT)
        self._config = get_config()

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)

        use_sonnet = _needs_sonnet(task_text)
        if use_sonnet:
            model = self._config.get("models.strong")
            self.logger.info("Usando Sonnet (conteudo rico)")
        else:
            model = self._config.get("models.fast")
            self.logger.info("Usando Haiku (tarefa simples)")

        message = (
            "TAREFA (siga EXATAMENTE o que esta escrito, palavra por palavra):\n"
            + task_text + "\n\n"

            "CHECKLIST antes de gerar o codigo:\n"
            "- A tarefa pediu 'apenas HTML' / 'HTML + CSS' / 'HTML + CSS + JS' /\n"
            "  'sistema python' / 'flask' / outro? Estou criando EXATAMENTE essas\n"
            "  extensoes (nada de .js se nao foi pedido)?\n"
            "- Cada arquivo CSS tem 80+ linhas de codigo REAL (sem placeholder)?\n"
            "- Se for sistema profissional em Python, estou criando 6+ arquivos\n"
            "  em pasta organizada (database/, ui/, etc) e nao apenas main.py?\n"
            "- O CONTEUDO fala sobre o TEMA pedido (nao 'Bem-vindo', 'Meu Site')?\n"
            "- HTML usa <link rel='stylesheet' href='style.css'> (separado)?\n"
            "  Exceto se user disse 'apenas HTML' (entao inline).\n"
            "- Estou usando webbrowser.open() para abrir HTML (NUNCA os.startfile)?\n"
            "- A pasta de projeto tem nome em snake_case relevante ao tema?\n"
            "- Se a pasta ja existir com conteudo, vou anexar sufixo _2 / _3?\n\n"

            "Gere JSON puro com codigo Python COMPLETO."
        )

        try:
            raw = self._client.message(
                model=model,
                system=self.system_prompt,
                user_content=message,
                max_tokens=10000,
            )
            from core.json_validator import safe_parse
            plan = safe_parse(raw, model)

            steps = []
            for st in plan.get("steps", []):
                code = st.get("code", "")
                code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
                steps.append({
                    "step": st.get("step", 1),
                    "description": st.get("description", ""),
                    "action": "run_python",
                    "params": {"code": code, "description": st.get("description", "")},
                    "agent": "CODE",
                })

            model_tag = model.split("-")[1] if "-" in model else model
            self.logger.info(f"Plano: {len(steps)} steps (model={model_tag})")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": steps, "agent": "CODE"}

        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "CODE"}
