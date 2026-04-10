"""
Maestro v13 — Migrado para ai_client centralizado.
Mantém cache, memória, e lógica de roteamento intactos.
"""

from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse

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
    "- action_type: send_message/write_text/open/call/create_file/search/send_file\n\n"
    "VARIAVEIS DE CONTEXTO (para subtarefas com depends_on):\n"
    "Quando uma subtarefa depende da anterior (depends_on: N), use essas variaveis nos params:\n"
    "  {output_folder_N}    → pasta criada/usada pela subtarefa N\n"
    "  {output_path_N}      → caminho principal (arquivo ou pasta) da subtarefa N\n"
    "  {output_files_N}     → primeiro arquivo criado pela subtarefa N\n"
    "  {output_all_files_N} → todos os arquivos separados por ponto-e-virgula\n"
    "  {output_url_N}       → URL visitada pela subtarefa N\n\n"
    "EXEMPLOS MULTI-SUBTAREFA:\n\n"
    "Tarefa: 'crie um site e envie os arquivos pelo Teams para Joao'\n"
    '{"analysis":"criar site e enviar via Teams","subtasks":['
    '{"agent":"CODE","task":"criar site HTML/CSS","params":{},"objectives":["Arquivos criados no Desktop"],"depends_on":null},'
    '{"agent":"DESKTOP","task":"enviar arquivos do site pelo Teams para Joao",'
    '"params":{"app":"teams","action_type":"send_file","person":"Joao",'
    '"files":"{output_all_files_1}","message":"Segue o site criado!"},'
    '"objectives":["Teams aberto","Arquivos anexados","Mensagem enviada"],"depends_on":1}'
    '],"skills":["code","teams"]}\n\n'
    "Tarefa: 'crie um projeto python e faca commit no github'\n"
    '{"analysis":"criar projeto e fazer commit","subtasks":['
    '{"agent":"CODE","task":"criar projeto Python","params":{},"objectives":["Arquivos criados"],"depends_on":null},'
    '{"agent":"CODE","task":"fazer git init, add e commit na pasta {output_folder_1}",'
    '"params":{"folder":"{output_folder_1}","action_type":"git_commit","message":"initial commit"},'
    '"objectives":["Commit criado"],"depends_on":1}'
    '],"skills":["code","git"]}\n\n'
    "Para DESKTOP, gere objectives (condicoes da tela):\n"
    "Exemplo simples: 'mande oi para Joao no Teams'\n"
    '{"analysis":"enviar msg no Teams","subtasks":[{"agent":"DESKTOP","task":"enviar mensagem",'
    '"params":{"app":"teams","action_type":"send_message","person":"Joao","message":"oi"},'
    '"objectives":["Teams aberto e visivel","Aba Chat selecionada","Conversa com Joao aberta","Mensagem enviada"],'
    '"depends_on":null}],"skills":["teams"]}\n\n'
    "Prefira 1 subtask quando possivel. Use depends_on apenas quando uma etapa precisa do resultado da anterior.\n"
    "Windows PT-BR."
)


class Maestro:
    def __init__(self):
        self._config = get_config()
        self._client = get_client()
        self.model = self._config.get_model("maestro")
        self._cache = {}

    def analyze(self, task):
        print("\n[Maestro] Analisando...")

        # Cache (só retorna se tem subtasks válidas)
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
                        "depends_on": None,
                    }],
                    "skills": list(wf.get("tags", [])),
                }
        except Exception:
            pass

        # API via client centralizado
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

            self._cache[key] = plan
            print(f"[Maestro] {len(plan['subtasks'])} subtask(s)")
            return plan

        except Exception as ex:
            print(f"[Maestro] Erro: {ex}")
            return {"error": True, "message": str(ex)}