"""
Maestro v16 — Roteamento inteligente + contexto seguro.
MUDANÇAS v16:
- "abra VS Code e crie arquivo/projeto" → CODE (não DESKTOP)
- "abra VS Code" (sem criar) → DESKTOP
- "abra paint e desenhe" → DESKTOP com action_type=draw
- Variáveis válidas atualizadas: inclui {output_summary_N}
- Exemplo de pesquisa+envio com summary
"""

from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse

PROMPT = (
    "Voce e o MAESTRO do AI Farm Agent.\n"
    "Entenda a INTENCAO REAL e gere plano preciso. JSON PURO.\n\n"

    "═══ PRINCIPIO ═══\n"
    "PROCEDIMENTO ≠ CONTEUDO. Se usuario NAO pediu texto → text=''.\n"
    "NUNCA invente texto, mensagens ou conteudo.\n\n"

    "═══ ROTEAMENTO (ORDEM DE PRIORIDADE) ═══\n"
    "1. Se pede CRIAR codigo/projeto/arquivo de programacao → CODE (mesmo se menciona VS Code)\n"
    "2. Se pede CRIAR planilha/Excel com dados → DATA\n"
    "3. Se pede navegar web/pesquisar/abrir site → WEB\n"
    "4. Se pede APENAS ABRIR um app (sem criar conteudo) → DESKTOP\n"
    "5. Se pede interagir com app desktop (Teams, WhatsApp, Notepad, Paint) → DESKTOP\n"
    "6. Se pede organizar/mover/copiar arquivos → FILE\n\n"

    "EXEMPLOS DE ROTEAMENTO:\n"
    "- 'abra o vs code e crie um arquivo python' → CODE (criar arquivo = CODE)\n"
    "- 'abra o vs code' → DESKTOP (apenas abrir = DESKTOP)\n"
    "- 'crie um site html' → CODE\n"
    "- 'abra o paint e desenhe' → DESKTOP com action_type=draw\n"
    "- 'pesquise no google' → WEB\n"
    "- 'crie uma planilha de vendas' → DATA\n\n"

    "═══ PARAMS ═══\n"
    "app, person, message, text, action_type, query, url\n\n"

    "═══ VARIAVEIS DE CONTEXTO ═══\n"
    "Quando depends_on: N, use SOMENTE:\n"
    "  {output_folder_N}   {output_path_N}   {output_files_N}\n"
    "  {output_all_files_N}   {output_url_N}\n"
    "  {output_text_N}     {output_summary_N}\n"
    "⚠️ NUNCA invente variaveis fora desta lista.\n"
    "⚠️ Para enviar resultado de pesquisa, use {output_summary_N} (mais curto e seguro).\n\n"

    "═══ REGRAS ═══\n"
    "1. UM APP = 1 subtask\n"
    "2. 2+ subtasks APENAS quando APPS DIFERENTES cooperam\n"
    "3. text='' se usuario nao pediu para escrever\n"
    "4. forbidden_assumptions = o que NAO presumir\n\n"

    "═══ EXEMPLOS ═══\n\n"

    "Tarefa: 'abra o bloco de notas'\n"
    '{"analysis":"apenas abrir","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir bloco de notas","params":{"app":"notepad","action_type":"open","text":""},'
    '"objectives":["Notepad aberto"],'
    '"forbidden_assumptions":["NAO escrever nenhum texto"],"depends_on":null}],"skills":["notepad"]}\n\n'

    "Tarefa: 'abra o vs code e crie um arquivo python com sistema de login'\n"
    '{"analysis":"criar arquivo python no VS Code","subtasks":[{"agent":"CODE",'
    '"task":"criar arquivo python com sistema de login e abrir no VS Code",'
    '"params":{"action_type":"create_file"},'
    '"objectives":["Arquivo criado","VS Code aberto com o arquivo"],'
    '"forbidden_assumptions":["NAO apenas abrir VS Code vazio"],"depends_on":null}],"skills":["python","vscode"]}\n\n'

    "Tarefa: 'abra o youtube e pesquise videos de skate'\n"
    '{"analysis":"youtube + pesquisa","subtasks":[{"agent":"WEB",'
    '"task":"abrir youtube e pesquisar videos de skate",'
    '"params":{"url":"https://www.youtube.com","query":"videos de skate","action_type":"search"},'
    '"objectives":["YouTube aberto","Pesquisa realizada"],'
    '"forbidden_assumptions":["NAO pesquisar termo diferente"],"depends_on":null}],"skills":["youtube"]}\n\n'

    "Tarefa: 'pesquise sobre Palmeiras e envie no Teams para Joao'\n"
    '{"analysis":"pesquisar + enviar via Teams","subtasks":['
    '{"agent":"WEB","task":"pesquisar sobre Palmeiras e ler resultado",'
    '"params":{"url":"https://www.google.com","query":"historia do Palmeiras","action_type":"search"},'
    '"objectives":["Pesquisa realizada","Conteudo lido"],'
    '"forbidden_assumptions":["NAO inventar conteudo"],"depends_on":null},'
    '{"agent":"DESKTOP","task":"enviar resumo da pesquisa para Joao no Teams",'
    '"params":{"app":"teams","action_type":"send_message","person":"Joao","message":"{output_summary_1}"},'
    '"objectives":["Teams aberto","Mensagem enviada"],'
    '"forbidden_assumptions":["NAO enviar texto inventado"],"depends_on":1}'
    '],"skills":["web","teams"]}\n\n'

    "Tarefa: 'abra o paint e desenhe uma casa'\n"
    '{"analysis":"abrir paint e desenhar","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir paint e desenhar uma casa",'
    '"params":{"app":"paint","action_type":"draw","text":"casa"},'
    '"objectives":["Paint aberto","Desenho feito"],'
    '"forbidden_assumptions":["NAO apenas abrir sem desenhar"],"depends_on":null}],"skills":["paint"]}\n\n'

    "Tarefa: 'abra o notepad e escreva de 10 ate 20'\n"
    '{"analysis":"notepad + numeros","subtasks":[{"agent":"DESKTOP",'
    '"task":"abrir notepad e escrever numeros 10-20",'
    '"params":{"app":"notepad","action_type":"write_text","text":"10\\n11\\n12\\n13\\n14\\n15\\n16\\n17\\n18\\n19\\n20"},'
    '"objectives":["Notepad aberto","Numeros escritos"],'
    '"forbidden_assumptions":["NAO escrever Ola"],"depends_on":null}],"skills":["notepad"]}\n\n'

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
                        "agent": wf["agent"], "task": wf["task"],
                        "params": wf.get("params", {}),
                        "objectives": wf.get("objectives", []),
                        "forbidden_assumptions": [], "depends_on": None,
                    }],
                    "skills": list(wf.get("tags", [])),
                }
        except: pass

        # API
        try:
            raw = self._client.message(
                model=self.model, system=PROMPT,
                user_content=f"TAREFA: {task}\nJSON puro.",
                max_tokens=self._config.get("limits.max_tokens_fast", 1500),
            )
            plan = safe_parse(raw, self.model)

            if "subtasks" not in plan or not plan.get("subtasks"):
                return {"error": True, "message": "Sem subtasks"}

            # Validação pós-LLM: bloqueia texto inventado
            generics = {"Ola!", "Ola", "Olá", "Hello", "Hi", "Oi", "Bom dia", ""}
            for sub in plan.get("subtasks", []):
                params = sub.get("params", {})
                for rule in sub.get("forbidden_assumptions", []):
                    if "NAO escrever" in rule:
                        if params.get("text", "") in generics:
                            params["text"] = ""
                        if params.get("message", "") in generics and "message" not in task.lower():
                            params["message"] = ""

            self._cache[key] = plan
            print(f"[Maestro] {len(plan['subtasks'])} subtask(s)")
            return plan

        except Exception as ex:
            print(f"[Maestro] Erro: {ex}")
            return {"error": True, "message": str(ex)}