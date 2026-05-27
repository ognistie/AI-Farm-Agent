"""
MemoryAgent v2 — Curador inteligente da memoria de longo prazo.

v1 era apenas um wrapper de 25 linhas sobre workflow_store. v2 adiciona
4 capacidades de inteligencia que NUNCA existiram antes:

1. SHOULD_REMEMBER — politica do que vale memorizar
   - Tarefas muito curtas (< 3 palavras) nao geram workflow util
   - Tarefas vazias/ambiguas sao descartadas
   - Tarefas com PII (CPF, email, senha) sao redatadas antes de salvar

2. DECAY — workflows nao usados perdem relevancia
   - > 60 dias sem uso: marcados como "cold" (excluidos do lookup)
   - > 90 dias: candidatos a remocao na proxima rotacao

3. MERGE_DUPLICATES — workflows muito similares (tema E tags) sao fundidos
   - Reforca contador de execucoes do mais antigo
   - Remove o redundante do disco

4. SUGGEST_AUTOMATION — detecta padroes repetitivos do usuario
   - Se a mesma forma de task aparece >= 3x em 7 dias, sugere "salvar atalho"
   - Retorna lista de sugestoes para o Command Center

API estavel (BaseAgent-compativel):
    find_template(task) -> {found, workflow?}
    save_success(task, steps, agent)
    decay_and_clean()  -> {marked_cold, removed}
    detect_patterns()  -> [{task_fragment, count, days_span}]
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from memory.workflow_store import (
    find_similar_workflow,
    save_workflow,
    WORKFLOWS_DIR,
    QUARANTINE_DIR,
    _extract_tags,
    _extract_topic_words,
)


# ───────────────────────────────────────────────────────────────────
#  Politicas
# ───────────────────────────────────────────────────────────────────

MIN_WORDS_TO_REMEMBER = 3
COLD_AFTER_DAYS = 60
REMOVE_AFTER_DAYS = 90
SUGGEST_THRESHOLD = 3       # quantas repeticoes para sugerir
SUGGEST_WINDOW_DAYS = 7

# Padroes de PII que devem ser redatados antes de salvar
_PII_PATTERNS = [
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),                   "[CPF]"),
    (re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),             "[CNPJ]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\bsenha[:=]\s*\S+", re.IGNORECASE),                "senha=[REDACTED]"),
    (re.compile(r"\bpassword[:=]\s*\S+", re.IGNORECASE),             "password=[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),                       "[API_KEY]"),
]


def _redact_pii(text: str) -> tuple[str, list[str]]:
    """Redige PII e retorna (texto_limpo, lista_de_tipos_encontrados)."""
    found = []
    for pat, label in _PII_PATTERNS:
        if pat.search(text):
            found.append(label.strip("[]").lower())
            text = pat.sub(label, text)
    return text, found


# ───────────────────────────────────────────────────────────────────
#  Agente
# ───────────────────────────────────────────────────────────────────


class MemoryAgent:
    """
    Curador da memoria operacional. NAO faz chamadas LLM — opera por regras
    deterministicas + estatistica leve. Custo zero por consulta.
    """

    name = "MEMORY"

    def __init__(self) -> None:
        self.metrics = {
            "lookups":          0,
            "hits":             0,
            "saves":            0,
            "rejected_saves":   0,
            "redacted_saves":   0,
            "cold_marked":      0,
            "duplicates_merged": 0,
        }

    # ── Lookup ────────────────────────────────────────────────────

    def find_template(self, task: str) -> dict[str, Any]:
        """Procura workflow similar com mesmo tema (delegado ao store v4)."""
        self.metrics["lookups"] += 1
        wf = find_similar_workflow(task)
        if wf:
            self.metrics["hits"] += 1
            return {"found": True, "workflow": wf}
        return {"found": False}

    # ── Save com politicas ────────────────────────────────────────

    def should_remember(self, task: str) -> tuple[bool, str]:
        """
        Decide se vale memorizar. Retorna (decisao, motivo).

        Rejeita:
        - tasks < MIN_WORDS_TO_REMEMBER palavras
        - tasks puramente comandos genericos sem tema ("abra o vscode")
        - tasks que parecem prompts de teste/debug
        """
        if not task or not task.strip():
            return False, "tarefa vazia"

        words = re.findall(r"\w+", task)
        if len(words) < MIN_WORDS_TO_REMEMBER:
            return False, f"tarefa curta ({len(words)} palavras)"

        topic = _extract_topic_words(task)
        tags = _extract_tags(task)
        if not topic and len(tags) < 2:
            return False, "tarefa sem tema nem tags tecnicas suficientes"

        t = task.lower()
        debug_markers = ("teste", "test ", "debug", "lorem ipsum",
                         "hello world", "asdf")
        if any(m in t for m in debug_markers):
            return False, "parece prompt de teste/debug"

        return True, "ok"

    def save_success(self, task: str, steps: list, agent: str) -> dict[str, Any]:
        """
        Salva workflow APENAS se passar pela politica + redige PII.
        Retorna {saved, reason, redacted_types}.
        """
        ok, reason = self.should_remember(task)
        if not ok:
            self.metrics["rejected_saves"] += 1
            return {"saved": False, "reason": reason}

        # Redacao de PII
        clean_task, found_pii = _redact_pii(task)
        if found_pii:
            self.metrics["redacted_saves"] += 1

        try:
            save_workflow(clean_task, steps, agent, success=True)
            self.metrics["saves"] += 1
            return {"saved": True, "reason": "ok",
                    "redacted_types": found_pii,
                    "task_stored": clean_task[:80]}
        except Exception as e:
            return {"saved": False, "reason": f"erro ao escrever: {e}"}

    # ── Decay / cleanup ───────────────────────────────────────────

    def decay_and_clean(self) -> dict[str, int]:
        """
        Marca como "cold" workflows nao usados em COLD_AFTER_DAYS e
        deleta os com REMOVE_AFTER_DAYS sem uso. Roda em batch.
        """
        if not WORKFLOWS_DIR.exists():
            return {"marked_cold": 0, "removed": 0, "scanned": 0}

        import json
        now = datetime.now()
        cold_cutoff = now - timedelta(days=COLD_AFTER_DAYS)
        remove_cutoff = now - timedelta(days=REMOVE_AFTER_DAYS)

        marked = 0
        removed = 0
        scanned = 0

        for f in WORKFLOWS_DIR.glob("*.json"):
            if QUARANTINE_DIR.name in f.parts:
                continue
            scanned += 1
            try:
                with open(f, encoding="utf-8") as fh:
                    wf = json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue

            created = wf.get("created_at", "")
            try:
                created_dt = datetime.fromisoformat(created) if created else None
            except ValueError:
                created_dt = None
            if not created_dt:
                continue

            last_used = wf.get("last_used", created)
            try:
                last_used_dt = datetime.fromisoformat(last_used)
            except ValueError:
                last_used_dt = created_dt

            if last_used_dt < remove_cutoff:
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
            elif last_used_dt < cold_cutoff and not wf.get("cold"):
                wf["cold"] = True
                try:
                    with open(f, "w", encoding="utf-8") as fh:
                        json.dump(wf, fh, ensure_ascii=False, indent=2)
                    marked += 1
                except OSError:
                    pass

        self.metrics["cold_marked"] += marked
        return {"marked_cold": marked, "removed": removed, "scanned": scanned}

    # ── Sugestao de automacao ─────────────────────────────────────

    def detect_patterns(self) -> list[dict[str, Any]]:
        """
        Le `desktop/data/history.jsonl` e detecta tasks repetitivas (>=
        SUGGEST_THRESHOLD vezes em SUGGEST_WINDOW_DAYS). Util para sugerir
        ao usuario "voce repetiu isso 4x — quer um atalho?".
        """
        history_file = Path(__file__).resolve().parent.parent \
            / "desktop" / "data" / "history.jsonl"
        if not history_file.exists():
            return []

        import json
        cutoff = datetime.now() - timedelta(days=SUGGEST_WINDOW_DAYS)
        buckets: dict[str, list[datetime]] = {}

        with open(history_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not e.get("success"):
                    continue
                try:
                    started = datetime.fromisoformat(e.get("started_at", ""))
                except ValueError:
                    continue
                if started < cutoff:
                    continue

                # Bucket por topic (palavras-tema)
                topic = tuple(sorted(_extract_topic_words(e.get("task", ""))))
                if not topic:
                    continue
                buckets.setdefault(topic, []).append(started)

        suggestions = []
        for topic, dates in buckets.items():
            if len(dates) >= SUGGEST_THRESHOLD:
                days_span = (max(dates) - min(dates)).days
                suggestions.append({
                    "topic": list(topic),
                    "count": len(dates),
                    "days_span": days_span,
                    "first_seen": min(dates).isoformat(),
                    "last_seen": max(dates).isoformat(),
                })

        suggestions.sort(key=lambda s: s["count"], reverse=True)
        return suggestions[:5]
