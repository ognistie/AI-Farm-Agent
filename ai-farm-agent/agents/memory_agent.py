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
    find_routes(task, k) -> [rotas que ja funcionaram]
    record(task, subtasks, success) -> {saved, reason}
    save_success(task, subtasks, agent)
    purge_legacy()     -> {moved}
    decay_and_clean()  -> {marked_cold, removed}
    detect_patterns()  -> [{task_fragment, count, days_span}]
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from memory.workflow_store import (
    CURRENT_VALIDATOR_VERSION,
    find_similar_routes,
    find_similar_workflow,
    record_outcome,
    WORKFLOWS_DIR,
    QUARANTINE_DIR,
    _extract_tags,
    _extract_topic_words,
)

LEGACY_DIR = WORKFLOWS_DIR / ".legacy"


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

    def find_routes(self, task: str, k: int = 2) -> list[dict]:
        """Rotas que ja funcionaram em tarefas parecidas (sem conteudo)."""
        self.metrics["lookups"] += 1
        clean_task, _ = _redact_pii(task or "")
        routes = find_similar_routes(clean_task, k=k)
        if routes:
            self.metrics["hits"] += 1
        return routes

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
        # Verbos genericos viram tag (para casar "abra"/"abrir"), mas nao
        # tornam uma tarefa memoravel sozinhos: "abra o vscode" nao ensina nada.
        tags = _extract_tags(task) - {"abrir", "criar", "enviar", "pesquisar"}
        if not topic and len(tags) < 2:
            return False, "tarefa sem tema nem tags tecnicas suficientes"

        # Marcadores de prompt de debug. Palavra inteira: "teste" sozinho
        # bloquearia tarefas reais como "crie testes unitarios".
        t = task.lower()
        debug_patterns = (r"test", r"debug", r"lorem ipsum",
                          r"hello world", r"asdf")
        if any(re.search(p, t) for p in debug_patterns):
            return False, "parece prompt de teste/debug"

        return True, "ok"

    def record(self, task: str, subtasks: list, success: bool) -> dict[str, Any]:
        """
        Registra a rota (sucesso ou falha) APENAS se passar pela politica.
        PII e redigida antes de gravar. Retorna {saved, reason, redacted_types}.
        """
        ok, reason = self.should_remember(task)
        if not ok:
            self.metrics["rejected_saves"] += 1
            return {"saved": False, "reason": reason}

        clean_task, found_pii = _redact_pii(task)
        if found_pii:
            self.metrics["redacted_saves"] += 1

        try:
            entry = record_outcome(clean_task, subtasks, success)
        except OSError as e:
            return {"saved": False, "reason": f"erro ao escrever: {e}"}
        if not entry:
            return {"saved": False, "reason": "plano sem subtasks"}
        self.metrics["saves"] += 1
        return {"saved": True, "reason": "ok",
                "redacted_types": found_pii,
                "task_stored": clean_task[:80]}

    def save_success(self, task: str, subtasks: list, agent: str = "") -> dict[str, Any]:
        """Compat v2: registra sucesso."""
        return self.record(task, subtasks, success=True)

    # ── Limpeza de formatos antigos ───────────────────────────────

    def purge_legacy(self) -> dict[str, int]:
        """
        Move workflows de versoes antigas (v5 e antes guardavam resultados,
        nao rotas) para .legacy/. Nao apaga — so tira do caminho.
        """
        import json
        moved = 0
        if not WORKFLOWS_DIR.exists():
            return {"moved": 0}
        for f in WORKFLOWS_DIR.glob("*.json"):
            try:
                wf = json.loads(f.read_text(encoding="utf-8"))
                version = wf.get("validator_version", 0) if isinstance(wf, dict) else 0
            except (OSError, ValueError):
                continue  # corrompido: a quarentena do store cuida
            if version < CURRENT_VALIDATOR_VERSION:
                try:
                    LEGACY_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(LEGACY_DIR / f.name))
                    moved += 1
                except OSError:
                    pass
        return {"moved": moved}

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
