"""
Registro duravel de tarefas: um arquivo de eventos por tarefa, gravado ANTES e DEPOIS de cada passo.

O historico (desktop/data/history.jsonl) so recebe a execucao no fim, entao uma queda perdia tudo.
Aqui cada evento vai para o disco na hora. O estado e sempre calculado a partir dos eventos.
Passo iniciado e sem fim registrado tem resultado desconhecido: pode ter tido efeito, entao
nunca e repetido as cegas. Este registro nao retoma nada sozinho.

Grava o nome dos parametros, nao os valores (mesma regra de core/action_logger.py). Falhar aqui
nunca derruba a tarefa: o agente segue, e o aviso fica no log.

Eventos: created, plan, step_started, step_finished, step_retry, progress, note, interrupted, finished
Estados: running -> completed | failed | cancelled | interrupted
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[1] / "memory" / "tasks"
KEEP_TASKS = 300
RESULT_MAX = 240
TERMINAL = ("completed", "failed", "cancelled", "interrupted")
log = logging.getLogger("task_ledger")


def _pid_alive(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        return True          # na duvida nao marca uma tarefa viva como interrompida


def replay(events: Iterable[dict]) -> dict:
    """O estado da tarefa, calculado so a partir dos eventos."""
    task = {"id": "", "state": "running", "goal": "", "steps_done": [], "steps_failed": [], "steps_uncertain": [],
            "steps_pending": [], "evidence": [], "interruptions": [], "verified": None, "pid": None, "events": 0}
    open_steps: dict = {}
    planned: list = []
    for event in events:
        kind = event.get("type")
        task["events"] += 1
        if kind == "created":
            task.update(id=event.get("task_id", ""), goal=event.get("goal", ""), pid=event.get("pid"),
                        source=event.get("source", ""), dry_run=bool(event.get("dry_run")),
                        session_id=event.get("session_id"), started_at=event.get("at"))
        elif kind == "plan":
            planned = [str(step) for step in event.get("steps", [])]
        elif kind == "step_started":
            open_steps[event.get("step")] = {"step": event.get("step"), "action": event.get("action", ""),
                                             "description": event.get("description", ""),
                                             "params": event.get("params", [])}
        elif kind == "step_finished":
            step = open_steps.pop(event.get("step"), {"step": event.get("step"), "action": event.get("action", "")})
            done = {**step, "status": event.get("status", ""), "verified": bool(event.get("verified"))}
            (task["steps_done"] if event.get("ok") else task["steps_failed"]).append(done)
            if event.get("result"):
                task["evidence"].append({"step": event.get("step"), "result": event["result"],
                                         "verified": bool(event.get("verified"))})
        elif kind == "progress":
            task["evidence"].append({"step": event.get("step"), "result": event.get("message", ""), "verified": False})
        elif kind == "note" and event.get("kind") == "interruption":
            task["interruptions"].append({"at": event.get("at"), "reason": event.get("reason", "")})
        elif kind == "interrupted":
            task["state"] = "interrupted"
            task["interruptions"].append({"at": event.get("at"), "reason": event.get("reason", "")})
        elif kind == "finished":
            task.update(state=event.get("state", "failed"), verified=event.get("verified"),
                        error=event.get("error"), ended_at=event.get("at"))
    task["steps_uncertain"] = list(open_steps.values())
    started = len(task["steps_done"]) + len(task["steps_failed"]) + len(open_steps)
    task["steps_pending"] = planned[started:] if task["state"] == "running" or task["state"] == "interrupted" else []
    return task


class TaskLedger:
    def __init__(self, root: Optional[Path] = None, enabled: bool = True):
        self.root = Path(root or ROOT)
        self.enabled = enabled
        self._lock = threading.Lock()
        self._seq: dict = {}

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.jsonl"

    def _write(self, task_id: str, event: dict) -> None:
        """Evento inteiro em uma linha, ja no disco ao retornar. Cada evento e independente: uma linha
        cortada por uma queda se perde sozinha, sem levar as anteriores."""
        if not self.enabled or not task_id:
            return
        try:
            with self._lock:
                seq = self._seq.get(task_id, 0) + 1
                self._seq[task_id] = seq
                self.root.mkdir(parents=True, exist_ok=True)
                line = json.dumps({"seq": seq, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **event}, ensure_ascii=False)
                with self._path(task_id).open("a", encoding="utf-8") as stream:
                    stream.write(line + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
        except (OSError, TypeError, ValueError) as error:
            log.warning("registro de tarefa falhou: %s", type(error).__name__)

    # ── gravar ────────────────────────────────────────────────────
    def begin(self, task_id: str, goal: str, *, source: str = "", dry_run: bool = False, session_id=None) -> str:
        self._write(task_id, {"type": "created", "task_id": task_id, "goal": goal, "source": source, "dry_run": dry_run,
                              "session_id": session_id, "pid": os.getpid()})
        return task_id

    def plan(self, task_id: str, steps: list) -> None:
        self._write(task_id, {"type": "plan", "steps": [str(step)[:160] for step in steps]})

    def step_started(self, task_id: str, step: int, agent: str, action: str, params, description: str = "") -> None:
        """Vem ANTES da acao: sem isto, uma queda no meio nao deixaria rastro do que pode ter acontecido."""
        keys = sorted(params) if isinstance(params, dict) else []
        self._write(task_id, {"type": "step_started", "step": step, "agent": agent, "action": action, "params": keys,
                              "description": str(description)[:160]})

    def step_retry(self, task_id: str, step: int, action: str) -> None:
        self._write(task_id, {"type": "step_retry", "step": step, "action": action})

    def step_finished(self, task_id: str, step: int, action: str, result: dict) -> None:
        self._write(task_id, {"type": "step_finished", "step": step, "action": action,
                              "ok": bool(result.get("success")), "status": result.get("status", ""),
                              "verified": result.get("verified") is True, "result": str(result.get("result", ""))[:RESULT_MAX]})

    def progress(self, task_id: str, step: int, message: str) -> None:
        self._write(task_id, {"type": "progress", "step": step, "message": str(message)[:RESULT_MAX]})

    def note(self, task_id: str, kind: str, **data) -> None:
        self._write(task_id, {"type": "note", "kind": kind, **data})

    def finish(self, task_id: str, state: str, *, verified: bool = False, error=None) -> None:
        self._write(task_id, {"type": "finished", "state": state if state in TERMINAL else "failed",
                              "verified": verified, "error": str(error)[:RESULT_MAX] if error else None})
        with self._lock:
            self._seq.pop(task_id, None)

    # ── ler ───────────────────────────────────────────────────────
    def events(self, task_id: str) -> list:
        rows = []
        try:
            for line in self._path(task_id).read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue         # linha cortada por uma queda: as demais continuam valendo
        except OSError:
            pass
        return rows

    def load(self, task_id: str) -> dict:
        return replay(self.events(task_id))

    def task_ids(self) -> list:
        try:
            files = sorted(self.root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        except OSError:
            return []
        return [path.stem for path in files]

    def recover(self) -> list:
        """Ao abrir o app: tarefa sem fim cujo processo morreu fica marcada como interrompida. So isso:
        nada e executado de novo. -> as tarefas que precisam da atencao da pessoa."""
        if not self.enabled:
            return []
        found = []
        for task_id in self.task_ids():
            task = self.load(task_id)
            if task["state"] != "running" or not task["id"]:
                continue
            if task["pid"] is not None and int(task["pid"]) != os.getpid() and _pid_alive(task["pid"]):
                continue
            self._write(task_id, {"type": "interrupted", "reason": "o app fechou antes de a tarefa terminar"})
            found.append(self.load(task_id))
        self.prune()
        return found

    def prune(self, keep: int = KEEP_TASKS) -> int:
        ids = self.task_ids()
        removed = 0
        for task_id in ids[:max(0, len(ids) - keep)]:
            try:
                self._path(task_id).unlink()
                removed += 1
            except OSError:
                pass
        return removed


_ledger: Optional[TaskLedger] = None


def get_ledger() -> TaskLedger:
    global _ledger
    if _ledger is None:
        try:
            from core.config import get_config
            enabled = bool(get_config().get("execution.ledger", True))
        except Exception:
            enabled = True
        _ledger = TaskLedger(enabled=enabled)
    return _ledger
