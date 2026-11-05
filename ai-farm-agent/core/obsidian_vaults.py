"""
Cofres do Obsidian: lista os registrados no computador e entende qual a pessoa pediu.

Abrir um cofre tem caminho direto (obsidian://open?vault=NOME). Procurar o cofre clicando na
tela leva a alucinacoes do piloto, entao o pedido e resolvido aqui, sem modelo. So abre cofre
que existe nesta lista; nome duvidoso vira pergunta.
"""

from __future__ import annotations

import difflib
import json
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from core.lexicon import _phonetic, norm

URI_PATTERN = r"^obsidian://open\?vault=[\w%.~-]+$"
_WORD = re.compile(r"\b(?:cofres?|vaults?)\b")
_OPEN = re.compile(r"\b(?:abr\w*|entr\w*|acess\w*|vai|ir|mostr\w*|troc\w*|mud\w*)\b")
_FILLER = {"o", "a", "os", "as", "um", "uma", "meu", "minha", "e", "ai", "agora", "por", "favor", "pra", "para", "mim",
           "no", "na", "nos", "nas", "em", "do", "da", "de", "dentro", "chamado", "chamada", "nome", "com", "ja",
           "aberto", "obsidian", "cofre", "cofres", "vault", "vaults", "isso", "esse", "essa", "que", "se", "voce",
           "pode", "quero", "queria", "preciso", "ver", "abre", "abra", "abrir", "abri", "entra", "entre", "entrar",
           "acessa", "acesse", "acessar", "vai", "ir", "mostra", "mostre", "mostrar", "troca", "troque", "trocar",
           "muda", "mude", "mudar"}
OPEN_SCORE, NAMED_SCORE, MARGIN = 0.8, 0.72, 0.08


def known_vaults(path: Optional[Path] = None) -> list:
    """Nomes dos cofres registrados no Obsidian que existem em disco. Falha vira lista vazia."""
    path = path or Path(os.path.expandvars(r"%APPDATA%")) / "obsidian" / "obsidian.json"
    try:
        vaults = json.loads(Path(path).read_text(encoding="utf-8")).get("vaults", {})
        names = [Path(v["path"]).name for v in vaults.values() if os.path.isdir(v.get("path", ""))]
    except (OSError, ValueError, AttributeError, KeyError, TypeError):
        return []
    return sorted(set(names), key=str.lower)


def vault_uri(name: str) -> str:
    return "obsidian://open?vault=" + quote(name, safe="")


def _plain(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", norm(text)).strip()


def _score(spoken: str, name: str) -> float:
    """Semelhanca do nome inteiro, por escrita e por som. Uma palavra so ('aurol') conta menos,
    porque costuma caber em varios cofres."""
    said, full = _plain(spoken), _plain(name)
    ratio = lambda a, b: difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    best = max(ratio(said, full), ratio(_phonetic(said), _phonetic(full)))
    if " " not in said:
        best = max(best, 0.85 * max((max(ratio(said, part), ratio(_phonetic(said), _phonetic(part)))
                                     for part in full.split()), default=0.0))
    return best


def _best(spoken: str, vaults: list) -> tuple:
    """-> (nome, nota) do melhor, ou ('', nota) se dois cofres empatam."""
    ranked = sorted(((_score(spoken, v), v) for v in vaults), reverse=True)
    if not ranked:
        return "", 0.0
    if len(ranked) > 1 and ranked[0][0] - ranked[1][0] < MARGIN:
        return "", ranked[0][0]
    return ranked[0][1], ranked[0][0]


def _spoken_name(text: str) -> str:
    return " ".join(w for w in _plain(text).split() if w not in _FILLER)


def _which(vaults: list) -> str:
    return "Qual cofre: " + ", ".join(vaults) + "?"


def parse_request(text: str, vaults: Optional[list] = None) -> Optional[dict]:
    """'abre o cofre Rede Aurora' -> {'open': nome} ou {'ask': pergunta}. None: nao e sobre cofre."""
    t = norm(text or "")
    if not _OPEN.search(t):
        return None
    vaults = known_vaults() if vaults is None else vaults
    if not vaults:
        return None
    asked_vault = bool(_WORD.search(t))
    spoken = _spoken_name(t)
    if not spoken:
        return {"ask": _which(vaults)} if asked_vault else None
    name, score = _best(spoken, vaults)
    if asked_vault:
        if name and score >= NAMED_SCORE:
            return {"open": name}
        if score >= NAMED_SCORE:
            return {"ask": _which(vaults)}
        return {"ask": f'Não achei esse cofre. {_which(vaults)}'}
    if name and score >= OPEN_SCORE:
        return {"open": name}
    return None


def mentioned_vault(text: str, vaults: Optional[list] = None) -> str:
    """'e... na rede aurora': a fala e so o nome de um cofre, sem pedir nada. -> nome ou ''."""
    vaults = known_vaults() if vaults is None else vaults
    spoken = _spoken_name(text or "")
    if not spoken or not vaults:
        return ""
    name, score = _best(spoken, vaults)
    return name if name and score >= OPEN_SCORE else ""
