"""
Onde um pedido continua: decisao unica usada pelo Controller (app) e pela
avaliacao de conversas (scripts/eval_conversations.py), para as duas nunca
divergirem.

1. O resolvedor apontou um alvo aberto (aba, janela, projeto) e o agente e o
   dono dele (web->WEB, app->DESKTOP, code->CODE, folder->FILE).
2. Senao, o Desktop recebeu um app que JA esta aberto nesta conversa: continua
   nele em vez de reabrir (o Excel "voltava" para a tela inicial a cada pedido),
   a menos que o usuario peca outro/novo.
"""

from __future__ import annotations

import re
from typing import Optional

WANTS_NEW = re.compile(r"\b(outr[oa]|nov[oa]|nova janela|mais um|mais uma|do zero)\b")


def continue_target_for(session, agent: str, params: dict, target: Optional[str],
                        task: str, already_used: bool = False) -> tuple[Optional[dict], str]:
    """-> (alvo, motivo) ou (None, '')."""
    if params.get("continue"):
        return None, ""
    if target and not already_used and agent == session.agent_for(target):
        tgt = session.target(target)
        if tgt:
            return tgt, "resolver"
    if agent == "DESKTOP" and params.get("app"):
        from core.lexicon import get_lexicon
        key = get_lexicon().app_key(params["app"])
        tgt = session.target(f"app:{key}") if key else None
        if tgt and not WANTS_NEW.search((task or "").lower()):
            return tgt, "app já aberto"
    return None, ""
