"""
AI Client — Cliente Anthropic centralizado.
Uma única instância compartilhada por todos os agentes.
Benefícios: connection pooling, métricas unificadas, troca de provider em 1 lugar.
"""

import os
import time
import logging
from anthropic import Anthropic

logger = logging.getLogger("ai_client")

# ══════════════════════════════════════════
#  Singleton — uma única instância global
# ══════════════════════════════════════════

_instance = None


def get_client():
    """Retorna a instância única do AIClient."""
    global _instance
    if _instance is None:
        _instance = AIClient()
    return _instance


class AIClient:
    """Cliente centralizado para a API Anthropic."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada no .env")

        self._client = Anthropic(api_key=api_key)
        self._metrics = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "calls_by_model": {},
            "errors": 0,
        }
        logger.info("AIClient inicializado")

    @property
    def metrics(self):
        """Retorna métricas de uso da API."""
        return {
            **self._metrics,
            "estimated_cost_usd": self._estimate_cost(),
        }

    def message(self, model, system, user_content, max_tokens=1500, images=None):
        """
        Envia mensagem para a API e retorna a resposta.

        Args:
            model: nome do modelo (ex: "claude-haiku-4-5-20251001")
            system: system prompt
            user_content: texto do usuário (str) ou lista de content blocks
            max_tokens: máximo de tokens na resposta
            images: lista de dicts {"base64": str, "media_type": str} (opcional)

        Returns:
            str com o texto da resposta
        """
        # Constrói content blocks
        if isinstance(user_content, str):
            content = []
            if images:
                for img in images:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img.get("media_type", "image/png"),
                            "data": img["base64"],
                        },
                    })
            content.append({"type": "text", "text": user_content})
        else:
            content = user_content

        # Chama a API com retry
        start = time.time()
        last_error = None

        for attempt in range(3):
            try:
                resp = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": content}],
                )

                # Métricas
                self._metrics["total_calls"] += 1
                input_tokens = getattr(resp.usage, "input_tokens", 0)
                output_tokens = getattr(resp.usage, "output_tokens", 0)
                self._metrics["total_input_tokens"] += input_tokens
                self._metrics["total_output_tokens"] += output_tokens

                model_key = model.split("-")[1] if "-" in model else model
                if model_key not in self._metrics["calls_by_model"]:
                    self._metrics["calls_by_model"][model_key] = 0
                self._metrics["calls_by_model"][model_key] += 1

                duration = round((time.time() - start) * 1000)
                logger.debug(f"API call: {model} | {input_tokens}+{output_tokens} tokens | {duration}ms")

                return resp.content[0].text.strip()

            except Exception as e:
                last_error = e
                self._metrics["errors"] += 1
                logger.warning(f"API error (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))

        raise last_error

    def _estimate_cost(self):
        """Estima custo baseado nos tokens consumidos."""
        # Preços aproximados (USD por 1M tokens)
        # Haiku: $0.25 input, $1.25 output
        # Sonnet: $3 input, $15 output
        # Estimativa conservadora usando média
        input_cost = self._metrics["total_input_tokens"] * 1.5 / 1_000_000
        output_cost = self._metrics["total_output_tokens"] * 8.0 / 1_000_000
        return round(input_cost + output_cost, 4)
