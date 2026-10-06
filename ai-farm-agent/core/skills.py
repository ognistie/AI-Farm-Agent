"""
Skills do catalogo AIWorkbench (vault: 30 Skills/*.md) aplicadas pelos agentes.

Cada nota de skill e um manual de uso:
  frontmatter  agentes: [CODE, DATA]       quem pode usar
               sempre_para: [CODE]          ativa em todo pedido desse agente
               ativa_quando: site, html...  palavras do pedido que ativam
  ## Como o agente aplica   - **Code Agent:** ...   (so as linhas do agente vao pro prompt)
  ## Regras / ## Conferir antes de concluir

skills_for(agente, pedido) escolhe as mais relevantes (palavras do pedido > "sempre"),
no maximo `limit`, e devolve o bloco compacto para o prompt + os nomes usados.
Como o resto do vault: referencia, nunca amplia permissoes.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

SKILLS_DIR = "30 Skills"
AGENT_LABEL = {"MAESTRO": "Maestro", "WEB": "Web Agent", "DESKTOP": "Desktop Agent", "CODE": "Code Agent",
               "DATA": "Data Agent", "FILE": "File Agent", "VISION": "Vision Agent", "MEMORY": "Memory Agent"}
MAX_CHARS_PER_SKILL = 800


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def _list(v: str) -> list[str]:
    return [x.strip().upper() for x in (v or "").strip("[] ").split(",") if x.strip()]


@dataclass
class Skill:
    name: str
    purpose: str
    agents: list
    always: list
    triggers: list
    apply: dict = field(default_factory=dict)      # agente -> [linhas]
    rules: list = field(default_factory=list)
    check: list = field(default_factory=list)

    def hits(self, task_n: str) -> int:
        """Quantas palavras de 'ativa_quando' aparecem no pedido (inicio de palavra: 'site' casa 'sites')."""
        return sum(1 for t in self.triggers if re.search(rf"(?<![\w]){re.escape(t)}", task_n))


def _section(md: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}[^\n]*\n(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def _bullets(text: str) -> list[str]:
    return [l[2:].strip() for l in text.splitlines() if l.startswith("- ") and l[2:].strip()]


def parse_skill(name: str, md: str) -> Optional[Skill]:
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n---", md, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    if fm.get("tipo") != "skill":
        return None
    purpose = re.search(r">\s*\[!skill\][^\n]*\n>\s*(.+)", md)
    apply: dict = {}
    by_label = {_norm(v): k for k, v in AGENT_LABEL.items()}
    for line in _bullets(_section(md, "Como o agente aplica")):
        lm = re.match(r"\*\*(.+?):\*\*\s*(.+)", line)
        if lm:
            ag = by_label.get(_norm(lm.group(1)), _norm(lm.group(1)).upper())
            apply.setdefault(ag, []).append(lm.group(2).strip())
    return Skill(name=name, purpose=(purpose.group(1).strip() if purpose else ""),
                 agents=_list(fm.get("agentes", "")), always=_list(fm.get("sempre_para", "")),
                 triggers=[_norm(t) for t in fm.get("ativa_quando", "").split(",") if len(_norm(t)) >= 3],
                 apply=apply, rules=_bullets(_section(md, "Regras")),
                 check=_bullets(_section(md, "Conferir antes de concluir")))


class SkillBook:
    def __init__(self, brain=None):
        if brain is None:
            from core.brain import get_brain
            brain = get_brain()
        self.brain = brain

    def all(self) -> list[Skill]:
        if not self.brain.enabled:
            return []
        base = self.brain.root / SKILLS_DIR
        out = []
        for f in sorted(base.glob("*.md")) if base.is_dir() else []:
            md = self.brain._read(f.relative_to(self.brain.root).as_posix())   # cache por mtime
            sk = parse_skill(f.stem, md) if md else None
            if sk:
                out.append(sk)
        return out

    def pick(self, agent: str, task: str, limit: int = 3) -> list[Skill]:
        """Skills do agente para este pedido: palavras do pedido pesam mais que 'sempre'."""
        agent = (agent or "").upper()
        t = _norm(task)
        scored = []
        for sk in self.all():
            if agent not in sk.agents or agent not in sk.apply:
                continue                       # sem linhas para este agente: nada util a dizer
            score = sk.hits(t) * 2 + (1 if agent in sk.always else 0)
            if score:
                scored.append((score, sk.name, sk))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [sk for _, _, sk in scored[:limit]]

    def render(self, agent: str, skills: list[Skill], compact: bool = False) -> str:
        agent = (agent or "").upper()
        parts = []
        for sk in skills:
            lines = [f"- {a}" for a in sk.apply.get(agent, [])[: 2 if compact else 4]]
            if not compact and sk.check:
                lines.append("Conferir antes de concluir: " + "; ".join(sk.check[:3]) + ".")
            # orcamento por skill com linhas INTEIRAS (frase cortada confunde o modelo)
            out, size = [f"[{sk.name}] {sk.purpose}"], len(sk.purpose) + len(sk.name) + 3
            for line in lines:
                if size + len(line) + 1 > MAX_CHARS_PER_SKILL:
                    break
                out.append(line)
                size += len(line) + 1
            parts.append("\n".join(out))
        return "\n\n".join(parts)


def skills_for(agent: str, task: str, limit: int = 3, compact: bool = False) -> tuple[str, list[str]]:
    """-> (bloco para o prompt, nomes das skills usadas). Falha nunca bloqueia o agente."""
    try:
        book = SkillBook()
        chosen = book.pick(agent, task, limit=1 if compact else limit)
        return book.render(agent, chosen, compact), [s.name for s in chosen]
    except Exception:
        return "", []
