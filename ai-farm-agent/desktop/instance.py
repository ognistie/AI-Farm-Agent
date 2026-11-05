"""
Uma instancia so do app. Abrir de novo traz a janela que ja existe para a frente, em vez de
criar um segundo agente ouvindo o mesmo microfone e respondendo junto. O nome some com o
processo, entao um app que caiu nao impede de abrir de novo.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "ognistie.AIFarmAgent.instance"
CONNECT_MS = 400


def notify_running(name: str = SERVER_NAME) -> bool:
    """-> True se ja ha um app aberto (e ele foi avisado para aparecer)."""
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(CONNECT_MS):
        return False
    socket.write(b"show")
    socket.waitForBytesWritten(CONNECT_MS)
    socket.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Fica escutando quem tentar abrir o app de novo."""

    def __init__(self, on_show: Callable[[], None], name: str = SERVER_NAME, parent=None):
        super().__init__(parent)
        self._on_show = on_show
        self._server = QLocalServer(self)
        QLocalServer.removeServer(name)
        self.listening = self._server.listen(name)
        self._server.newConnection.connect(self._accept)

    def _accept(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is not None:
            socket.disconnected.connect(socket.deleteLater)
            self._on_show()
