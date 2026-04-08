"""
CodeAgent v16 — Sonnet para conteudo especifico, Haiku para generico.
O Haiku ignora conteudo da tarefa. O Sonnet segue instrucoes.
"""

import json, os, getpass
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
USERNAME = getpass.getuser()
BASE = "C:/Users/" + USERNAME

SYSTEM = (
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


def _needs_sonnet(task):
    """Detecta se a tarefa precisa de conteudo especifico (Sonnet) ou generico (Haiku)."""
    t = str(task).lower()
    # Se menciona conteudo especifico, titulos, nomes, links → Sonnet
    indicators = [
        "titulo", "title", "github.com", "desenvolvido por", "apresentacao",
        "sobre o", "about", "seções", "sections", "secoes",
        "conteudo", "content", "texto", "escreva", "coloque",
        "nome", "link", "url", "http", "logo"
    ]
    for ind in indicators:
        if ind in t:
            return True
    return False


class CodeAgent:
    def __init__(self):
        self.name = "CODE"

    def plan(self, task, context=None):
        # Escolhe modelo baseado na complexidade do conteudo
        use_sonnet = _needs_sonnet(task)
        model = "claude-sonnet-4-20250514" if use_sonnet else "claude-haiku-4-5-20251001"

        if use_sonnet:
            print("  [CODE] Usando Sonnet (conteudo especifico)")
        else:
            print("  [CODE] Usando Haiku (estrutura simples)")

        message = (
            "TAREFA (siga EXATAMENTE o que esta escrito, palavra por palavra):\n"
            + str(task) + "\n\n"
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
            resp = client.messages.create(model=model, max_tokens=8000, system=SYSTEM,
                messages=[{"role": "user", "content": message}])
            raw = resp.content[0].text.strip()
            plan = safe_parse(raw, model)
            steps = []
            for st in plan.get("steps", []):
                code = st.get("code", "")
                code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
                steps.append({
                    "step": st.get("step", 1),
                    "description": st.get("description", ""),
                    "action": "run_python",
                    "params": {"code": code, "description": st.get("description", "")}
                })
            return {"steps": steps, "agent": "CODE"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "CODE"}