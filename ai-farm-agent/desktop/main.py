"""
Entry point do AI Farm Agent Desktop.

Inicia QApplication, carrega QML raiz e injeta `Bridge` como context
property. Substitui completamente o antigo servidor Flask + browser.

Uso:
    python main.py            # via main.py raiz do projeto
    python -m desktop.main    # direto (para debug)
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

import PySide6
from PySide6.QtCore import QRectF, QUrl, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from desktop.bridge import Bridge


HERE = Path(__file__).parent
QML_DIR = HERE / "qml"
QML_ROOT = QML_DIR / "Main.qml"


def _setup_fonts(app: QGuiApplication) -> None:
    """Fonte do sistema (Segoe UI Variable no Windows 11). Se nao existir,
    o Qt escolhe a sans-serif padrao."""
    # Windows 10 nao tem Segoe UI Variable; Cascadia vem com o Terminal.
    QFont.insertSubstitutions("Segoe UI Variable Text", ["Segoe UI Variable", "Segoe UI"])
    QFont.insertSubstitutions("Segoe UI Variable Display", ["Segoe UI Variable", "Segoe UI"])
    QFont.insertSubstitutions("Cascadia Mono", ["Consolas", "Courier New"])
    default = QFont("Segoe UI Variable Text", 10)
    default.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(default)


def _brand_icon() -> QIcon:
    """Icone da janela/barra de tarefas: a mesma marca do app (BrandMark.qml)."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 256):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        pad = size * 0.08
        gap = max(1.0, size * 0.10)
        cell = (size - 2 * pad - gap) / 2
        for i in range(4):
            x = pad + (i % 2) * (cell + gap)
            y = pad + (i // 2) * (cell + gap)
            p.setBrush(QColor("#0A7CFF" if i == 3 else "#1D1D1F"))
            p.drawRoundedRect(QRectF(x, y, cell, cell), cell * 0.28, cell * 0.28)
        p.end()
        icon.addPixmap(pix)
    return icon


def _style_title_bar(window) -> None:
    """Barra nativa clara (como o resto da UI) sem perder os controles da janela."""
    if sys.platform != "win32":
        return

    try:
        handle = ctypes.c_void_p(int(window.winId()))
        set_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        set_attribute.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                  ctypes.c_void_p, ctypes.c_uint]
        set_attribute.restype = ctypes.c_long

        def apply(attribute: int, value: int) -> None:
            data = ctypes.c_uint(value)
            set_attribute(handle, attribute, ctypes.byref(data),
                          ctypes.sizeof(data))

        apply(20, 0)           # DWMWA_USE_IMMERSIVE_DARK_MODE (desligado)
        apply(35, 0x00FFFFFF)  # DWMWA_CAPTION_COLOR (#FFFFFF)
        apply(36, 0x001F1D1D)  # DWMWA_TEXT_COLOR (#1D1D1F, COLORREF e BGR)
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        print(f"[desktop] barra de titulo nativa sem personalizacao: {exc}")


def run() -> int:
    # Estilo "Basic": o estilo nativo do Windows ignora parte da
    # customizacao (fundo de TextArea, ScrollBar) e gera avisos no console.
    QQuickStyle.setStyle("Basic")
    # Escala fracionaria (125%, 150%) sem arredondar — evita textos e
    # bordas borrados/desproporcionais em notebooks.
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # Identidade propria na barra de tarefas (senao o Windows agrupa como
    # python.exe e mostra o icone do Python)
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ognistie.AIFarmAgent")
        except (AttributeError, OSError):
            pass

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    app.setApplicationName("AI Farm Agent")
    app.setOrganizationName("ognistie")
    app.setApplicationDisplayName("AI Farm Agent")
    app.setWindowIcon(_brand_icon())

    _setup_fonts(app)

    # Python 3.14 no Windows pode nao localizar as DLLs usadas pelos plugins
    # QML apenas com o import do PySide6. O handle precisa viver ate o fim.
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        app._qt_dll_directory = os.add_dll_directory(  # type: ignore[attr-defined]
            str(Path(PySide6.__file__).parent))

    bridge = Bridge()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    engine.rootContext().setContextProperty("Bridge", bridge)

    engine.load(QUrl.fromLocalFile(str(QML_ROOT)))
    if not engine.rootObjects():
        print("[desktop] falha ao carregar QML raiz:", QML_ROOT)
        return 2

    window = engine.rootObjects()[0]
    # Abertura: janela propria por cima do app ja maximizado (ver
    # SplashWindow.qml). Ocupa exatamente a area da janela maximizada (a tela
    # sem a barra de tarefas): a barra de tarefas fica parada o tempo todo e o
    # fade de saida so revela o app que esta atras. Mostrada antes para o app
    # nao piscar sem ela.
    splash = next((w for w in QGuiApplication.topLevelWindows()
                   if w.objectName() == "splashWindow"), None)
    if splash is not None and bridge.splash_enabled():
        screen = window.screen() or app.primaryScreen()
        splash.setGeometry(screen.availableGeometry())
        splash.show()
    window.showMaximized()
    if splash is not None and splash.isVisible():
        splash.raise_()
        splash.requestActivate()
    _style_title_bar(window)
    # Mini chat: janela propria que assume a conversa quando o agente vai
    # para outro app (ver desktop/window_mode.py)
    mini = next((w for w in QGuiApplication.topLevelWindows()
                 if w.objectName() == "miniChat"), None)
    if mini is not None:
        bridge.attach_windows(window, mini)

    # Manter referencias vivas
    app._bridge_ref = bridge  # type: ignore[attr-defined]
    app._engine_ref = engine  # type: ignore[attr-defined]

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
