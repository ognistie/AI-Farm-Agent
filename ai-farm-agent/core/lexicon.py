"""
Dicionario brasileiro de voz (lido do vault: 70 Dicionario/*.md).

Tabelas markdown: 1a coluna = jeitos de falar separados por ' / ',
2a coluna = o que significa / forma certa (+ colunas extras).

Usos:
- fix(text)            gaguejos + confusoes da transcricao marcadas como `auto`
                       (as marcadas `dica` so vao para o modelo: "ponto", "time",
                       "vê esse código" mudam de sentido conforme a frase)
- relevant(text)       linhas do dicionario que aparecem na fala, as mais
                       especificas primeiro (vao para o modelo)
- apps_in(text)        apps/sites citados -> [(nome certo, alvo)]
- sounds_like_app(t)   app com som parecido ("espotifai" ~ Spotify) — so pista
- table(note)          linhas de uma nota (ex.: paginas das Configuracoes)
O dicionario e relido quando algum arquivo muda (o usuario pode ensinar no Obsidian).
"""

from __future__ import annotations

import difflib
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DICT_DIR = "70 Dicionario"
APPS = "Apps e sites"
CONFUSIONS = "Confusoes de transcricao"
# Ordem de desempate no que vai para o modelo: o que corrige nomes primeiro
_NOTE_RANK = {CONFUSIONS: 0, APPS: 1, "Formas de pedir": 2, "Termos de computador": 3,
              "Configuracoes do Windows": 4, "Atalhos de teclado": 5, "Girias e expressoes": 6,
              "Referencias e contexto": 7, "Muletas e ruido": 8, "Numeros e tempo": 9}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w@.+\-/ ]+", " ", s)).strip()


def _phonetic(s: str) -> str:
    """Chave de som aproximada (pt-BR/ingles aportuguesado): 'spotify' ~ 'espotifai'."""
    t = norm(s).replace(" ", "")
    for a, b in (("ph", "f"), ("sh", "x"), ("ch", "x"), ("qu", "k"), ("ck", "k"), ("c", "k"), ("w", "u"),
                 ("y", "i"), ("z", "s"), ("ou", "o"), ("ai", "i"), ("ei", "i"), ("h", ""), ("e", "i")):
        t = t.replace(a, b)
    t = re.sub(r"^i(?=s[^aeiou])", "", t)          # "espoti" -> "spoti"
    return re.sub(r"(.)\1+", r"\1", t)


@dataclass
class Entry:
    variants: list            # normalizadas
    meaning: str
    note: str
    extra: list = field(default_factory=list)
    raw: str = ""

    @property
    def auto(self) -> bool:
        """Confusao segura para corrigir sem o modelo (coluna 'Corrigir' = auto)."""
        return self.note == CONFUSIONS and len(self.extra) > 1 and norm(self.extra[1]).startswith("auto")


def _parse_tables(text: str, note: str) -> list[Entry]:
    out = []
    for line in text.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or norm(cells[0]) in ("fala", "ouvido", "situacao", "atalho"):
            continue
        variants = [re.sub(r"\(.*?\)", "", v) for v in re.split(r"\s+/\s+", cells[0])]
        variants = [norm(v).strip(" '\"") for v in variants]
        variants = [v for v in variants if len(v) >= 2]
        if variants:
            out.append(Entry(variants, cells[1], note, cells[2:], cells[0]))
    return out


