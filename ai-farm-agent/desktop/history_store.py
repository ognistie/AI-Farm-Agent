"""
HistoryStore — persistencia append-only de execucoes.

Cada execucao vira UMA linha JSON em `desktop/data/history.jsonl`. Append
only para nunca corromper o arquivo no meio de uma escrita. Leitura le
todo o arquivo (sufuciente ate ~10k execucoes; depois rotaciona).

Schema de cada linha:

    {
      "id": "20260525_174203_a3f1",
      "task": "abra o vs code e crie um site sobre Muay Thai",
      "started_at": "2026-05-25T17:42:03",
      "ended_at":   "2026-05-25T17:42:21",
      "duration_ms": 18000,
      "success": true,
      "dry_run": false,
      "subtasks": [{"agent":"CODE","task":"..."}],
      "metrics": {"api_calls": 2, "tokens_est": 1500, "cost_usd": 0.003},
      "skills": ["html","css"],
      "artifacts": {
          "folder": "C:/Users/.../Desktop/site_muay_thai",
          "files":  ["index.html","style.css"],
          "url":    null
      },
      "report_path": "reports/report_20260525_174221.html",
      "error": null
    }
"""

from __future__ import annotations

import json
import secrets
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


HISTORY_FILE = Path(__file__).parent / "data" / "history.jsonl"
_lock = threading.Lock()


def _ensure_file() -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.touch()


def new_execution(task: str, dry_run: bool = False) -> Dict[str, Any]:
    """Cria registro inicial de execucao. Caller preenche e chama append()."""
    now = datetime.now()
    return {
        "id": f"{now.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(2)}",
        "task": task,
        "started_at": now.isoformat(timespec="seconds"),
        "ended_at": None,
        "duration_ms": 0,
        "success": False,
        "dry_run": dry_run,
        "subtasks": [],
        "metrics": {"api_calls": 0, "tokens_est": 0, "cost_usd": 0.0},
        "skills": [],
        "artifacts": {"folder": None, "files": [], "url": None},
        "report_path": None,
        "error": None,
    }


def append(entry: Dict[str, Any]) -> None:
    """Apende registro completo ao arquivo. Thread-safe."""
    _ensure_file()
    line = json.dumps(entry, ensure_ascii=False)
    with _lock:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def list_all(limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """Le todas as execucoes (mais recentes primeiro). None = sem limite."""
    _ensure_file()
    out: List[Dict[str, Any]] = []
    with _lock:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    # linha corrompida — ignora silenciosamente (nao bloqueia)
                    continue
    out.reverse()
    return out[:limit] if limit else out


def stats() -> Dict[str, Any]:
    """Estatisticas agregadas para o cabecalho do Historico."""
    items = list_all(limit=None)
    if not items:
        return {"total": 0, "success_rate": 0.0, "total_cost_usd": 0.0,
                "avg_duration_ms": 0}
    ok = sum(1 for it in items if it.get("success"))
    cost = sum(float(it.get("metrics", {}).get("cost_usd", 0.0)) for it in items)
    dur = sum(int(it.get("duration_ms", 0)) for it in items)
    return {
        "total": len(items),
        "success_rate": round(ok / len(items) * 100, 1),
        "total_cost_usd": round(cost, 4),
        "avg_duration_ms": round(dur / len(items)),
    }
