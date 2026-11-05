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
    executionFinished  = Signal(str)
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
    # Plano esperando aprovacao (Configuracoes > revisar plano) e acesso rapido (Alt+Espaco)
    planReview         = Signal(str)
    quickEntry         = Signal()
    _quickEntryHotkey  = Signal()     # thread do atalho -> thread da interface
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
        # plano. O reconhecimento carrega alguns segundos depois de abrir (sem
        # disputar com a abertura), para a primeira fala nao esperar o modelo.
        try:
            from core.config import get_config
            vcfg = get_config().get("voice", {}) or {}
            if vcfg.get("start_on_launch", True):
                self._voice_ctl().start_hotkey()
                if vcfg.get("preload_on_launch", True):
                    QTimer.singleShot(4000, lambda: self._voice_ctl().stt.preload_async())
        except Exception as e:
            print(f"  [voz] indisponivel: {e}")
        self._start_stop_hotkey()
        self._quickEntryHotkey.connect(self._on_quick_entry)
        self._start_quick_hotkey()

    # ── Interface: abertura, mini chat e atalho de parar ─────────────

    @staticmethod
    def _ui_cfg() -> Dict[str, Any]:
        """config.yaml > ui, com as escolhas da tela Configuracoes por cima."""
        try:
            from core.config import get_config
            cfg = dict(get_config().get("ui", {}) or {})
        except Exception:
            cfg = {}
        try:
            from core.user_settings import load
            mine = load()
            cfg["splash"], cfg["mini_chat"] = mine["splash"], mine["mini_chat"]
        except Exception:
            pass
        return cfg

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

    # ── Configuracoes, conversas, anexos, plano ─────────────────────
    @Slot(result=str)
    def getSettings(self) -> str:
        from core.user_settings import load
        data = load()
        data["hotkeys"] = {"voice": getattr(self._voice, "combo", "") if self._voice else "",
                           "stop": self._stop_hotkey.combo if self._stop_hotkey else "",
                           "quick": self._quick_hotkey.combo if getattr(self, "_quick_hotkey", None) else ""}
        return _to_json(data)

    @Slot(str, result=str)
    def saveSettings(self, payload: str) -> str:
        """Grava e aplica o que da para aplicar na hora (voz); abertura e mini chat no proximo inicio."""
        from core.user_settings import save
        try:
            data = save(json.loads(payload or "{}"))
        except ValueError:
            return _to_json({"ok": False})
        if self._voice is not None:
            self._voice.barge_in, self._voice.earcon = data["barge_in"], data["earcon"]
            self._voice.live_conversation = data["live_conversation"]
        return _to_json({"ok": True, **data})

    def shutdown(self) -> None:
        """App fechando: nada de voz, atalho ou tarefa pode continuar depois daqui."""
        for hotkey in (self._stop_hotkey, getattr(self, "_quick_hotkey", None)):
            if hotkey is not None:
                hotkey.stop()
        if self._controller.state.get("running"):
            self._controller.force_stop()
        if self._voice is not None:
            self._voice.shutdown()

    @Slot(str, str, result=bool)
    def renameConversation(self, sid: str, title: str) -> bool:
        from core.session import Session
        ok = Session.rename_saved(sid, title)
        if ok and sid == self._controller.session.id:
            self._controller.session.custom_title = " ".join(title.split())[:80]
        if ok:
            self.conversationsChanged.emit(_to_json({"id": sid}))
        return ok

    @Slot(str, result=bool)
    def deleteConversation(self, sid: str) -> bool:
        from core.session import Session
        if self._running and sid == self._controller.session.id:
            return False                 # nao some com a conversa em execucao
        ok = Session.delete_saved(sid)
        if ok:
            if sid == self._controller.session.id:
                self._controller.new_session()
            self.conversationsChanged.emit(_to_json({"id": sid}))
        return ok

    @Slot(str, result=str)
    def attachFiles(self, payload: str) -> str:
        """Lista de caminhos (JSON) -> os que existem; ficam na conversa como arquivos legiveis."""
        try:
            paths = [str(p) for p in json.loads(payload or "[]")]
        except ValueError:
            paths = []
        return _to_json(self._controller.attach_files(paths))

    @Slot(bool, str)
    def approvePlan(self, ok: bool, token: str) -> None:
        self._controller.approve_plan(ok, token)

    def _start_quick_hotkey(self) -> None:
        """Acesso rapido de qualquer app (como Alt+Espaco no ChatGPT e o atalho do Claude):
        abre a caixa de pedido por cima do que estiver na tela."""
        self._quick_hotkey = None
        combo = self._ui_cfg().get("quick_hotkey", "alt+space")
        if not combo:
            return
        try:
            from core.voice.hotkey import GlobalHotkey
            hk = GlobalHotkey(combo, self._quickEntryHotkey.emit)
            if hk.start_and_wait():
                self._quick_hotkey = hk
            else:
                print(f"  [ui] atalho de acesso rapido {combo} indisponivel (em uso)")
        except Exception as e:
            print(f"  [ui] atalho de acesso rapido indisponivel: {e}")

    @Slot()
    def _on_quick_entry(self) -> None:
        if self._window_mode:
            self._window_mode.quick_entry()
        self.quickEntry.emit()

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
            "execution_finished": self._on_execution_finished,
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
            "plan_review":        lambda p: self.planReview.emit(_to_json(p)),
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

    def _on_execution_finished(self, payload: dict) -> None:
        self.executionFinished.emit(_to_json(payload))
        if self._running:
            self._running = False
            self.runningChanged.emit(False)

    def _on_answer(self, payload: dict) -> None:
        self.answerReady.emit(_to_json(payload))

    def _on_cancelled(self, payload: dict) -> None:
        self.cancelled.emit(_to_json(payload))

    def _on_error(self, payload: dict) -> None:
        self.errorRaised.emit(_to_json(payload))
        if not self._controller.state.get("running"):
            self._on_execution_finished({"success": False, "status": "rejected"})

    # ── Slots invocados pelo QML ──────────────────────────────────────

    @Slot(str, bool, bool)
    def executeTask(self, task: str, dry_run: bool, generate_report: bool) -> None:
        self._controller.execute_task(task, dry_run=dry_run,
                                      generate_report=generate_report)

    def _voice_ctl(self):
        if self._voice is None:
            from core.config import get_config
            from desktop.voice import VoiceController
            vcfg = dict(get_config().get("voice", {}) or {})
            try:
                from core.user_settings import load
                mine = load()
                vcfg["barge_in"], vcfg["earcon"] = mine["barge_in"], mine["earcon"]
                vcfg["live_conversation"] = mine["live_conversation"]
            except Exception:
                pass
            self._voice = VoiceController(self._controller, vcfg)
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
