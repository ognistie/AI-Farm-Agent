"""
AI Farm Agent — Camada Desktop (PySide6 + QML).

Substitui a antiga UI web (Flask + SocketIO + HTML) por uma aplicacao
nativa estilo macOS. Nao modifica nenhum agente, nem core/, nem memory/.

Pontos de entrada:
- `desktop.main:run()` inicia QApplication e abre a janela principal.
- `main.py` (raiz) delega a este modulo.
"""

__version__ = "1.0.0"
