"""
Evolution Engine — Aprendizado contínuo do AI Farm Agent.

Cada tarefa executada alimenta o sistema:
1. EXECUTAR → agente faz a tarefa
2. OBSERVAR → mede sucesso/falha
3. MEMORIZAR → salva workflow bem-sucedido
4. ADAPTAR → próxima tarefa similar reusa sem LLM

Quando um workflow tem success_rate > 0.8 E foi executado 3+ vezes,
vira um "template consagrado" e é usado direto (custo $0, velocidade instantânea).

Arquivos gerados:
- memory/evolution/workflows.json       — workflows aprendidos
- memory/evolution/failures.json        — falhas registradas para evitar repetir
- memory/evolution/stats.json           — estatísticas gerais
"""

import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path


MEMORY_DIR = Path("memory/evolution")
WORKFLOWS_FILE = MEMORY_DIR / "workflows.json"
FAILURES_FILE = MEMORY_DIR / "failures.json"
STATS_FILE = MEMORY_DIR / "stats.json"

# Thresholds
MIN_EXECUTIONS_TO_TRUST = 3    # Workflow precisa ser executado 3x para ser confiável
MIN_SUCCESS_RATE = 0.8         # Taxa mínima de sucesso para usar direto
SIMILARITY_THRESHOLD = 0.6     # Similaridade mínima para considerar mesma tarefa
MAX_WORKFLOWS = 500            # Limite de workflows armazenados (descarta os piores)


def _ensure_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def _save_json(path, data):
    _ensure_dir()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"  [Evolution] Erro ao salvar: {e}")
        return False


def _task_hash(task):
    """Gera hash único da tarefa (para identificar duplicatas)."""
    return hashlib.md5(task.lower().strip().encode()).hexdigest()[:12]


def _tokenize(text):
    """Extrai tokens relevantes da tarefa para cálculo de similaridade."""
    import re
    text = text.lower()
    # Remove stopwords básicas
    stopwords = {"o", "a", "e", "de", "da", "do", "para", "com", "em", "no", "na",
                 "um", "uma", "os", "as", "que", "por", "pelo", "pela", "me", "meu",
                 "minha", "seu", "sua", "ao", "aos", "às", "à"}
    tokens = re.findall(r'\w+', text)
    return set(t for t in tokens if t not in stopwords and len(t) > 2)


