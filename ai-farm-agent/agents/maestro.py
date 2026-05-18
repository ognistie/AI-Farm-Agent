"""
Maestro v17 — Roteamento inteligente + ambiguity gate.

MUDANÇAS v17 (vs v16):
- AMBIGUITY GATE (cenários A e J do briefing): prompts vagos ("deixa o
  projeto rodando", "atualiza o relatorio do mes passado") NAO disparam
  3 hipoteses em paralelo. Maestro retorna needs_clarification=True com
  uma unica pergunta objetiva.
- Heuristica deterministica detecta padroes obvios antes de chamar LLM.
- Prompt ensina o LLM a usar needs_clarification quando ambiguo.

MUDANÇAS v16:
- "abra VS Code e crie arquivo/projeto" → CODE (não DESKTOP)
- "abra VS Code" (sem criar) → DESKTOP
"""

import re

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
    "2. Se pede EDITAR/MODIFICAR/CORRIGIR arquivo de codigo existente → CODE\n"
    "3. Se pede ABRIR VS Code APONTANDO PRA UMA PASTA (sem criar nada) → CODE\n"
    "4. Se pede CRIAR planilha/Excel com dados → DATA\n"
    "5. Se pede navegar web/pesquisar/abrir site → WEB\n"
    "6. Se pede APENAS ABRIR um app vazio (sem criar conteudo nem apontar pasta) → DESKTOP\n"
    "7. Se pede interagir com app desktop (Teams, WhatsApp, Notepad, Paint) → DESKTOP\n"
    "8. Se pede organizar/mover/copiar arquivos → FILE\n\n"

    "EXEMPLOS DE ROTEAMENTO:\n"
    "- 'abra o vs code e crie um arquivo python' → CODE (criar arquivo = CODE)\n"
    "- 'edite o app.py adicionando uma rota /login' → CODE (edit_existing)\n"
    "- 'abra o vs code na pasta meu-projeto' → CODE (open_vscode_folder)\n"
    "- 'abra o vs code' → DESKTOP (apenas abrir vazio = DESKTOP)\n"
    "- 'crie um site html' → CODE\n"
    "- 'crie um script python que renomeia imagens' → CODE (single_file)\n"
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
    "4. forbidden_assumptions = o que NAO presumir\n"
    "5. PROIBIDO acoplar CODE + DESKTOP notepad/word com o codigo gerado.\n"
    "   Se voce roteou para CODE, o CODE ja cria os arquivos e abre o\n"
    "   VS Code. NUNCA crie uma subtask DESKTOP escrevendo o HTML/python\n"
    "   no notepad/word como 'visualizacao'. Isso confunde o usuario.\n\n"

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

    "═══ AMBIGUITY GATE (cenarios A e J do briefing) ═══\n"
    "Se a tarefa for AMBIGUA ou faltam dados essenciais para executar com\n"
    "seguranca (qual app? qual arquivo? qual periodo? qual destinatario?),\n"
    "NUNCA chute. NUNCA execute 3 hipoteses em paralelo. Retorne:\n"
    "  {\"needs_clarification\": true, \"question\": \"<UMA pergunta objetiva>\",\n"
    "   \"why\": \"<o que esta faltando>\"}\n"
    "Exemplos de pedidos ambiguos:\n"
    "- 'deixa o projeto rodando'        → qual projeto? rodar = dev/test/prod?\n"
    "- 'atualiza o relatorio do mes passado' → qual relatorio? que mes (abs)?\n"
    "- 'envia para ele'                 → ele quem? por qual canal?\n"
    "Regra: faca NO MAXIMO 1 pergunta por turno (briefing secao 10).\n\n"

    "Prefira 1 subtask. Windows PT-BR. JSON PURO."
)


# ───────────────────────────────────────────────────────────────────────
#  Heuristica determinstica de ambiguidade (cenarios A e J)
# ───────────────────────────────────────────────────────────────────────

# Frases curtas notoriamente vagas — fazem o usuario pagar uma chamada LLM
# por nada. Pre-bloqueamos com pergunta direta.
_VAGUE_PHRASES = {
    "deixa rodando", "deixa o projeto rodando", "deixa rodar",
    "faz funcionar", "arruma isso", "conserta", "resolve isso",
    "atualiza", "atualiza o relatorio", "envia pra ele", "manda pra ela",
    "termina isso", "continua de onde parou",
}

# Marcadores temporais relativos (cenario J).
_RELATIVE_TIME_MARKERS = (
    "mes passado", "semana passada", "ontem", "outro dia",
    "ultimo mes", "ultima semana", "anteontem", "esses dias",
    "no ano passado",
)

# Marcadores deicticos sem antecedente claro.
_DEICTIC_PRONOUNS = ("ele", "ela", "isso", "aquilo", "aquele", "aquela")


