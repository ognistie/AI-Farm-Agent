"""
Retry Engine — Recuperacao inteligente de falhas com estrategias alternativas.
"""

import time
import logging

logger = logging.getLogger("retry_engine")


class RetryEngine:
    MAX_ATTEMPTS = 3

    def __init__(self, interaction_layer=None):
        self.il = interaction_layer

    def execute_with_retry(self, action_fn, action_params, context=""):
        """Executa uma acao com retry inteligente."""
        last_error = None

        for attempt in range(self.MAX_ATTEMPTS):
            try:
                result = action_fn(**action_params) if isinstance(action_params, dict) else action_fn(action_params)

                if result.get("success"):
                    if attempt > 0:
                        logger.info(f"Sucesso na tentativa {attempt + 1}: {context}")
                    return result

                last_error = result.get("error", result.get("result", "Falha"))
                logger.warning(f"Tentativa {attempt + 1} falhou: {last_error}")

                strategy = self._diagnose(str(last_error), context, attempt)

                if strategy["action"] == "WAIT_AND_RETRY":
                    time.sleep(strategy.get("wait_time", 2))
                    continue
                elif strategy["action"] == "ALTERNATIVE_PATH":
                    self._try_close_blocking()
                    continue
                elif strategy["action"] == "RECOVER_STATE":
                    self._recover_state()
                    continue
                elif strategy["action"] == "ESCALATE_METHOD":
                    # Retorna para que o caller tente outro metodo
                    return {"success": False, "error": last_error, "escalate": True}
                elif strategy["action"] == "ABORT":
                    return {"success": False, "error": last_error, "aborted": True}

            except Exception as e:
                last_error = str(e)
                logger.error(f"Excecao tentativa {attempt + 1}: {e}")
                time.sleep(1)

        return {"success": False, "error": f"Falhou apos {self.MAX_ATTEMPTS} tentativas: {last_error}"}

    def _diagnose(self, error, context, attempt):
        """Diagnostica o tipo de falha e retorna estrategia."""
        e = error.lower()

        if any(w in e for w in ["not found", "nao encontrad", "timeout", "nao apareceu"]):
            return {"action": "WAIT_AND_RETRY", "wait_time": 3} if attempt == 0 else {"action": "ESCALATE_METHOD"}

        if any(w in e for w in ["blocked", "dialog", "popup", "modal"]):
            return {"action": "ALTERNATIVE_PATH"}

        if any(w in e for w in ["wrong window", "janela errada", "foco", "browser"]):
            return {"action": "RECOVER_STATE"}

        if any(w in e for w in ["permission", "access denied", "crash", "nao responde"]):
            return {"action": "ABORT"}

        return {"action": "WAIT_AND_RETRY", "wait_time": 2}

    def _try_close_blocking(self):
        """Tenta fechar popups/dialogs bloqueantes."""
        try:
            import pyautogui
            pyautogui.press("escape")
            time.sleep(0.5)
        except:
            pass

    def _recover_state(self):
        """Tenta voltar para estado conhecido."""
        try:
            import pyautogui
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.5)
            pyautogui.press("escape")
            time.sleep(0.3)
        except:
            pass