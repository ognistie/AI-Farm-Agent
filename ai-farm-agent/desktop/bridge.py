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
    # Conversa: como a fala foi entendida, resposta sem acao, nova conversa
    resolved           = Signal(str)
    answerReady        = Signal(str)
    sessionReset       = Signal(str)
    # Modo voz
    voiceState         = Signal(str)
    voiceLevel         = Signal(str)
    voiceHeard         = Signal(str)
    voiceCommand       = Signal(str)
    voiceReply         = Signal(str)
    voiceChat          = Signal(str)
    # Conversa: resposta do assistente ao fim de cada pedido; lista de conversas mudou
    assistantMessage   = Signal(str)
    conversationsChanged = Signal(str)
    # Estado de running (UI bloqueia botao executar)
    runningChanged     = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._controller = Controller()
        self._running = False
        self._voice = None
        self._window_mode = None
        self._stop_hotkey = None
        self._wire_bus()
        self.runningChanged.connect(self._on_running_changed)
        # Voz pronta desde o inicio: atalho global ativo e voz aquecida em segundo
        # plano. O reconhecimento (modelo) so carrega na primeira fala.
        try:
            from core.config import get_config
            if (get_config().get("voice", {}) or {}).get("start_on_launch", True):
                self._voice_ctl().start_hotkey()
        except Exception as e:
            print(f"  [voz] indisponivel: {e}")
        self._start_stop_hotkey()

    # ── Interface: abertura, mini chat e atalho de parar ─────────────

    @staticmethod
    def _ui_cfg() -> Dict[str, Any]:
        try:
            from core.config import get_config
            return dict(get_config().get("ui", {}) or {})
        except Exception:
            return {}

    def _start_stop_hotkey(self) -> None:
        """Atalho global para parar: o mini chat nao recebe cliques enquanto
        o agente trabalha, entao parar precisa funcionar de qualquer janela."""
        combo = self._ui_cfg().get("stop_hotkey", "ctrl+alt+x")
        if not combo:
            return
        try:
            from core.voice.hotkey import GlobalHotkey
            hk = GlobalHotkey(combo, self._stop_from_hotkey)
            if hk.start_and_wait():
                self._stop_hotkey = hk
            else:
                print(f"  [ui] atalho de parar {combo} indisponivel (em uso por outro programa)")
        except Exception as e:
            print(f"  [ui] atalho de parar indisponivel: {e}")

    def _stop_from_hotkey(self) -> None:
        if self._running:
            self._controller.force_stop()

    def attach_windows(self, main_window, mini_window) -> None:
        """Chamado pelo main.py depois de carregar o QML."""
        from desktop.window_mode import WindowMode
        cfg = self._ui_cfg()
        self._window_mode = WindowMode(
            main_window, mini_window,
            enabled=cfg.get("mini_chat", True) is not False,
            hide_from_capture=bool(cfg.get("mini_hide_from_capture", False)))

    @Slot(bool)
    def _on_running_changed(self, running: bool) -> None:
        if self._window_mode:
            self._window_mode.set_running(running)

    def splash_enabled(self) -> bool:
        return self._ui_cfg().get("splash", True) is not False

    @Slot(result=str)
    def uiSettings(self) -> str:
        cfg = self._ui_cfg()
        # So anuncia o atalho de parar se ele foi registrado de fato
        combo = self._stop_hotkey.combo if self._stop_hotkey else ""
        label = "+".join(k.capitalize() for k in combo.split("+")) if combo else ""
        return _to_json({
            "splash": self.splash_enabled(),
            "mini_chat": cfg.get("mini_chat", True) is not False,
            "stop_hotkey_label": label,
        })

    @Slot()
    def restoreMain(self) -> None:
        if self._window_mode:
            self._window_mode.restore()

    @Slot()
    def closeMini(self) -> None:
        if self._window_mode:
            self._window_mode.close_mini()

    @Slot()
    def mainActivated(self) -> None:
        if self._window_mode:
            self._window_mode.main_activated()

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
            "resolved":           lambda p: self.resolved.emit(_to_json(p)),
            "answer":             self._on_answer,
            "session_reset":      lambda p: self.sessionReset.emit(_to_json(p)),
            "voice_state":        lambda p: self.voiceState.emit(_to_json(p)),
            "voice_level":        lambda p: self.voiceLevel.emit(_to_json(p)),
            "voice_heard":        lambda p: self.voiceHeard.emit(_to_json(p)),
            "voice_command":      lambda p: self.voiceCommand.emit(_to_json(p)),
            "voice_reply":        lambda p: self.voiceReply.emit(_to_json(p)),
            "voice_chat":         lambda p: self.voiceChat.emit(_to_json(p)),
            "assistant_message":  lambda p: self.assistantMessage.emit(_to_json(p)),
            "conversations_changed": lambda p: self.conversationsChanged.emit(_to_json(p)),
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

    def _on_answer(self, payload: dict) -> None:
        self.answerReady.emit(_to_json(payload))
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

    def _voice_ctl(self):
        if self._voice is None:
            from core.config import get_config
            from desktop.voice import VoiceController
            self._voice = VoiceController(self._controller, get_config().get("voice", {}) or {})
        return self._voice

    @Slot()
    def voiceRecordToggle(self) -> None:
        """Microfone: 1o clique grava, 2o envia (como mensagem de audio)."""
        self._voice_ctl().record_toggle()

    @Slot()
    def voiceRecordCancel(self) -> None:
        self._voice_ctl().record_cancel()

    @Slot(bool)
    def setLiveConversation(self, on: bool) -> None:
        """Conversa ao vivo: microfone aberto, cada fala vira pedido e executa em fila."""
        self._voice_ctl().set_live(on)

    @Slot()
    def newSession(self) -> None:
        self._controller.new_session()

    @Slot()
    def forceStop(self) -> None:
        self._controller.force_stop()

    @Slot(result=str)
    def loadConversations(self) -> str:
        """Conversas salvas (mais recente primeiro) para a barra lateral."""
        return _to_json({"items": self._controller.list_conversations(),
                         "current": self._controller.session.id})

    @Slot(str, result=str)
    def openConversation(self, sid: str) -> str:
        """Retoma uma conversa: devolve os pedidos/respostas para a tela."""
        data = self._controller.open_conversation(sid)
        return _to_json(data or {})

    @Slot(result=str)
    def loadHistory(self) -> str:
        """Retorna JSON com lista de execucoes + stats agregados."""
        return _to_json({
            "items": history_store.list_all(limit=200),
            "stats": history_store.stats(),
        })