def _detect_ambiguity(task: str) -> dict | None:
    """
    Retorna {"question": ..., "why": ...} se a tarefa for ambigua, senao None.

    NAO substitui o LLM — apenas elimina ambiguidades obvias antes do
    custo de uma chamada de API.
    """
    if not task:
        return {
            "question": "O que voce gostaria que eu fizesse?",
            "why": "tarefa vazia",
        }

    t = task.lower().strip()

    # Curto demais para uma intencao acionavel
    word_count = len(re.findall(r"\w+", t))
    if word_count <= 2 and t not in {"oi", "ola", "ajuda", "help"}:
        return {
            "question": f"'{task}' — pode detalhar o que voce quer fazer?",
            "why": "tarefa curta demais para roteamento confiavel",
        }

    # Frase vaga em catalogo
    for vague in _VAGUE_PHRASES:
        if t == vague or t.startswith(vague + " ") or t.endswith(" " + vague):
            return {
                "question": "Pode especificar qual projeto/arquivo/aplicacao e o resultado esperado?",
                "why": f"frase vaga detectada: '{vague}'",
            }

    # Marcador temporal relativo sem objeto especifico
    for marker in _RELATIVE_TIME_MARKERS:
        if marker in t:
            # Se nao tem nome proprio nem arquivo identificavel, e ambiguo
            has_filename = bool(re.search(r"\b[\w-]+\.[a-zA-Z]{1,5}\b", task))
            has_proper_noun = bool(re.search(r"\b[A-Z][a-z]+\b", task))
            if not has_filename and not has_proper_noun:
                return {
                    "question": f"Qual data exatamente ({marker})? E qual arquivo/relatorio especifico?",
                    "why": f"marcador temporal relativo sem referencia absoluta: '{marker}'",
                }

    return None


class Maestro:
    def __init__(self):
        self._config = get_config()
        self._client = get_client()
        self.model = self._config.get_model("maestro")
        self._cache = {}

    def analyze(self, task):
        print("\n[Maestro] Analisando...")

        # Ambiguity gate (cenarios A e J): bloqueia ANTES do cache,
        # antes da memoria e antes da API. Pergunta UMA coisa só.
        ambiguity = _detect_ambiguity(task)
        if ambiguity:
            print(f"[Maestro] Ambiguidade detectada: {ambiguity['why']}")
            return {
                "needs_clarification": True,
                "question": ambiguity["question"],
                "why": ambiguity["why"],
                "subtasks": [],
            }

        key = task.lower().strip()[:80]
        if key in self._cache:
            cached = self._cache[key]
            if cached.get("subtasks") and len(cached["subtasks"]) > 0:
                print("[Maestro] Cache hit!")
                return cached
            else:
                del self._cache[key]

        # Memória — falha do lookup nunca pode bloquear a tarefa,
        # mas precisa de log para diagnosticar workflow_store quebrado.
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
        except Exception as mem_err:
            print(f"[Maestro] workflow_store indisponivel: {mem_err}")

        # API
        try:
            raw = self._client.message(
                model=self.model, system=PROMPT,
                user_content=f"TAREFA: {task}\nJSON puro.",
                max_tokens=self._config.get("limits.max_tokens_fast", 1500),
            )
            plan = safe_parse(raw, self.model)

            # Se o LLM detectou ambiguidade que a heuristica nao pegou,
            # propaga o pedido de clarificacao em vez de "Sem subtasks".
            if plan.get("needs_clarification"):
                print(f"[Maestro] LLM pediu clarificacao: {plan.get('why','')}")
                return {
                    "needs_clarification": True,
                    "question": plan.get("question", "Pode dar mais detalhes?"),
                    "why": plan.get("why", "ambiguidade detectada pelo LLM"),
                    "subtasks": [],
                }

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

            # Filtro defensivo: se temos uma subtask CODE, removemos qualquer
            # subtask DESKTOP que pareça apenas "colar o codigo no notepad/word"
            # como visualizacao — comportamento ruim que confunde o usuario.
            subs = plan.get("subtasks", [])
            has_code = any((s.get("agent") or "").upper() == "CODE" for s in subs)
            if has_code:
                filtered = []
                removed = 0
                for s in subs:
                    agent = (s.get("agent") or "").upper()
                    if agent == "DESKTOP":
                        p = s.get("params", {}) or {}
                        app = (p.get("app", "") or "").lower()
                        action = (p.get("action_type", "") or "").lower()
                        text = (p.get("text", "") or p.get("message", "") or "")
                        # Heuristica: notepad/word + texto que parece codigo
                        looks_like_code = any(
                            tok in text for tok in (
                                "<html", "<!DOCTYPE", "<script", "<style",
                                "def ", "class ", "import ", "from ", "function ",
                            )
                        )
                        if app in ("notepad", "bloco de notas", "word", "microsoft word") and (
                            action in ("write_text", "type", "paste") or looks_like_code
                        ):
                            removed += 1
                            continue
                    filtered.append(s)
                if removed:
                    print(f"[Maestro] Removido(s) {removed} subtask(s) DESKTOP redundante(s) acoplada(s) ao CODE")
                    plan["subtasks"] = filtered

            self._cache[key] = plan
            print(f"[Maestro] {len(plan['subtasks'])} subtask(s)")
            return plan

        except Exception as ex:
            print(f"[Maestro] Erro: {ex}")
            return {"error": True, "message": str(ex)}