def _similarity(task_a, task_b):
    """Calcula similaridade Jaccard entre duas tarefas."""
    tokens_a = _tokenize(task_a)
    tokens_b = _tokenize(task_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


# ═══════════════════════════════════════════════════════════
#  EvolutionEngine — API principal
# ═══════════════════════════════════════════════════════════


class EvolutionEngine:
    def __init__(self):
        _ensure_dir()
        self.workflows = _load_json(WORKFLOWS_FILE, [])
        self.failures = _load_json(FAILURES_FILE, [])
        self.stats = _load_json(STATS_FILE, {
            "total_executions": 0,
            "total_successes": 0,
            "total_failures": 0,
            "cache_hits": 0,       # Quantas vezes usou workflow aprendido
            "api_calls_saved": 0,  # Chamadas de API economizadas
            "started_at": datetime.now().isoformat(),
        })

    # ── Busca: ver se tarefa já foi aprendida ──────────────

    def find_learned_workflow(self, task):
        """
        Procura workflow aprendido que resolve tarefa similar.

        Returns: workflow dict se encontrado confiável, None caso contrário.
        """
        if not self.workflows:
            return None

        best_match = None
        best_score = 0.0

        for wf in self.workflows:
            # Só considera workflows confiáveis
            if wf.get("executions", 0) < MIN_EXECUTIONS_TO_TRUST:
                continue
            if wf.get("success_rate", 0) < MIN_SUCCESS_RATE:
                continue

            sim = _similarity(task, wf.get("original_task", ""))
            if sim >= SIMILARITY_THRESHOLD and sim > best_score:
                best_score = sim
                best_match = wf

        if best_match:
            self.stats["cache_hits"] += 1
            self.stats["api_calls_saved"] += best_match.get("subtasks_count", 1)
            _save_json(STATS_FILE, self.stats)
            print(f"  [Evolution] ♻️ Workflow aprendido (similaridade {best_score:.0%}, "
                  f"sucessos {best_match.get('success_rate', 0):.0%})")

        return best_match

    # ── Registro: salvar execução ──────────────────────────

    def record_execution(self, task, plan, success, execution_time_ms=0):
        """
        Registra uma execução para alimentar o aprendizado.

        Args:
            task: tarefa original do usuário
            plan: plano gerado pelo Maestro (com subtasks)
            success: True se a execução foi bem-sucedida
            execution_time_ms: duração em ms
        """
        self.stats["total_executions"] += 1
        if success:
            self.stats["total_successes"] += 1
        else:
            self.stats["total_failures"] += 1
            self._record_failure(task, plan)
            _save_json(STATS_FILE, self.stats)
            _save_json(FAILURES_FILE, self.failures)
            return

        # Só aprende com sucessos
        task_h = _task_hash(task)
        existing = next((w for w in self.workflows if w.get("hash") == task_h), None)

        if existing:
            # Reforço: incrementa contadores
            existing["executions"] = existing.get("executions", 0) + 1
            existing["successes"] = existing.get("successes", 0) + 1
            existing["success_rate"] = existing["successes"] / existing["executions"]
            existing["last_used"] = datetime.now().isoformat()
            if execution_time_ms:
                # Média móvel do tempo
                prev_avg = existing.get("avg_time_ms", execution_time_ms)
                existing["avg_time_ms"] = round((prev_avg + execution_time_ms) / 2)
            print(f"  [Evolution] 📈 Workflow reforçado (sucessos {existing['success_rate']:.0%})")
        else:
            # Novo workflow
            subtasks = plan.get("subtasks", [])
            new_wf = {
                "hash": task_h,
                "original_task": task,
                "plan": plan,
                "subtasks_count": len(subtasks),
                "agents_used": list(set(s.get("agent", "") for s in subtasks)),
                "executions": 1,
                "successes": 1,
                "success_rate": 1.0,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "avg_time_ms": execution_time_ms,
                "tags": list(_tokenize(task))[:10],
            }
            self.workflows.append(new_wf)
            print(f"  [Evolution] ✨ Novo workflow aprendido")

            # Cleanup: mantém apenas os melhores
            if len(self.workflows) > MAX_WORKFLOWS:
                self._cleanup_workflows()

        _save_json(WORKFLOWS_FILE, self.workflows)
        _save_json(STATS_FILE, self.stats)

    # ── Registro: falha ────────────────────────────────────

    def _record_failure(self, task, plan):
        """Registra falha para evitar estratégias ruins no futuro."""
        task_h = _task_hash(task)

        # Se workflow existe, decrementa sucesso
        existing = next((w for w in self.workflows if w.get("hash") == task_h), None)
        if existing:
            existing["executions"] = existing.get("executions", 0) + 1
            existing["success_rate"] = existing.get("successes", 0) / existing["executions"]
            # Se caiu abaixo de 50%, remove
            if existing["success_rate"] < 0.5 and existing["executions"] >= 3:
                self.workflows.remove(existing)
                print(f"  [Evolution] 🗑️ Workflow ruim removido (sucesso {existing['success_rate']:.0%})")
            _save_json(WORKFLOWS_FILE, self.workflows)

        # Salva falha para análise
        self.failures.append({
            "task": task,
            "hash": task_h,
            "plan_agents": list(set(s.get("agent", "") for s in plan.get("subtasks", []))),
            "timestamp": datetime.now().isoformat(),
        })
        # Mantém só últimas 100 falhas
        self.failures = self.failures[-100:]

    # ── Cleanup ────────────────────────────────────────────

    def _cleanup_workflows(self):
        """Remove workflows com pior performance."""
        # Ordena por success_rate * log(executions) — prioriza os confiáveis
        import math
        self.workflows.sort(
            key=lambda w: w.get("success_rate", 0) * math.log(w.get("executions", 1) + 1),
            reverse=True,
        )
        self.workflows = self.workflows[:MAX_WORKFLOWS]

    # ── Stats ──────────────────────────────────────────────

    def get_stats(self):
        """Retorna estatísticas agregadas."""
        total = self.stats.get("total_executions", 0)
        success_rate = 0
        if total > 0:
            success_rate = self.stats.get("total_successes", 0) / total

        trusted = sum(1 for w in self.workflows
                     if w.get("executions", 0) >= MIN_EXECUTIONS_TO_TRUST
                     and w.get("success_rate", 0) >= MIN_SUCCESS_RATE)

        return {
            "total_executions": total,
            "total_workflows": len(self.workflows),
            "trusted_workflows": trusted,
            "success_rate": round(success_rate * 100, 1),
            "cache_hits": self.stats.get("cache_hits", 0),
            "api_calls_saved": self.stats.get("api_calls_saved", 0),
            "total_failures": len(self.failures),
        }

    def list_top_workflows(self, n=10):
        """Lista os top N workflows por performance."""
        sorted_wf = sorted(
            self.workflows,
            key=lambda w: (w.get("success_rate", 0), w.get("executions", 0)),
            reverse=True,
        )
        return [{
            "task": w.get("original_task", "")[:60],
            "executions": w.get("executions", 0),
            "success_rate": round(w.get("success_rate", 0) * 100, 1),
            "agents": w.get("agents_used", []),
            "last_used": w.get("last_used", ""),
        } for w in sorted_wf[:n]]


# Singleton
_instance = None

def get_evolution_engine():
    global _instance
    if _instance is None:
        _instance = EvolutionEngine()
    return _instance