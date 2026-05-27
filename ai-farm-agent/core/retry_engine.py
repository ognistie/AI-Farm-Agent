"""
Retry Engine v2 — Recuperacao inteligente com backoff exponencial e
memoria de falhas recentes.

Mudancas vs v1:
- Backoff exponencial (2s, 4s, 8s) em vez de fixo
- Memoria de falhas em memoria (process-local): se mesma assinatura
  ja falhou 2x nesta sessao, escala direto (sem repetir hammering)
- _diagnose mais preciso: alem de WAIT/ALT/ESC/ABORT, adiciona
  "MUTATE" (mudar o action) quando o erro indica seletor/coord ruim
"""

from __future__ import annotations

import time
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger("retry_engine")


class RetryEngine:
    MAX_ATTEMPTS = 3
    BACKOFF_BASE_S = 2  # backoff = base * 2^attempt

    # Memoria process-local: assinatura -> count de falhas nesta sessao
    _failure_memory: dict[str, int] = defaultdict(int)

    def __init__(self, interaction_layer=None):
        self.il = interaction_layer

    # ── API publica ──────────────────────────────────────────────────

    def execute_with_retry(self, action_fn, action_params, context: str = ""):
        """Executa uma acao com retry inteligente + backoff exponencial."""
        last_error = None
        signature = self._signature(action_fn, action_params, context)

        # Curto-circuito: se ja falhou >=2x nesta sessao, escala direto
        if self._failure_memory[signature] >= 2:
            logger.warning(
                f"Assinatura ja falhou {self._failure_memory[signature]}x nesta sessao — "
                f"escalando sem retry: {context[:60]}"
            )
            return {
                "success": False,
                "error": "Acao bloqueada por historico de falhas (escalando metodo)",
                "escalate": True,
            }

        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if isinstance(action_params, dict):
                    result = action_fn(**action_params)
                else:
                    result = action_fn(action_params)

                if result.get("success"):
                    if attempt > 0:
                        logger.info(f"Sucesso na tentativa {attempt + 1}: {context}")
                        # Limpa memoria de falha para esta assinatura
                        self._failure_memory.pop(signature, None)
                    return result

                last_error = result.get("error", result.get("result", "Falha"))
                logger.warning(f"Tentativa {attempt + 1}/{self.MAX_ATTEMPTS} falhou: {last_error}")

                strategy = self._diagnose(str(last_error), context, attempt)

                if strategy["action"] == "WAIT_AND_RETRY":
                    wait_time = strategy.get(
                        "wait_time",
                        self.BACKOFF_BASE_S * (2 ** attempt),
                    )
                    time.sleep(wait_time)
                    continue
                elif strategy["action"] == "ALTERNATIVE_PATH":
                    self._try_close_blocking()
                    time.sleep(0.5)
                    continue
                elif strategy["action"] == "RECOVER_STATE":
                    self._recover_state()
                    time.sleep(1)
                    continue
                elif strategy["action"] == "MUTATE":
                    # Retorna para o caller mutar a acao (seletor/coord)
                    self._failure_memory[signature] += 1
                    return {"success": False, "error": last_error,
                            "mutate": True, "hint": strategy.get("hint", "")}
                elif strategy["action"] == "ESCALATE_METHOD":
                    self._failure_memory[signature] += 1
                    return {"success": False, "error": last_error, "escalate": True}
                elif strategy["action"] == "ABORT":
                    self._failure_memory[signature] += 1
                    return {"success": False, "error": last_error, "aborted": True}

            except Exception as e:
                last_error = str(e)
                logger.error(f"Excecao tentativa {attempt + 1}: {e}")
                time.sleep(self.BACKOFF_BASE_S * (2 ** attempt))

        # Esgotou retries — incrementa memoria
        self._failure_memory[signature] += 1
        return {
            "success": False,
            "error": f"Falhou apos {self.MAX_ATTEMPTS} tentativas: {last_error}",
        }

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _signature(action_fn, params, context: str) -> str:
        """Gera assinatura curta para memoria de falhas."""
        fn_name = getattr(action_fn, "__name__", str(action_fn))[:30]
        params_repr = str(params)[:80] if params else ""
        key = f"{fn_name}|{context[:40]}|{params_repr}"
        return hashlib.md5(key.encode()).hexdigest()[:10]

    def _diagnose(self, error: str, context: str, attempt: int) -> dict:
        """Diagnostica o tipo de falha e retorna estrategia."""
        e = error.lower()

        # Permissoes/crashes — abortar imediatamente
        if any(w in e for w in ("permission", "access denied", "crash", "nao responde")):
            return {"action": "ABORT"}

        # Elemento nao encontrado — primeiro tentar esperar, depois escalar
        if any(w in e for w in ("not found", "nao encontrad", "timeout", "nao apareceu",
                                "no such element")):
            if attempt == 0:
                return {"action": "WAIT_AND_RETRY",
                        "wait_time": self.BACKOFF_BASE_S * 2}
            return {"action": "ESCALATE_METHOD"}

        # Popups/modais — limpar antes de tentar de novo
        if any(w in e for w in ("blocked", "dialog", "popup", "modal", "cookie", "consent")):
            return {"action": "ALTERNATIVE_PATH"}

        # Foco/janela errada — recuperar estado
        if any(w in e for w in ("wrong window", "janela errada", "foco", "browser",
                                "out of frame")):
            return {"action": "RECOVER_STATE"}

        # Seletor/coord ruim — pedir mutacao
        if any(w in e for w in ("invalid selector", "stale element", "coord", "off screen",
                                "fora da tela", "seletor")):
            return {"action": "MUTATE",
                    "hint": "use seletor mais especifico ou coordenada validada"}

        # Padrao: esperar e tentar de novo com backoff
        return {"action": "WAIT_AND_RETRY",
                "wait_time": self.BACKOFF_BASE_S * (2 ** attempt)}

    def _try_close_blocking(self):
        """Tenta fechar popups/dialogs bloqueantes."""
        try:
            import pyautogui
            pyautogui.press("escape")
            time.sleep(0.3)
            pyautogui.press("escape")
        except Exception as e:
            logger.debug(f"close_blocking falhou (nao critico): {e}")

    def _recover_state(self):
        """Tenta voltar para um estado conhecido (Alt+Tab + Esc)."""
        try:
            import pyautogui
            pyautogui.press("escape")
            time.sleep(0.2)
        except Exception as e:
            logger.debug(f"recover_state falhou (nao critico): {e}")

    @classmethod
    def reset_memory(cls):
        """Limpa memoria de falhas (usado entre testes)."""
        cls._failure_memory.clear()
