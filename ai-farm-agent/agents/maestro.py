"""
Maestro v12 — Objetivos verificaveis + cache que NAO salva vazios.
"""

import json, os, getpass
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
USERNAME = getpass.getuser()
BASE = "C:/Users/" + USERNAME

PROMPT = (
    "Voce e o MAESTRO do AI Farm Agent.\n\n"
    "Decompor tarefa em OBJETIVOS VERIFICAVEIS + params estruturados. JSON PURO.\n\n"
    "AGENTES: DATA (Excel), WEB (navegacao), CODE (criar codigo), DESKTOP (apps visuais), FILE (arquivos)\n"
    "ROTEAMENTO: Excel->DATA | Web->WEB | Codigo->CODE | Apps->DESKTOP | Arquivos->FILE\n\n"
    "PARAMS:\n"
    "- app: nome do app\n"
    "- person: APENAS nome\n"
    "- message: APENAS conteudo (sem instrucoes de envio)\n"
    "- text: texto a escrever\n"
    "- action_type: send_message/write_text/open/call/create_file/search\n\n"
    "Para DESKTOP, gere objectives (condicoes da tela):\n"
    "Exemplo: 'mande oi para Joao no Teams'\n"
    '{"analysis":"enviar msg no Teams","subtasks":[{"agent":"DESKTOP","task":"enviar mensagem",'
    '"params":{"app":"teams","action_type":"send_message","person":"Joao","message":"oi"},'
    '"objectives":["Teams aberto e visivel","Aba Chat selecionada","Conversa com Joao aberta","Mensagem enviada"],'
    '"depends_on":null}],"skills":["teams"]}\n\n'
    "Prefira 1 subtask. Windows PT-BR. Usuario: " + USERNAME
)


class Maestro:
    def __init__(self):
        self.model = "claude-haiku-4-5-20251001"
        self._cache = {}

    def analyze(self, task):
        print("\n[Maestro] Analisando...")

        # Cache (so retorna se tem subtasks validas)
        key = task.lower().strip()[:80]
        if key in self._cache:
            cached = self._cache[key]
            if cached.get("subtasks") and len(cached["subtasks"]) > 0:
                print("[Maestro] Cache hit!")
                return cached
            else:
                # Cache invalido, remove
                del self._cache[key]

        # Memoria
        try:
            from memory.workflow_store import find_similar_workflow
            wf = find_similar_workflow(task)
            if wf:
                print("[Maestro] Workflow da memoria!")
                return {
                    "analysis": "Template da memoria",
                    "subtasks": [{"agent": wf["agent"], "task": wf["task"],
                                  "params": wf.get("params", {}),
                                  "objectives": wf.get("objectives", []),
                                  "depends_on": None}],
                    "skills": list(wf.get("tags", []))
                }
        except: pass

        # API
        try:
            resp = client.messages.create(model=self.model, max_tokens=1500, system=PROMPT,
                messages=[{"role": "user", "content": "TAREFA: " + task + "\nJSON puro."}])
            plan = safe_parse(resp.content[0].text.strip(), self.model)
            if "subtasks" not in plan or len(plan.get("subtasks", [])) == 0:
                return {"error": True, "message": "Sem subtasks"}
            # So cacheia se tem subtasks validas
            self._cache[key] = plan
            print("[Maestro] " + str(len(plan["subtasks"])) + " subtask(s)")
            return plan
        except Exception as ex:
            print("[Maestro] Erro: " + str(ex))
            return {"error": True, "message": str(ex)}