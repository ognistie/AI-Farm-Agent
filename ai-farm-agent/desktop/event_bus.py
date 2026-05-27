"""
EventBus — pub/sub sincrono e thread-safe.

Substitui `socketio.emit(name, payload)` por `bus.emit(name, payload)`.
Multiplos listeners por evento. Excecoes em listeners NUNCA derrubam o
publisher: sao logadas e o proximo listener continua (briefing principio
3 - falha rapida, falha alta, mas localizada).

Eventos publicados pela camada Controller (espelha 1-pra-1 o que o
antigo ui/server.py emitia via SocketIO):

    phase              — mudanca de fase (maestro/agent/reporting)
    plan_ready         — Maestro entregou plano (subtasks)
    step_start         — inicio de step de agente
    step_done          — fim de step (ok/falha, screenshot)
    api_usage          — atualizacao incremental de calls/tokens
    context_extracted  — ContextManager extraiu arquivos/pastas/url
    task_done          — execucao concluida
    report_ready       — relatorio do Narrator pronto
    cancelled          — execucao interrompida
    error              — erro inesperado
    log                — log estruturado (level/agent/msg)        [NOVO]
    history_changed    — nova entrada no historico                [NOVO]
"""

from __future__ import annotations

import threading
import traceback
from collections import defaultdict
from typing import Any, Callable, Dict, List


Listener = Callable[[dict], None]


class EventBus:
    """Pub/sub minimo. Thread-safe via lock interno."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Listener]] = defaultdict(list)
        self._lock = threading.RLock()

    def on(self, event: str, callback: Listener) -> Callable[[], None]:
        """Inscreve listener. Retorna funcao para cancelar inscricao."""
        with self._lock:
            self._listeners[event].append(callback)

        def _off() -> None:
            with self._lock:
                if callback in self._listeners.get(event, []):
                    self._listeners[event].remove(callback)

        return _off

    def emit(self, event: str, payload: Any = None) -> None:
        """Publica evento. Listeners executam no thread do publisher."""
        if payload is None:
            payload = {}
        with self._lock:
            listeners = list(self._listeners.get(event, []))
        for cb in listeners:
            try:
                cb(payload)
            except Exception:  # nunca derruba o publisher
                print(f"[EventBus] listener para '{event}' levantou:")
                traceback.print_exc()

    def clear(self) -> None:
        """Remove todos os listeners (usado em testes)."""
        with self._lock:
            self._listeners.clear()


# Singleton de processo. Importe `bus` em qualquer lugar.
bus = EventBus()
