"""
Autorizacao por efeito: o que uma acao faz fora do computador, decidido pelo app e nao pelo modelo.

A autorizacao por agente (core/action_policy.py) diz qual ferramenta cada agente usa. Ela nao ve o
efeito: o piloto do navegador pode clicar em "Enviar" ou "Comprar" e so uma frase no prompt o
impedia. Aqui o efeito e classificado pelo que a acao toca (nome do botao, campo, tecla, tipo de
operacao) e cada caso sensivel passa por esta porta.

Modos (config.yaml > execution.authorization):
  shadow   so registra o que seria bloqueado; nada muda para a pessoa (padrao, para medir antes)
  enforce  efeito sensivel so com confirmacao explicita no pedido ("confirmo", "pode enviar")
  off      desligado
O registro em memory/authorization.jsonl guarda o rotulo do elemento (ex.: "Enviar"), nunca o
texto digitado nem o conteudo da pagina.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Optional

LOG = Path(__file__).resolve().parents[1] / "memory" / "authorization.jsonl"
MODES = ("off", "shadow", "enforce")
_lock = threading.Lock()

# Efeito fora do computador ou dificil de desfazer. O rotulo e normalizado sem acento.
KINDS = (
    ("pagar", r"\b(?:pag(?:ar|ue|a)|pagamento|finalizar (?:compra|pedido)|fechar pedido|checkout|pay|place order|"
              r"confirmar (?:compra|pedido|pagamento)|assinar plano|subscribe)\b"),
    ("comprar", r"\b(?:compr(?:ar|e|a)|buy now|buy|adicionar ao carrinho|add to cart)\b"),
    ("transferir", r"\b(?:transferir|transfere|transferencia|pix|enviar dinheiro|send money)\b"),
    ("excluir", r"\b(?:exclu(?:ir|a|i)|apag(?:ar|a|ue)|delet(?:ar|a|e)|delete|remov(?:er|a|e)|remove|descartar|"
                r"discard|esvaziar lixeira|desinstal(?:ar|a|e)|uninstall|formatar)\b"),
    ("publicar", r"\b(?:public(?:ar|a|que)|post(?:ar|a|e)|post|publish|tweetar|tweet|compartilhar publicamente|share)\b"),
    ("enviar", r"\b(?:envi(?:ar|a|e)|mand(?:ar|a|e)|send|responder a todos|reply all|encaminh(?:ar|a|e)|forward|"
               r"submit|submeter)\b"),
    ("aceitar", r"\b(?:aceito|aceitar|concordo|i agree|accept terms|aceitar os termos|assinar documento|sign)\b"),
)
# Campo onde Enter manda o texto para alguem
_MESSAGE_FIELD = r"\b(?:mensagem|message|digite uma mensagem|type a message|comentario|comment|chat|resposta|reply|tweet|post)\b"
# O que nao e efeito, mesmo com palavra parecida: o botao de pesquisa "Enviar consulta" etc.
_HARMLESS = r"\b(?:pesquisa|pesquisar|search|buscar|busca|filtro|filtrar)\b"
# Confirmacao dita pela pessoa no proprio pedido
_CONFIRM = r"\b(?:confirmo|confirmado|pode (?:enviar|comprar|pagar|publicar|excluir|apagar|postar|mandar|transferir)|" \
           r"tenho certeza|sim,? (?:pode|envia|manda|compra|paga)|autorizo)\b"


def _norm(text: str) -> str:
    from core.lexicon import norm
    return norm(text or "")


def label_risk(label: str) -> Optional[str]:
    """Efeito de clicar em um elemento com este rotulo. None = nada sensivel."""
    text = _norm(label)
    if not text or re.search(_HARMLESS, text):
        return None
    for kind, pattern in KINDS:
        if re.search(pattern, text):
            return kind
    return None


def ui_risk(act: str, label: str = "", submit: bool = False, key: str = "") -> Optional[str]:
    """Efeito de uma acao de piloto: clique, digitar com Enter, ou tecla."""
    act = (act or "").lower()
    if act in ("click", "double_click", "vision_click"):
        return label_risk(label)
    if act == "type" and submit and re.search(_MESSAGE_FIELD, _norm(label)):
        return "enviar"
    if act == "press" and re.sub(r"\s", "", (key or "").lower()) in ("enter", "ctrl+enter", "return") \
            and re.search(_MESSAGE_FIELD, _norm(label)):
        return "enviar"
    return None


def step_risk(action: str, params: dict) -> Optional[str]:
    """Efeito de um passo do executor (fora dos pilotos)."""
    if action == "delete_file":
        return "excluir"
    if action in ("click", "vision_click", "uia_click"):
        return label_risk(str((params or {}).get("description") or (params or {}).get("element") or ""))
    return None


def confirmed(task: str) -> bool:
    return bool(re.search(_CONFIRM, _norm(task)))


def requested(kind: str, task: str) -> bool:
    """O pedido da pessoa fala desse efeito? Serve para medir, nunca substitui a confirmacao."""
    pattern = dict(KINDS).get(kind)
    return bool(pattern and re.search(pattern, _norm(task)))


def mode() -> str:
    try:
        from core.config import get_config
        value = str(get_config().get("execution.authorization", "shadow")).lower()
    except Exception:
        value = "shadow"
    return value if value in MODES else "shadow"


def _record(row: dict, path: Optional[Path] = None) -> None:
    target = path or LOG
    try:
        with _lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def authorize(kind: Optional[str], *, task: str, agent: str, action: str, label: str = "",
              current: Optional[str] = None, log_path: Optional[Path] = None) -> str:
    """-> '' para seguir, ou a pergunta de confirmacao (so no modo enforce)."""
    if not kind:
        return ""
    current = current or mode()
    if current == "off":
        return ""
    ok = confirmed(task)
    blocked = current == "enforce" and not ok
    _record({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": current, "agent": agent, "action": action,
             "kind": kind, "label": str(label)[:60], "requested": requested(kind, task), "confirmed": ok,
             "decision": "blocked" if blocked else ("allowed" if ok or current == "enforce" else "would_block")},
            log_path)
    if not blocked:
        return ""
    verb = {"pagar": "pagar", "comprar": "comprar", "transferir": "transferir", "excluir": "excluir",
            "publicar": "publicar", "enviar": "enviar", "aceitar": "aceitar"}[kind]
    where = f" ('{str(label)[:40]}')" if label else ""
    return f"Antes de {verb}{where} preciso da sua confirmação. Diga \"confirmo\" junto com o pedido para eu seguir."


class NeedsConfirmation(Exception):
    """Levantada pelo piloto quando a porta bloqueia: ele para antes de agir e pergunta."""


def report(path: Optional[Path] = None) -> dict:
    """Resumo do modo shadow: o que seria bloqueado e quantas vezes o pedido nem falava disso."""
    target = path or LOG
    rows = []
    try:
        rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError):
        pass
    by_kind: dict = {}
    for row in rows:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
    return {"total": len(rows), "would_block": sum(r["decision"] == "would_block" for r in rows),
            "blocked": sum(r["decision"] == "blocked" for r in rows),
            "not_requested": sum(not r["requested"] for r in rows), "by_kind": by_kind}


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=1))
