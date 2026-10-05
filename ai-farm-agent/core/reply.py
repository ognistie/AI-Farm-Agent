"""
A resposta do assistente ao fim de cada pedido (texto na tela e, na voz, falada).

Como numa conversa com uma IA: em vez de so "Tarefa concluida", uma frase
natural que conta o que foi feito e o dado pedido ("O dolar ta R$ 5,12.").
- speak=True so quando acrescenta algo (dado lido ou falha): na voz a
  confirmacao ja foi dita na hora ("Beleza, abrindo o Excel"), nao repetir.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

SYSTEM = """Você é o assistente de um agente que usa o PC do usuário. Escreva a resposta ao usuário
depois de um pedido executado (1 a 2 frases, até ~30 palavras).
- Conte o que foi feito e, se o pedido era saber algo, o DADO lido primeiro (só o que está no resultado).
- Se falhou: diga o que deu errado em palavras simples e uma sugestão do que tentar.
- Se o resultado tem uma lista (vídeos, produtos, arquivos), cite no máximo 2 itens e ofereça o próximo passo.
- Não leia URLs, caminhos, ids nem nomes técnicos de passos.
JEITO DE FALAR:
{style}
Responda só a frase."""


def _clean(text: str, limit: int = 700) -> str:
    from core.voice.tts import clean_for_speech
    return clean_for_speech(text or "", limit)


def informative(summary: str, success: bool) -> bool:
    s = _clean(summary)
    return (not success) or bool(re.search(r"\d", s)) or len(s) > 70


def _default_llm(system: str, user: str) -> str:
    from core.ai_client import get_client
    from core.config import get_config
    cfg = get_config()
    return get_client().message(model=cfg.get_model("resolver"), system=system, user_content=user,
                                max_tokens=800, effort="low", agent="REPLY")


def compose(said: str, task: str, summary: str, success: bool, error: str = "",
            recent: Optional[list] = None, llm: Optional[Callable[[str, str], str]] = None) -> dict:
    """-> {"text": frase para a tela, "speak": falar em voz alta?}"""
    s = _clean(summary)
    user = (f"O USUÁRIO DISSE: {said}\nENTENDIDO COMO: {task}\nDEU CERTO: {'sim' if success else 'não'}\n"
            f"RESULTADO: {s or error or '(sem detalhes)'}\n"
            + ("FALAS RECENTES:\n" + "\n".join(f"- {r}" for r in (recent or [])[-4:]) + "\n" if recent else "")
            + "Responda só a frase.")
    try:
        from core.voice.persona import get_persona
        system = SYSTEM.replace("{style}", get_persona().style())
        text = (llm or _default_llm)(system, user).strip().strip('"')
    except Exception:
        text = ""
    if not text:
        text = "Feito." if success else ("Não consegui concluir. " + (error or "")[:120]).strip()
    return {"text": text, "speak": informative(summary, success)}
