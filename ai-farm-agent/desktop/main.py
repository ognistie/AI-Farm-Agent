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

from PySide6.QtCore import QUrl, QCoreApplication, Qt
from PySide6.QtGui import QGuiApplication, QFont, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from desktop.bridge import Bridge


HERE = Path(__file__).parent
QML_DIR = HERE / "qml"
QML_ROOT = QML_DIR / "Main.qml"


def _setup_fonts(app: QGuiApplication) -> None:
    """Aplica fonte default. Se Inter/JetBrains nao estiver instalada o Qt
    cai automaticamente para a melhor proxima (Segoe UI no Windows)."""
    default = QFont("Inter", 10)
    default.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(default)


def run() -> int:
    # High-DPI ja eh default no Qt6, mas garantimos round policy fina.
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    app.setApplicationName("AI Farm Agent")
    app.setOrganizationName("ognistie")
    app.setApplicationDisplayName("AI Farm Agent")

    _setup_fonts(app)

    bridge = Bridge()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    engine.rootContext().setContextProperty("Bridge", bridge)
    engine.rootContext().setContextProperty("QML_DIR", str(QML_DIR).replace("\\", "/"))

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