class Lexicon:
    def __init__(self, vault: Optional[Path] = None):
        if vault is None:
            from core.brain import get_brain
            vault = get_brain().root
        self.dir = Path(vault) / DICT_DIR
        self._lock = threading.Lock()
        self._stamp = None
        self.entries: list[Entry] = []

    def _load(self) -> None:
        files = sorted(self.dir.glob("*.md")) if self.dir.is_dir() else []
        stamp = tuple((f.name, f.stat().st_mtime) for f in files)
        if stamp == self._stamp:
            return
        entries = []
        for f in files:
            if f.stem == "Dicionario de voz":
                continue
            try:
                entries += _parse_tables(f.read_text(encoding="utf-8"), f.stem)
            except OSError:
                continue
        self.entries, self._stamp = entries, stamp

    def _all(self) -> list[Entry]:
        with self._lock:
            self._load()
            return self.entries

    def table(self, note: str) -> list[Entry]:
        return [e for e in self._all() if e.note == note]

    # ── usos ──────────────────────────────────────────────────────
    @staticmethod
    def _has(text_n: str, variant: str) -> bool:
        return re.search(rf"(?<![\w]){re.escape(variant)}(?![\w])", text_n) is not None

    def apps_in(self, text: str) -> list[tuple[str, str]]:
        """Apps/sites citados na fala (o mais longo vence: 'google maps' antes de 'google')."""
        t = norm(text)
        found, spans = [], []
        cands = [(v, e) for e in self.table(APPS) for v in e.variants]
        for v, e in sorted(cands, key=lambda x: -len(x[0])):
            m = re.search(rf"(?<![\w]){re.escape(v)}(?![\w])", t)
            if not m or any(a <= m.start() < b for a, b in spans):
                continue
            spans.append((m.start(), m.end()))
            alvo = e.extra[1] if len(e.extra) > 1 else ""
            if (e.meaning, alvo) not in found:
                found.append((e.meaning, alvo))
        return found

    def app_entry(self, name: str) -> Optional[Entry]:
        t = norm(name)
        for e in self.table(APPS):
            if t == norm(e.meaning) or t in e.variants:
                return e
        return None

    def app_key(self, name: str) -> str:
        """Chave unica do app ('settings', 'configurações', 'Configurações do Windows' -> 'configuracoes').
        Sem correspondencia no dicionario devolve o nome normalizado."""
        n = norm(name or "")
        if not n:
            return ""
        for meaning, alvo in self.apps_in(n):
            if alvo.startswith("app:"):
                return alvo.split(":", 1)[1]
            if alvo == "web":
                return "web"
        return n

    def is_app_name(self, text: str) -> bool:
        """O texto inteiro e um jeito de chamar um app/site ('o youtube', 'vs code')?"""
        t = re.sub(r"^(?:o|a|os|as|meu|minha)\s+", "", norm(text)).strip()
        return any(t == re.sub(r"^(?:o|a|os|as|meu|minha)\s+", "", v) or t == norm(e.meaning)
                   for e in self.table(APPS) for v in e.variants)

    def sounds_like_app(self, text: str, min_ratio: float = 0.84) -> Optional[tuple[str, str, float]]:
        """App cujo nome SOA como algum trecho da fala e que nao foi citado literalmente.
        -> (nome certo, trecho ouvido, semelhanca). So pista para o modelo / palpite da pergunta."""
        words = norm(text).split()
        if not words or self.apps_in(text):
            return None
        best = None
        cands = [(e.meaning, _phonetic(v)) for e in self.table(APPS) for v in e.variants if len(v) >= 4]
        for n in (3, 2, 1):
            for i in range(len(words) - n + 1):
                chunk = " ".join(words[i:i + n])
                if len(chunk) < 4:
                    continue
                key = _phonetic(chunk)
                for meaning, vk in cands:
                    r = difflib.SequenceMatcher(None, key, vk).ratio()
                    if r >= min_ratio and (best is None or r > best[2]):
                        best = (meaning, chunk, round(r, 2))
        return best

    def fix(self, text: str) -> str:
        """Texto ouvido -> gaguejos removidos e confusoes SEGURAS corrigidas (coluna Corrigir = auto)."""
        t = norm(text)
        t = re.sub(r"\b(\w+)(?:[ ,]+\1\b)+", r"\1", t)            # "meu meu meu" -> "meu"
        for e in self._all():
            if not e.auto:
                continue
            for v in sorted(e.variants, key=len, reverse=True):
                if len(v) >= 4 and self._has(t, v):
                    t = re.sub(rf"(?<![\w]){re.escape(v)}(?![\w])", e.meaning, t)
        return re.sub(r"\s+", " ", t).strip()

    def relevant(self, text: str, limit: int = 24) -> list[str]:
        """Linhas do dicionario cujas variacoes aparecem na fala, as mais especificas primeiro.
        Variacoes de 2 letras so contam para apps ('g1'); muletas curtas nao inundam o prompt."""
        t = norm(text)
        scored = []
        for e in self._all():
            hit = max((len(v) for v in e.variants
                       if (len(v) >= 3 or e.note == APPS) and self._has(t, v)), default=0)
            if hit:
                scored.append((-hit, _NOTE_RANK.get(e.note, 10), e))
        scored.sort(key=lambda x: (x[0], x[1]))
        out = []
        for _, _, e in scored[:limit]:
            hint = e.extra[0] if e.extra and e.extra[0] and e.note != APPS else ""
            if e.note == APPS and len(e.extra) > 1:
                hint = e.extra[1] + (f"; abrir: {e.extra[2]}" if len(e.extra) > 2 and e.extra[2] else "")
            out.append(f"- [{e.note}] {e.raw} → {e.meaning}" + (f" ({hint})" if hint else ""))
        return out

    def size(self) -> int:
        return sum(len(e.variants) for e in self._all())


_instance: Optional[Lexicon] = None


def get_lexicon() -> Lexicon:
    global _instance
    if _instance is None:
        _instance = Lexicon()
    return _instance
