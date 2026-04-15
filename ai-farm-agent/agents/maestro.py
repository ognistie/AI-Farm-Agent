"""
Maestro v15 — Inteligência de contexto entre subtarefas.
MUDANÇAS v15:
- Lista EXPLÍCITA de variáveis válidas no prompt
- Regra: NUNCA usar variável que não está na lista
- Exemplo de pesquisa + envio com web_read e {output_text_N}
- Campo forbidden_assumptions
- Validação pós-LLM: limpa texto inventado
"""

from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse

PROMPT = (
    "Voce e o MAESTRO do AI Farm Agent — o cerebro central.\n"
    "Entenda a INTENCAO REAL do usuario e gere um plano preciso.\n\n"

    "═══ PRINCIPIO ═══\n"
    "PROCEDIMENTO (como fazer) ≠ CONTEUDO (o que escrever/digitar).\n"
    "Se o usuario NAO pediu texto → text deve ser ''.\n"
    "NUNCA invente texto, mensagens ou conteudo.\n\n"

    "═══ AGENTES ═══\n"
    "DATA: Excel | WEB: navegacao web | CODE: criar codigo\n"
    "DESKTOP: apps (Teams, WhatsApp, Notepad, Paint) | FILE: arquivos\n\n"

    "═══ ROTEAMENTO ═══\n"
    "Excel→DATA | Browser/site/pesquisa→WEB | Codigo→CODE | Apps→DESKTOP | Arquivos→FILE\n\n"

    "═══ PARAMS ═══\n"
    "app, person, message, text, action_type, query, url\n\n"

    "═══ VARIAVEIS DE CONTEXTO (SOMENTE ESTAS EXISTEM) ═══\n"
    "Quando depends_on: N, use APENAS estas variaveis:\n"
    "  {output_folder_N}     → pasta criada pela subtask N\n"
    "  {output_path_N}       → caminho principal\n"
    "  {output_files_N}      → primeiro arquivo\n"
    "  {output_all_files_N}  → todos os arquivos\n"
    "  {output_url_N}        → URL visitada\n"
    "  {output_text_N}       → conteudo textual (resultado de pesquisa, leitura)\n\n"
    "⚠️ NUNCA use variaveis que NAO estao nesta lista.\n"
    "⚠️ NUNCA invente variaveis como {output_search_content}, {resultado}, etc.\n\n"

    "═══ REGRAS DE DECOMPOSICAO ═══\n"
    "1. UM APP = 1 subtask (nunca separe abrir/usar)\n"
    "2. 2+ subtasks APENAS quando APPS DIFERENTES cooperam\n"
    "3. Se a subtask WEB precisa capturar conteudo para a proxima, inclua web_read nos objectives\n"
    "4. text='' se usuario nao pediu para escrever\n"
    "5. forbidden_assumptions lista o que NAO presumir\n\n"

    "═══ EXEMPLOS ═══\n\n"

    "Tarefa: 'abra o bloco de notas'\n"
    '{"analysis":"apenas abrir","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir bloco de notas","params":{"app":"notepad","action_type":"open","text":""},'
    '"objectives":["Notepad aberto"],'
    '"forbidden_assumptions":["NAO escrever nenhum texto"],'
    '"depends_on":null}],"skills":["notepad"]}\n\n'

    "Tarefa: 'abra o notepad e escreva de 10 ate 20'\n"
    '{"analysis":"abrir notepad e escrever numeros","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir notepad e escrever numeros 10-20",'
    '"params":{"app":"notepad","action_type":"write_text","text":"10\\n11\\n12\\n13\\n14\\n15\\n16\\n17\\n18\\n19\\n20"},'
    '"objectives":["Notepad aberto","Numeros escritos"],'
    '"forbidden_assumptions":["NAO escrever Ola"],'
    '"depends_on":null}],"skills":["notepad"]}\n\n'

    "Tarefa: 'abra o youtube e pesquise videos de skate'\n"
    '{"analysis":"youtube + pesquisa","subtasks":[{"agent":"WEB",'
    '"task":"abrir youtube e pesquisar videos de skate",'
    '"params":{"url":"https://www.youtube.com","query":"videos de skate","action_type":"search"},'
    '"objectives":["YouTube aberto","Pesquisa realizada"],'
    '"forbidden_assumptions":["NAO pesquisar termo diferente"],'
    '"depends_on":null}],"skills":["youtube"]}\n\n'

    "Tarefa: 'pesquise sobre o Palmeiras e envie no Teams para Joao'\n"
    '{"analysis":"pesquisar + enviar via Teams","subtasks":['
    '{"agent":"WEB","task":"pesquisar sobre Palmeiras e ler resultado",'
    '"params":{"url":"https://www.google.com","query":"historia do Palmeiras","action_type":"search"},'
    '"objectives":["Pesquisa realizada","Conteudo lido com web_read"],'
    '"forbidden_assumptions":["NAO inventar conteudo"],'
    '"depends_on":null},'
    '{"agent":"DESKTOP","task":"enviar resultado da pesquisa para Joao no Teams",'
    '"params":{"app":"teams","action_type":"send_message","person":"Joao","message":"{output_text_1}"},'
    '"objectives":["Teams aberto","Mensagem enviada"],'
    '"forbidden_assumptions":["NAO enviar texto inventado"],'
    '"depends_on":1}'
    '],"skills":["web","teams"]}\n\n'

    "Tarefa: 'abra o paint e desenhe uma casa'\n"
    '{"analysis":"abrir paint e desenhar","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir paint e desenhar uma casa",'
    '"params":{"app":"paint","action_type":"draw","text":"casa"},'
    '"objectives":["Paint aberto","Desenho realizado"],'
    '"forbidden_assumptions":["NAO apenas abrir sem desenhar"],'
    '"depends_on":null}],"skills":["paint"]}\n\n'

    "Prefira 1 subtask. Windows PT-BR. JSON PURO."
)


