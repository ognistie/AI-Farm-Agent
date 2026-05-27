"""
Bridge — QObject expondo o Controller para o QML.

QML nao consegue chamar diretamente um EventBus Python. A `Bridge` traduz:

    EventBus.emit(name, payload)        →  Bridge.<signal>(payload_json_str)
    QML.executeTask(text, dry, report)  →  Controller.execute_task(...)

Cada signal e emitido com payload JSON string (mais simples de consumir
em QML que QVariantMap, e funciona com PySide6 sem ginastica de tipos).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from desktop.event_bus import bus
from desktop.controller import Controller
from desktop import history_store
from desktop.theme import as_qml_dict, agent_color


def _to_json(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        return "{}"


class Bridge(QObject):
    """Objeto exposto ao QML como `Bridge` via context property."""

    # ── sinais 1-pra-1 com os eventos do EventBus ────────────────────
    phaseChanged       = Signal(str)
    planReady          = Signal(str)
    stepStart          = Signal(str)
    stepDone           = Signal(str)
    apiUsage           = Signal(str)
    contextExtracted   = Signal(str)
    taskDone           = Signal(str)
    reportReady        = Signal(str)
    cancelled          = Signal(str)
    errorRaised        = Signal(str)
    logEntry           = Signal(str)
    historyChanged     = Signal(str)
    # Estado de running (UI bloqueia botao executar)
    runningChanged     = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._controller = Controller()
        self._running = False
        self._wire_bus()

    # ── Listeners do bus → emit signals Qt ────────────────────────────

    def _wire_bus(self) -> None:
        m = {
            "phase":              self._on_phase,
            "plan_ready":         lambda p: self.planReady.emit(_to_json(p)),
            "step_start":         lambda p: self.stepStart.emit(_to_json(p)),
            "step_done":          lambda p: self.stepDone.emit(_to_json(p)),
            "api_usage":          lambda p: self.apiUsage.emit(_to_json(p)),
            "context_extracted":  lambda p: self.contextExtracted.emit(_to_json(p)),
            "task_done":          self._on_task_done,
            "report_ready":       lambda p: self.reportReady.emit(_to_json(p)),
            "cancelled":          self._on_cancelled,
            "error":              self._on_error,
            "log":                lambda p: self.logEntry.emit(_to_json(p)),
            "history_changed":    lambda p: self.historyChanged.emit(_to_json(p)),
        }
        for ev, cb in m.items():
            bus.on(ev, cb)

    def _on_phase(self, payload: dict) -> None:
        self.phaseChanged.emit(_to_json(payload))
        # quando entra em fase "maestro" pela primeira vez, running=True
        if not self._running:
            self._running = True
            self.runningChanged.emit(True)

    def _on_task_done(self, payload: dict) -> None:
        self.taskDone.emit(_to_json(payload))
        if self._running:
            self._running = False
            self.runningChanged.emit(False)

    def _on_cancelled(self, payload: dict) -> None:
        self.cancelled.emit(_to_json(payload))
        if self._running:
            self._running = False
            self.runningChanged.emit(False)

    def _on_error(self, payload: dict) -> None:
        self.errorRaised.emit(_to_json(payload))
        if self._running:
            self._running = False
            self.runningChanged.emit(False)

    # ── Slots invocados pelo QML ──────────────────────────────────────

    @Slot(str, bool, bool)
    def executeTask(self, task: str, dry_run: bool, generate_report: bool) -> None:
        self._controller.execute_task(task, dry_run=dry_run,
                                      generate_report=generate_report)

    @Slot()
    def forceStop(self) -> None:
        self._controller.force_stop()

    @Slot(result=str)
    def loadHistory(self) -> str:
        """Retorna JSON com lista de execucoes + stats agregados."""
        return _to_json({
            "items": history_store.list_all(limit=200),
            "stats": history_store.stats(),
        })

    @Slot(str, result=str)
    def replayFromHistory(self, entry_id: str) -> str:
        """Localiza task pelo id e devolve para o QML preencher o input."""
        for it in history_store.list_all(limit=None):
            if it.get("id") == entry_id:
                return it.get("task", "")
        return ""

    @Slot(str, result=str)
    def agentColor(self, agent_name: str) -> str:
        return agent_color(agent_name)

    @Slot(result=str)
    def theme(self) -> str:
        """Tokens de tema serializados para QML usar diretamente."""
        return _to_json(as_qml_dict())
