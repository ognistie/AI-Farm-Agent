"""
Maestro v18 — Roteamento inteligente + ambiguity gate + memoria de rotas.

MUDANÇAS v18 (vs v17):
- Sem cache de planos em memoria: a chave era task[:80], entao tarefas
  diferentes com o mesmo comeco recebiam o MESMO plano, e repetir um
  pedido devolvia sempre a mesma resposta.
- Memoria deixou de ser ATALHO (antes: devolvia so o 1o agente, sem
  params, sem chamar o LLM — perdia subtasks). Agora as rotas que ja
  funcionaram entram no prompt como REFERENCIA; o plano e o conteudo sao
  sempre gerados para a tarefa atual.

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
    "NUNCA invente texto que o usuario nao pediu.\n\n"

    "═══ CONTEUDO PEDIDO ═══\n"
    "a) Texto ditado (entre aspas ou 'escreva X'): use X exatamente.\n"
    "b) Pedido para CRIAR conteudo (poema, email, resumo, lista, historia, texto sobre um tema):\n"
    "   ESCREVA o conteudo completo e coloque em text/message. Isso nao e inventar: foi pedido.\n"
    "c) Reproduzir obra protegida (letra de musica, capitulo de livro, texto pago): nao pode.\n"
    "   NUNCA escreva um substituto (titulo, trecho inventado). Retorne:\n"
    "   {\"cannot_do\": true, \"reason\": \"<por que>\", \"alternative\": \"<o que posso fazer>\"}\n"
    "   (ex.: resumo do tema da musica com palavras proprias, ou pesquisar a letra oficial).\n\n"
    "═══ PESQUISA WEB ═══\n"
    "Toda subtask WEB de pesquisa precisa de params.query com o termo exato.\n"
    "Cada pedido e novo: query, texto, nomes e tema saem SOMENTE da tarefa atual.\n"
    "Os exemplos abaixo ensinam o FORMATO — nao copie seus valores.\n\n"

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


def _format_route_hint(routes: list) -> str:
    """Rotas da memoria -> bloco de referencia para o prompt (sem conteudo)."""
    if not routes:
        return ""
    from memory.workflow_store import format_route
    lines = [
        "REFERENCIA (memoria): rotas de agentes que ja funcionaram em tarefas "
        "parecidas. Use so como pista de roteamento. NAO reutilize textos, "
        "temas, nomes ou valores; se a tarefa atual pede outra coisa, ignore."
    ]
    for r in routes:
        lines.append(f"- {format_route(r['route'])}  [{r.get('success_count', 1)} sucesso(s)]")
    return "\n".join(lines)


class Maestro:
    def __init__(self, memory=None):
        self._config = get_config()
        self._client = get_client()
        self.model = self._config.get_model("maestro")
        self.effort = self._config.get_effort("maestro")
        self._memory = memory

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

        # Memoria de rotas — falha do lookup nunca bloqueia a tarefa.
        # Vai na mensagem do usuario (nao no system) para nao invalidar
        # o prompt cache do PROMPT, que e o prefixo estavel.
        routes = []
        try:
            if self._memory is None:
                from agents.memory_agent import MemoryAgent
                self._memory = MemoryAgent()
            routes = self._memory.find_routes(task, k=2)
            if routes:
                print(f"[Maestro] {len(routes)} rota(s) da memoria como referencia")
        except Exception as mem_err:
            print(f"[Maestro] memoria indisponivel: {mem_err}")
        hint = _format_route_hint(routes)

        # Segundo cerebro: tarefas de referencia parecidas (caminhos que ja
        # funcionaram, curados no Obsidian). Tambem so como referencia.
        try:
            from core.brain import get_brain
            refs = get_brain().find_references(task, k=2)
            if refs:
                print(f"[Maestro] {len(refs)} referencia(s) do segundo cerebro")
                hint += ("\n" if hint else "") + "REFERENCIA (segundo cerebro, so pista — nao copie valores):\n"
                hint += "\n".join(f"- {r['title']} [{r['agent']}]: {r['path']}" for r in refs)
        except Exception as brain_err:
            print(f"[Maestro] segundo cerebro indisponivel: {brain_err}")

        plan = self._ask(task, hint)
        if not plan.get("subtasks"):
            return plan   # clarificacao, limitacao ou erro

        # ── Politicas de aceite (codigo, nao LLM) ────────────────────
        # O Maestro propoe; as politicas validam. Uma reprovacao ganha UMA
        # chance de replanejar com o motivo literal.
        from core.plan_validator import validate_plan
        validation = validate_plan(task, plan)
        if not validation.approved:
            print(f"[Maestro] Plano reprovado: {validation.summary()}")
            retry = self._ask(task, hint, feedback=validation.feedback())
            if retry.get("limitation") or retry.get("needs_clarification"):
                return retry
            if retry.get("subtasks"):
                plan = retry
                validation = validate_plan(task, plan)

        plan["validation"] = {"approved": validation.approved,
                              "violations": validation.violations}
        if routes:
            plan["memory_routes"] = [r["route"] for r in routes]
        if not validation.approved:
            return {"error": True, "subtasks": [], "validation": plan["validation"],
                    "rejected_plan": plan,
                    "message": "O Maestro reprovou o plano: " + validation.summary()}
        return plan

    def _ask(self, task: str, hint: str = "", feedback: str = "") -> dict:
        """Uma chamada ao LLM + saneamento do plano (sem validacao de politica)."""
        try:
            user = f"TAREFA: {task}\n"
            if hint:
                user += f"\n{hint}\n"
            if feedback:
                user += ("\nSEU PLANO ANTERIOR FOI REPROVADO PELAS POLITICAS DE ACEITE:\n"
                         f"{feedback}\nCorrija e devolva o plano completo.\n")
            user += "JSON puro."
            raw = self._client.message(
                model=self.model, system=PROMPT,
                user_content=user,
                max_tokens=self._config.get("limits.max_tokens_strong", 16000),
                effort=self.effort, agent="MAESTRO",
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

            # Pedido que o sistema nao deve cumprir (ex.: letra de musica
            # protegida). Melhor avisar do que escrever um substituto.
            if plan.get("cannot_do"):
                reason = plan.get("reason") or "Nao posso fazer isso como pedido."
                alt = plan.get("alternative") or ""
                print(f"[Maestro] Limitacao: {reason}")
                if alt and not alt.lower().startswith("posso"):
                    alt = "Posso " + alt[0].lower() + alt[1:]
                return {"limitation": True, "subtasks": [],
                        "message": reason + (f" {alt}" if alt else "")}

            if "subtasks" not in plan or not plan.get("subtasks"):
                return {"error": True, "message": "Sem subtasks"}

            # ── PRESERVA TASK ORIGINAL ──────────────────────────────────
            # O Maestro pode REFORMULAR a task ao gerar subtasks (ex.:
            # "sistema profissional" -> "criar sistema com arquitetura
            # modular"). Isso polui topic extraction e theme leak downstream.
            # Carregamos `original_task` ao lado para que os agentes possam
            # usar a versao do USUARIO quando precisarem (topic, theme leak).
            for sub in plan.get("subtasks", []):
                sub.setdefault("original_task", task)

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

            print(f"[Maestro] {len(plan['subtasks'])} subtask(s)")
            return plan

        except Exception as ex:
            print(f"[Maestro] Erro: {ex}")
            return {"error": True, "message": str(ex)}