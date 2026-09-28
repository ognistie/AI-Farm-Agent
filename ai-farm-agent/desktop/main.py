"""
Entry point do AI Farm Agent Desktop.

Inicia QApplication, carrega QML raiz e injeta `Bridge` como context
property. Substitui completamente o antigo servidor Flask + browser.

Uso:
    python main.py            # via main.py raiz do projeto
    python -m desktop.main    # direto (para debug)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QGuiApplication, QFont, QIcon
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


def run() -> int:
    # Estilo "Basic": o estilo nativo do Windows ignora parte da
    # customizacao (fundo de TextArea, ScrollBar) e gera avisos no console.
    QQuickStyle.setStyle("Basic")
    # Escala fracionaria (125%, 150%) sem arredondar — evita textos e
    # bordas borrados/desproporcionais em notebooks.
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    app.setApplicationName("AI Farm Agent")
    app.setOrganizationName("ognistie")
    app.setApplicationDisplayName("AI Farm Agent")

    _setup_fonts(app)

    bridge = Bridge()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    engine.rootContext().setContextProperty("Bridge", bridge)

    engine.load(QUrl.fromLocalFile(str(QML_ROOT)))
    if not engine.rootObjects():
        print("[desktop] falha ao carregar QML raiz:", QML_ROOT)
        return 2

    # Manter referencias vivas
    app._bridge_ref = bridge  # type: ignore[attr-defined]
    app._engine_ref = engine  # type: ignore[attr-defined]

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
