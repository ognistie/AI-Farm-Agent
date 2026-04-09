"""
CodeAgent v17 — Migrado para BaseAgent.
Mantém seleção dinâmica de modelo: Sonnet para conteúdo específico, Haiku para genérico.
"""

import os
import getpass
from agents.base_agent import BaseAgent
from core.config import get_config

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"

SYSTEM_PROMPT = (
    "Gere codigo Python que cria um projeto de arquivos.\n"
    "O codigo DEVE:\n"
    "1. import os, subprocess\n"
    "2. Criar pasta no Desktop com os.makedirs\n"
    "3. Criar CADA arquivo em arquivo SEPARADO (html separado de css)\n"
    "4. O HTML deve usar <link rel='stylesheet' href='style.css'> (NAO css inline)\n"
    "5. O CONTEUDO deve ser EXATAMENTE sobre o tema que o usuario pediu\n"
    "6. Abrir no VS Code: subprocess.Popen(['code', pasta])\n"
    "7. Se site: abrir browser: subprocess.Popen(f'start \"\" \"{path}\"', shell=True)\n"
    "8. print() resultado\n\n"
    "PROIBIDO:\n"
    "- Texto generico como 'Bem-vindo', 'Meu Site', 'Conteudo Principal'\n"
    "- CSS dentro do HTML (deve ser arquivo separado)\n"
    "- Ignorar o tema/titulo/conteudo que o usuario pediu\n\n"
    '{"steps":[{"step":1,"description":"...","code":"codigo python completo"}]}'
)

# Indicadores de conteúdo específico que requerem Sonnet
_SONNET_INDICATORS = [
    "titulo", "title", "github.com", "desenvolvido por", "apresentacao",
    "sobre o", "about", "seções", "sections", "secoes",
    "conteudo", "content", "texto", "escreva", "coloque",
    "nome", "link", "url", "http", "logo",
]


def _needs_sonnet(task):
    """Detecta se a tarefa precisa de conteúdo específico (Sonnet) ou genérico (Haiku)."""
    t = str(task).lower()
    return any(ind in t for ind in _SONNET_INDICATORS)


class CodeAgent(BaseAgent):
    """Agente especialista em criação de código e projetos."""

    def __init__(self):
        super().__init__(name="CODE", system_prompt=SYSTEM_PROMPT)
        self._config = get_config()

    def plan(self, task, context=None):
        """Gera plano com seleção dinâmica de modelo."""
        task_text = self._extract_task_text(task)

        # Escolhe modelo baseado na complexidade do conteúdo
        use_sonnet = _needs_sonnet(task_text)
        if use_sonnet:
            model = self._config.get("models.strong")
            self.logger.info("Usando Sonnet (conteúdo específico)")
        else:
            model = self._config.get("models.fast")
            self.logger.info("Usando Haiku (estrutura simples)")

        message = (
            "TAREFA (siga EXATAMENTE o que esta escrito, palavra por palavra):\n"
            + task_text + "\n\n"
            "CHECKLIST antes de gerar o codigo:\n"
            "- O titulo/nome do site e EXATAMENTE o que foi pedido? (nao 'Meu Site')\n"
            "- O conteudo fala sobre o TEMA pedido? (nao generico)\n"
            "- Se pediu link do GitHub, o link APARECE no site?\n"
            "- Se pediu secoes especificas, TODAS estao no HTML?\n"
            "- HTML e CSS estao em ARQUIVOS SEPARADOS?\n"
            "- O <link> para style.css esta no <head>?\n\n"
            "Gere JSON puro com codigo Python completo."
        )

        try:
            raw = self._client.message(
                model=model,
                system=self.system_prompt,
                user_content=message,
                max_tokens=8000,
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

            self.logger.info(f"Plano: {len(steps)} steps (model={model.split('-')[1]})")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": steps, "agent": "CODE"}

        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "CODE"}