"""
Brain — segundo cerebro no Obsidian (vault AI-Farm-agents).

O vault e a fonte de DIRECAO dos agentes (playbooks, politicas, tarefas de
referencia) e o registro do que aconteceu (planos propostos, validacao do
Maestro, execucoes com sucesso e com falha).

Regras (vindas do Maestro do hackathon_openai_sp):
- Conteudo do vault e DADO de referencia, nunca instrucao que amplia
  permissoes. As politicas que bloqueiam vivem em codigo (plan_validator).
- Escrita restrita ao vault, sem segredos (PII redigida), append-only no
  registro de execucoes.
- Falha do vault nunca bloqueia uma tarefa: o app continua sem ele.

Estrutura usada (ver AI-Farm-agents/00 Maestro/Como usar o cerebro.md):
    10 Agentes/<Agente>/<Agente> Agent.md   secao "## Regras de execucao"
    30 Tarefas de referencia/*.md           secao "## Caminho"
    40 Execucoes/Planos|Sucesso|Falhas/     escrito pelo app
"""

from __future__ import annotations

import logging
import re
import threading
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("brain")

AGENT_FOLDERS = {
    "MAESTRO": ("00 Maestro", "Maestro"),
    "WEB": ("10 Agentes/Web", "Web Agent"),
    "DESKTOP": ("10 Agentes/Desktop", "Desktop Agent"),
    "CODE": ("10 Agentes/Code", "Code Agent"),
    "DATA": ("10 Agentes/Data", "Data Agent"),
    "FILE": ("10 Agentes/File", "File Agent"),
}

GUIDE_MAX_CHARS = 1200
REFERENCE_MAX_CHARS = 450


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _tokens(text: str) -> set[str]:
    stop = {"o", "a", "os", "as", "de", "do", "da", "e", "em", "no", "na", "um", "uma",
            "para", "por", "com", "que", "abra", "abrir", "sobre"}
    words = re.findall(r"[a-z0-9]+", _strip_accents((text or "").lower()))
    return {w for w in words if len(w) > 2 and w not in stop}


