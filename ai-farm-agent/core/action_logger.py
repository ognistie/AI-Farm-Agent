"""
Action Logger — Logging estruturado de todas as acoes executadas.
Cada acao vira uma linha JSON em logs/actions.jsonl.
"""

import json
import time
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("logs/actions.jsonl")

def log_action(agent, action, params, result, method="", duration_ms=0, screenshot_path=""):
    """Registra uma acao executada."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "params": {k: str(v)[:100] for k, v in (params or {}).items()},
        "result": "SUCCESS" if result.get("success") else "FAIL",
        "error": result.get("error", result.get("result", ""))[:200] if not result.get("success") else "",
        "method": method,
        "duration_ms": duration_ms,
    }
    try:
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