class Maestro:
    def __init__(self):
        self._config = get_config()
        self._client = get_client()
        self.model = self._config.get_model("maestro")
        self._cache = {}

    def analyze(self, task):
        print("\n[Maestro] Analisando...")

        key = task.lower().strip()[:80]
        if key in self._cache:
            cached = self._cache[key]
            if cached.get("subtasks") and len(cached["subtasks"]) > 0:
                print("[Maestro] Cache hit!")
                return cached
            else:
                del self._cache[key]

        # Memória
        try:
            from memory.workflow_store import find_similar_workflow
            wf = find_similar_workflow(task)
            if wf:
                print("[Maestro] Workflow da memória!")
                return {
                    "analysis": "Template da memória",
                    "subtasks": [{
                        "agent": wf["agent"],
                        "task": wf["task"],
                        "params": wf.get("params", {}),
                        "objectives": wf.get("objectives", []),
                        "forbidden_assumptions": [],
                        "depends_on": None,
                    }],
                    "skills": list(wf.get("tags", [])),
                }
        except Exception:
            pass

        # API
        try:
            raw = self._client.message(
                model=self.model,
                system=PROMPT,
                user_content=f"TAREFA: {task}\nJSON puro.",
                max_tokens=self._config.get("limits.max_tokens_fast", 1500),
            )
            plan = safe_parse(raw, self.model)

            if "subtasks" not in plan or len(plan.get("subtasks", [])) == 0:
                return {"error": True, "message": "Sem subtasks"}

            # Validação pós-LLM
            for sub in plan.get("subtasks", []):
                params = sub.get("params", {})
                forbidden = sub.get("forbidden_assumptions", [])

                # Bloqueia texto genérico inventado
                text_val = params.get("text", "")
                msg_val = params.get("message", "")
                generics = ["Ola!", "Ola", "Olá", "Hello", "Hi", "Oi", "Bom dia"]

                for rule in forbidden:
                    if "NAO escrever" in rule:
                        if text_val in generics:
                            params["text"] = ""
                            print(f"  [Maestro] Bloqueou text inventado: '{text_val}'")
                        if msg_val in generics and "message" not in task.lower():
                            params["message"] = ""
                            print(f"  [Maestro] Bloqueou message inventada: '{msg_val}'")

            self._cache[key] = plan
            print(f"[Maestro] {len(plan['subtasks'])} subtask(s)")
            return plan

        except Exception as ex:
            print(f"[Maestro] Erro: {ex}")
            return {"error": True, "message": str(ex)}