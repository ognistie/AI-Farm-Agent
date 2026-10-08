"""
Janela completa <-> mini chat.

Quando uma tarefa esta rodando e outra janela vai para a frente (o agente
abriu um app, o navegador...), a janela principal minimiza sem roubar o foco
e a conversa continua num mini chat no canto inferior direito. Ao clicar em
"abrir a janela completa" (ou na barra de tarefas), volta tudo ao normal.

Regras que protegem a execucao:
- nada aqui ativa janelas durante a tarefa: o mini chat aparece sem foco e,
  enquanto o agente trabalha, nao recebe cliques (o QML cuida das flags);
- minimizar usa SW_SHOWMINNOACTIVE, que nao muda a janela em primeiro plano.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QWindow

# Janelas do proprio Windows que nao contam como "o agente foi para outro app"
_SHELL_CLASSES = {
    "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "Progman", "WorkerW",
    "Windows.UI.Core.CoreWindow", "ForegroundStaging", "MultitaskingViewFrame",
    "XamlExplorerHostIslandWindow", "TaskSwitcherWnd", "NotifyIconOverflowWindow",
    "TopLevelWindowForOverflowXamlIsland",
}

SW_SHOWMINNOACTIVE = 7
WDA_NONE, WDA_EXCLUDEFROMCAPTURE = 0x0, 0x11
DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND = 33, 2
DWMWA_BORDER_COLOR = 34
MARGIN = 16
POLL_MS = 350


def foreign_foreground() -> bool:
    """True se a janela em primeiro plano e de outro programa (nao do shell)."""
    if sys.platform != "win32":
        return False
    u = ctypes.windll.user32
    h = u.GetForegroundWindow()
    if not h:
        return False
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value == os.getpid():
        return False
    cls = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, cls, 256)
    if cls.value in _SHELL_CLASSES:
        return False
    return bool(u.IsWindowVisible(h)) and u.GetWindowTextLengthW(h) > 0


def _dwm_set(hwnd: int, attribute: int, value: int) -> None:
    data = ctypes.c_uint(value)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        ctypes.c_void_p(hwnd), ctypes.c_uint(attribute),
        ctypes.byref(data), ctypes.sizeof(data))


class WindowMode(QObject):
    """Alterna entre a janela principal e o mini chat."""

    def __init__(self, main: QWindow, mini: QWindow, *, enabled: bool = True,
                 hide_from_capture: bool = False) -> None:
        super().__init__(main)
        self.main, self.mini = main, mini
        self.enabled = enabled and sys.platform == "win32"
        self.hide_from_capture = hide_from_capture
        self.active = False          # mini chat em cena
        self._was_maximized = True
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._check)
        # Mostrar o mini chat nunca tira o foco do app que o agente esta usando
        mini.setProperty("_q_showWithoutActivating", True)

    # ── Execucao ────────────────────────────────────────────────────
    def set_running(self, running: bool) -> None:
        if not self.enabled:
            return
        if running and not self.active:
            self._timer.start()
        else:
            self._timer.stop()

    def _check(self) -> None:
        if self.active or not foreign_foreground():
            return
        self._timer.stop()
        self.enter()

    # ── Transicoes ──────────────────────────────────────────────────
    def enter(self) -> None:
        """Mini chat no canto; a janela principal minimiza sem ativar nada."""
        if self.active:
            return
        self.active = True
        self._place_mini()
        self.mini.show()
        self._style_mini()
        self._was_maximized = self.main.visibility() == QWindow.Visibility.Maximized
        if sys.platform == "win32":
            ctypes.windll.user32.ShowWindow(ctypes.c_void_p(int(self.main.winId())),
                                            SW_SHOWMINNOACTIVE)
        else:
            self.main.showMinimized()

    def restore(self) -> None:
        """Volta para a janela completa (pedido do usuario)."""
        self.active = False
        self.mini.hide()
        if self._was_maximized:
            self.main.showMaximized()
        else:
            self.main.showNormal()
        self.main.raise_()
        self.main.requestActivate()

    def close_mini(self) -> None:
        """Fecha so o mini chat; a janela principal segue na barra de tarefas."""
        self.active = False
        self.mini.hide()

    def main_activated(self) -> None:
        """O usuario voltou para a janela principal (ex.: barra de tarefas)."""
        if self.active:
            self.active = False
            self.mini.hide()

    # ── Detalhes de janela ──────────────────────────────────────────
    def _place_mini(self) -> None:
        screen = self.main.screen() or self.mini.screen()
        if screen is None:
            return
        g = screen.availableGeometry()
        self.mini.setPosition(g.x() + g.width() - self.mini.width() - MARGIN,
                              g.y() + g.height() - self.mini.height() - MARGIN)

    def _style_mini(self) -> None:
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.mini.winId())
            _dwm_set(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)
            _dwm_set(hwnd, DWMWA_BORDER_COLOR, 0x00E3E3E3)
            ctypes.windll.user32.SetWindowDisplayAffinity(
                ctypes.c_void_p(hwnd),
                WDA_EXCLUDEFROMCAPTURE if self.hide_from_capture else WDA_NONE)
        except (AttributeError, OSError) as exc:
            print(f"[desktop] mini chat sem cantos arredondados: {exc}")
