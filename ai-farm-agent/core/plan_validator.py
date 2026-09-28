"""
Plan Validator — politicas de aceite aplicadas pelo Maestro.

Fluxo (inspirado no Maestro do hackathon_openai_sp): o LLM PROPOE, o codigo
VALIDA. Nenhuma regra aqui depende do modelo concordar — sao checagens
deterministicas sobre o plano do Maestro (subtasks) e sobre os passos que
cada agente propoe antes de executar.

Cada violacao tem um id de politica (espelhado em
AI-Farm-agents/20 Politicas/) para rastrear no segundo cerebro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KNOWN_AGENTS = {"DATA", "WEB", "CODE", "DESKTOP", "FILE"}

# Pedido para o agente PRODUZIR texto (nao so abrir um app)
_WRITE_VERBS = re.compile(
    r"\b(escrev\w*|digit\w*|redij\w*|redig\w*|compo\w*|elabor\w*|envi\w*|mand\w*)\b",
    re.IGNORECASE,
)
# Pedido de conteudo que o modelo precisa CRIAR (nao e texto literal)
_CREATIVE = re.compile(
    r"\b(poema|poesia|letra|texto|redacao|redação|historia|história|conto|carta|e-?mail|"
    r"resumo|lista|mensagem\s+(?:de|sobre|para)|artigo|piada|receita|roteiro|discurso)\b",
    re.IGNORECASE,
)
_SEARCH_VERB = re.compile(r"\b(pesquis\w*|procur\w*|busc\w*|busqu\w*)\b", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{output_\w+?_(\d+)\}")
_TEXT_APPS = {"notepad", "bloco de notas", "word", "microsoft word", "teams", "microsoft teams",
              "whatsapp", "whats", "zap", "outlook"}


@dataclass
class Validation:
    approved: bool = True
    violations: list[dict] = field(default_factory=list)

    def add(self, policy: str, msg: str, subtask: int | None = None) -> None:
        self.approved = False
        self.violations.append({"policy": policy, "msg": msg, "subtask": subtask})

    def feedback(self) -> str:
        return "\n".join(f"- [{v['policy']}] {v['msg']}" for v in self.violations)

    def summary(self) -> str:
        if self.approved:
            return "aprovado"
        return "reprovado: " + "; ".join(v["msg"] for v in self.violations)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9à-ú]+", (text or "").lower()))


def _is_echo(text: str, task: str) -> bool:
    """Texto curto cujas palavras ja estavam todas no pedido (so repete o pedido)."""
    words = _tokens(text)
    return bool(words) and len(text) < 80 and words <= _tokens(task)


def _literal_text(task: str) -> str:
    """
    Texto ditado: aspas logo apos 'escreva', 'digite', 'frase', 'mensagem'...
    Aspas em volta de um TITULO ('a letra da musica "Beat it"') nao contam.
    """
    m = re.search(r"\b(?:escrev\w*|digit\w*|frase|texto|mensagem|dizendo|diga)\s*:?\s*"
                  r"[\"“']([^\"”']{1,500})[\"”']", task or "", re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _wants_generated_content(task: str) -> bool:
    return bool(_WRITE_VERBS.search(task or "")) and bool(_CREATIVE.search(task or ""))


def validate_plan(task: str, plan: dict) -> Validation:
    """Checa o plano do Maestro (lista de subtasks) contra as politicas."""
    v = Validation()
    subs = plan.get("subtasks") or []
    if not subs:
        v.add("POL-000", "plano sem subtasks")
        return v

    literal = _literal_text(task)
    generated = _wants_generated_content(task) and not literal

    for i, sub in enumerate(subs, start=1):
        agent = (sub.get("agent") or "").upper()
        params = sub.get("params") or {}
        if agent not in KNOWN_AGENTS:
            v.add("POL-005", f"agente desconhecido '{agent}'", i)
            continue

        # POL-001 / POL-002: conteudo pedido precisa existir e nao pode ser eco do pedido
        app = (params.get("app") or "").lower()
        text = (params.get("text") or params.get("message") or "").strip()
        writes = (params.get("action_type") in ("write_text", "send_message")
                  or (app in _TEXT_APPS and _WRITE_VERBS.search(task or "")))
        uses_previous = "{output_" in text
        if agent == "DESKTOP" and writes and not uses_previous:
            if not text:
                v.add("POL-001", "o pedido e para escrever conteudo, mas o texto do plano esta vazio", i)
            elif generated and _is_echo(text, task):
                v.add("POL-002", f"o texto '{text[:60]}' so repete o pedido; gere o conteudo pedido "
                                 "ou declare que nao pode (cannot_do)", i)

        # POL-003: pesquisa precisa de termo
        if agent == "WEB" and _SEARCH_VERB.search(sub.get("task", "") + " " + task):
            from agents.web_agent import extract_query
            if not (params.get("query") or extract_query(sub.get("task", "")) or extract_query(task)):
                v.add("POL-003", "pesquisa sem termo de busca (params.query vazio)", i)

        # POL-004: variaveis de contexto so de subtasks anteriores e declaradas
        for ref in _PLACEHOLDER.findall(text + " " + (params.get("query") or "")):
            n = int(ref)
            if n >= i or sub.get("depends_on") in (None, ""):
                v.add("POL-004", f"usa resultado da subtask {n} sem depends_on valido", i)

    return v


def validate_steps(agent: str, subtask: dict, steps: list, task: str) -> Validation:
    """Checa os passos que um agente propos para uma subtask, antes de executar."""
    v = Validation()
    agent = (agent or "").upper()
    params = subtask.get("params") or {}
    if not steps:
        v.add("POL-000", "agente nao propos nenhum passo")
        return v
    if len(steps) > 40:
        v.add("POL-006", f"plano longo demais ({len(steps)} passos)")

    actions = [s.get("action", "") for s in steps]

    # Piloto do navegador recebe o OBJETIVO inteiro e confere cada acao na pagina:
    # pesquisa, entrar no site e clicar ficam por conta dele (POL-003/POL-007 cobertas).
    pilot = [s for s in steps if s.get("action") == "browser_task"]
    if agent == "WEB" and pilot:
        if not all(str((s.get("params") or {}).get("goal", "")).strip() for s in pilot):
            v.add("POL-007", "passo do piloto sem objetivo")
        return v

    if agent == "WEB" and _SEARCH_VERB.search(subtask.get("task", "") + " " + task):
        searched = any(
            ("search" in str((s.get("params") or {}).get("url", "")))
            or (s.get("action") in ("web_type", "type_text") and (s.get("params") or {}).get("text"))
            or (s.get("action") == "run_python" and "search" in str((s.get("params") or {}).get("code", "")))
            for s in steps
        )
        if not searched:
            v.add("POL-003", "os passos abrem o site mas nao executam a pesquisa")

    if agent == "WEB":
        # POL-007: toda acao pedida precisa estar nos passos. Antes "pesquise
        # gmail e entre no gmail" so pesquisava e saia "concluida".
        from agents.web_agent import follow_up
        fu = follow_up(subtask.get("task", "") + " " + task)
        urls = " ".join(str((s.get("params") or {}).get("url", "")) + " " +
                        str((s.get("params") or {}).get("code", "")) for s in steps)
        clicks = any(a in ("web_click", "vision_click", "browser_click", "uia_click", "click") for a in actions) \
            or "btnI=1" in urls
        if fu["site"]:
            domain = fu["site"].split("//")[-1].split("/")[0]
            if domain not in urls:
                v.add("POL-007", f"o pedido manda entrar em {domain}, mas nenhum passo abre esse site")
        if (fu["click"] or fu["first"]) and not clicks and not fu["site"]:
            v.add("POL-007", "o pedido manda clicar, mas nenhum passo clica")

    if agent == "DESKTOP" and (params.get("text") or params.get("message")):
        typed = any(a in ("app_type", "type_text", "vision_type", "uia_type") for a in actions)
        if not typed:
            v.add("POL-001", "ha texto para escrever mas nenhum passo digita")

    return v