def _slug(text: str, limit: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", _strip_accents(text or "")).strip()
    s = re.sub(r"\s+", " ", s)[:limit].strip()
    return s or "tarefa"


def _section(md: str, title: str) -> str:
    """Conteudo de '## <title>' ate o proximo '## ' (titulo com ou sem acento)."""
    want = _strip_accents(title).lower()
    for m in re.finditer(r"^##\s+(.+?)\s*$(.*?)(?=^##\s|\Z)", md, re.MULTILINE | re.DOTALL):
        if _strip_accents(m.group(1)).lower().strip() == want:
            return m.group(2).strip()
    return ""


def _frontmatter(md: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", md, re.DOTALL)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip("[]")
    return out


def _redact(text: str) -> str:
    try:
        from agents.memory_agent import _redact_pii
        return _redact_pii(text or "")[0]
    except Exception:
        return text or ""


class Brain:
    def __init__(self, vault_path: Optional[str] = None) -> None:
        if vault_path is None:
            from core.config import get_config
            cfg = get_config()
            vault_path = cfg.get("brain.vault_path", "../AI-Farm-agents")
            enabled = cfg.get("brain.enabled", True)
        else:
            enabled = True
        root = Path(vault_path)
        if not root.is_absolute():
            root = Path(__file__).resolve().parent.parent / root
        # resolve() sempre: a checagem "dentro do vault" compara caminhos
        # resolvidos (no Windows, GUILHE~1 vs Guilherme sao o mesmo lugar).
        self.root = root.resolve()
        self.enabled = bool(enabled) and self.root.is_dir()
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, str]] = {}
        if not self.enabled:
            logger.info(f"Segundo cerebro indisponivel em {root}")

    # ── IO seguro ─────────────────────────────────────────────────────
    def _path(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError(f"caminho fora do vault: {rel}")
        return p

    def _read(self, rel: str) -> str:
        try:
            p = self._path(rel)
            mtime = p.stat().st_mtime
            cached = self._cache.get(rel)
            if cached and cached[0] == mtime:
                return cached[1]
            text = p.read_text(encoding="utf-8")
            self._cache[rel] = (mtime, text)
            return text
        except (OSError, ValueError):
            return ""

    def _write(self, rel: str, content: str) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            p = self._path(rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                p.write_text(content, encoding="utf-8")
            return rel
        except (OSError, ValueError) as e:
            logger.warning(f"Falha ao escrever no cerebro ({rel}): {e}")
            return None

    # ── Leitura: direcao para os agentes ──────────────────────────────
    def agent_guide(self, agent: str) -> str:
        """Secao 'Regras de execucao' da nota do agente (curta, para o prompt)."""
        if not self.enabled:
            return ""
        folder, name = AGENT_FOLDERS.get((agent or "").upper(), (None, None))
        if not folder:
            return ""
        rules = _section(self._read(f"{folder}/{name}.md"), "Regras de execucao")
        return rules[:GUIDE_MAX_CHARS]

    def find_references(self, task: str, k: int = 2) -> list[dict]:
        """Tarefas de referencia parecidas (curadas + sucessos registrados)."""
        if not self.enabled:
            return []
        want = _tokens(task)
        if not want:
            return []
        scored = []
        for folder in ("30 Tarefas de referencia", "10 Agentes", "40 Execucoes/Sucesso"):
            base = self.root / folder
            if not base.is_dir():
                continue
            for f in base.rglob("*.md"):
                rel = f.relative_to(self.root).as_posix()
                md = self._read(rel)
                fm = _frontmatter(md)
                have = _tokens(f.stem + " " + fm.get("keywords", "") + " " + fm.get("tarefa", ""))
                if not have:
                    continue
                score = len(want & have) / len(want | have)
                if score >= 0.2:
                    path = _section(md, "Caminho") or _section(md, "Plano executado")
                    scored.append((score, {"title": f.stem, "agent": fm.get("agente", ""),
                                           "path": path[:REFERENCE_MAX_CHARS], "note": rel}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ref for _, ref in scored[:k]]

    # ── Escrita: planos e execucoes ───────────────────────────────────
    def write_plan(self, task: str, plan: dict) -> Optional[str]:
        """Plano do Maestro, proposto e validado, antes de executar."""
        if not self.enabled:
            return None
        now = datetime.now()
        rel = f"40 Execucoes/Planos/{now:%Y-%m-%d %H%M%S} - {_slug(task)}.md"
        val = plan.get("validation") or {}
        subs = plan.get("subtasks") or []
        agents = sorted({(s.get("agent") or "").upper() for s in subs if s.get("agent")})
        lines = [
            "---",
            "tipo: plano-de-acao",
            f"status: {'aprovado' if val.get('approved', True) else 'reprovado'}",
            f"data: {now.isoformat(timespec='seconds')}",
            f"agentes: [{', '.join(agents)}]",
            "tags: [plano, execucao]",
            "cssclasses: [agent-maestro]",
            "---",
            f"# Plano — {_redact(task)[:120]}",
            "",
            "> [!info] Proposto pelo [[Maestro]] e validado pelas [[Politicas de aceite]] antes de executar.",
            "",
            "## Pedido",
            _redact(task),
            "",
            "## Subtarefas (Maestro)",
        ]
        for i, s in enumerate(subs, 1):
            ag = (s.get("agent") or "").upper()
            link = AGENT_FOLDERS.get(ag, (None, ag))[1]
            lines.append(f"{i}. [[{link}]] — {_redact(s.get('task', ''))}")
        lines += ["", "## Validacao do Maestro",
                  "- Resultado: " + ("aprovado" if val.get("approved", True) else "**reprovado**")]
        for v in val.get("violations", []):
            lines.append(f"- [[{v['policy']}]] {v['msg']}")
        lines += ["", "## Planos dos agentes", ""]
        return self._write(rel, "\n".join(lines) + "\n")

    def append_agent_plan(self, rel: Optional[str], agent: str, subtask: dict,
                          steps: list, validation, subagents: Optional[list] = None) -> None:
        """Cada agente 'sobe' seus passos na nota do plano; o Maestro valida."""
        if not rel or not self.enabled:
            return
        link = AGENT_FOLDERS.get((agent or "").upper(), (None, agent))[1]
        out = [f"### [[{link}]] — {_redact(subtask.get('task', ''))[:100]}"]
        if subagents:
            out.append("> [!metric] Subagentes")
            for t in subagents:
                mark = "✅" if t.ok else "❌"
                out.append(f"> - {mark} [[{t.name}]] ({t.role}) — {_redact(t.summary)[:140]}")
            out.append("")
        for s in steps[:40]:
            desc = s.get("description") or s.get("action", "")
            out.append(f"- `{s.get('action', '')}` {_redact(str(desc))[:120]}")
        out.append("- Validacao: " + ("aprovado" if validation.approved
                                      else "**reprovado** — " + validation.summary()))
        self._append(rel, "\n".join(out) + "\n\n")

    def finish(self, rel: Optional[str], entry: dict, records: list) -> Optional[str]:
        """Resultado final: atualiza o plano e cria a nota em Sucesso ou Falhas."""
        if not self.enabled or entry.get("dry_run"):
            return None
        ok = bool(entry.get("success"))
        if rel:
            md = self._read(rel)
            if md:
                md = re.sub(r"^status: .*$", f"status: {'executado' if ok else 'falhou'}",
                            md, count=1, flags=re.MULTILINE)
                self._write(rel, md)
        task = entry.get("task", "")
        subs = entry.get("subtasks") or []
        agents = sorted({(s.get("agent") or "").upper() for s in subs if s.get("agent")})
        folder = "Sucesso" if ok else "Falhas"
        started = entry.get("started_at", "")[:19].replace("T", " ").replace(":", "")
        note = f"40 Execucoes/{folder}/{started} - {_slug(task)}.md"
        m = entry.get("metrics") or {}
        lines = [
            "---",
            f"tipo: execucao-{'sucesso' if ok else 'falha'}",
            f"tarefa: {_redact(task)[:200]}",
            f"agente: {', '.join(agents)}",
            f"keywords: {' '.join(sorted(_tokens(task)))}",
            f"data: {entry.get('started_at', '')}",
            f"duracao_ms: {entry.get('duration_ms', 0)}",
            f"custo_usd: {m.get('cost_usd', 0)}",
            f"status: {'sucesso' if ok else 'falha'}",
            f"tags: [execucao, {'sucesso' if ok else 'falha'}]",
            f"cssclasses: [{'exec-ok' if ok else 'exec-fail'}]",
            "---",
            f"# {'✅' if ok else '❌'} {_redact(task)[:120]}",
            "",
            "Agentes: " + ", ".join(f"[[{AGENT_FOLDERS.get(a, (None, a))[1]}]]" for a in agents),
        ]
        if rel:
            lines.append(f"Plano: [[{Path(rel).stem}]]")
        if not ok and entry.get("error"):
            lines += ["", "## Erro", _redact(str(entry.get("error")))[:600]]
        lines += ["", "## Plano executado"]
        for r in records[:40]:
            mark = "✓" if r.get("success") else "✗"
            res = str(r.get("result", "")).replace("\n", " ")[:100]
            lines.append(f"- {mark} `{r.get('action', '')}` {_redact(res)}")
        if ok:
            if records:
                how = "; ".join(str(r.get("action", "")) for r in records[:12])
            else:
                how = "; ".join(f"{s.get('agent', '')}: {_redact(s.get('task', ''))}" for s in subs)
            lines += ["", "## Caminho", " → ".join(agents) + " — " + how]
        written = self._write(note, "\n".join(lines) + "\n")
        if written:
            self._log_daily(entry, Path(written).stem, ok, agents)
        return written

    def _log_daily(self, entry: dict, note_stem: str, ok: bool, agents: list) -> None:
        """Diario de operacoes: uma linha por execucao em 50 Diario/AAAA-MM-DD."""
        day = (entry.get("started_at") or datetime.now().isoformat())[:10]
        hour = (entry.get("started_at") or "")[11:16]
        rel = f"50 Diario/{day}.md"
        if not self._read(rel):
            self._write(rel, "\n".join([
                "---",
                "tipo: diario",
                f"data: {day}",
                "tags: [diario]",
                "cssclasses: [agent-maestro]",
                "---",
                f"# 📓 {day}",
                "",
                "Registro automático das execuções do dia. ← [[Início]] · [[Maestro]]",
                "",
                "## Execuções",
                "",
            ]) + "\n")
        mark = "✅" if ok else "❌"
        who = ", ".join(agents) or "—"
        self._append(rel, f"- {hour} {mark} [[{note_stem}]] · {who}\n")

    def _append(self, rel: str, text: str) -> None:
        try:
            p = self._path(rel)
            with self._lock, open(p, "a", encoding="utf-8") as fh:
                fh.write(text)
        except (OSError, ValueError) as e:
            logger.warning(f"Falha ao anexar no cerebro ({rel}): {e}")


_instance: Optional[Brain] = None


def get_brain() -> Brain:
    global _instance
    if _instance is None:
        _instance = Brain()
    return _instance
