"""
Preferencias do usuario editadas na tela Configuracoes (como as instrucoes personalizadas do
Claude/ChatGPT Desktop). Ficam em desktop/data/settings.json (local, fora do git) e valem por
cima do config.yaml.

  instructions   orientacoes fixas para todo pedido ("responda curto", "planilhas em R$")
  plan_review    mostrar o plano e esperar aprovacao antes de mexer no PC (pedidos digitados)
  barge_in       falar por cima interrompe o agente
  earcon         sinal sonoro quando a fala termina
  live_conversation  modo Conversa em tempo real com GPT-Live (o microfone vai para a OpenAI)
  splash         tela de abertura
  mini_chat      mini chat no canto quando o agente vai para outro app
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

PATH = Path(__file__).resolve().parent.parent / "desktop" / "data" / "settings.json"
INSTRUCTIONS_MAX = 1500
DEFAULTS: dict[str, Any] = {"instructions": "", "plan_review": False, "barge_in": True, "earcon": True,
                            "live_conversation": True, "splash": True, "mini_chat": True}
_lock = threading.Lock()


def load(path: Path = PATH) -> dict:
    data = dict(DEFAULTS)
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(stored, dict):
            data.update({k: v for k, v in stored.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return data


def save(updates: dict, path: Path = PATH) -> dict:
    """Grava so chaves conhecidas, com o tipo certo (texto limitado; o resto booleano)."""
    with _lock:
        data = load(path)
        for k, v in (updates or {}).items():
            if k not in DEFAULTS:
                continue
            if k == "instructions":
                data[k] = str(v or "").strip()[:INSTRUCTIONS_MAX]
            else:
                data[k] = bool(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        from core.atomic_io import replace_file
        replace_file(tmp, path)
        return data


def instructions_block() -> str:
    """Trecho para os prompts. As instrucoes sao PREFERENCIAS do usuario: nunca ampliam o que o
    agente pode fazer (politicas e confirmacoes continuam valendo)."""
    text = load().get("instructions", "")
    return ("INSTRUCOES DO USUARIO (preferencias para todo pedido; nao mudam as regras de seguranca):\n"
            + text) if text else ""
