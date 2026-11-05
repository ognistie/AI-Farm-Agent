"""
Action Logger — Logging estruturado de todas as acoes executadas.
Cada acao vira uma linha JSON em logs/actions.jsonl.
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "actions.jsonl"
_lock = threading.Lock()

def log_action(agent, action, params, result, method="", duration_ms=0, screenshot_path=""):
    """Registra uma acao executada."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "param_keys": sorted((params or {}).keys()),  # no text, code, credentials or personal paths
        "result": "SUCCESS" if result.get("success") else "FAIL",
        "status": result.get("status", "succeeded" if result.get("success") else "failed"),
        "method": method,
        "duration_ms": duration_ms,
    }
    try:
        with _lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except:
        pass

def get_failure_stats():
    """Retorna estatisticas de falha."""
    if not LOG_FILE.exists():
        return {"total": 0, "failures": 0}
    stats = {"total": 0, "failures": 0, "by_agent": {}, "by_action": {}}
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                stats["total"] += 1
                if entry["result"] == "FAIL":
                    stats["failures"] += 1
                agent = entry.get("agent", "?")
                if agent not in stats["by_agent"]:
                    stats["by_agent"][agent] = {"total": 0, "failures": 0}
                stats["by_agent"][agent]["total"] += 1
                if entry["result"] == "FAIL":
                    stats["by_agent"][agent]["failures"] += 1
    except:
        pass
    return stats
