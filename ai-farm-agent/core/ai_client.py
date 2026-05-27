"""
AI Client v2 — Cliente Anthropic centralizado com:
- Custo REAL por modelo (Haiku/Sonnet/Opus) — nao mais estimativa fixa
- Fallback automatico Sonnet -> Haiku em RateLimit/Timeout
- Retorna metadados de uso via `message_with_meta()`
- Singleton com metricas agregadas
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Optional

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIConnectionError

logger = logging.getLogger("ai_client")


# Precos por modelo (USD por 1M tokens) — Anthropic 2025
# https://www.anthropic.com/pricing
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Haiku 4.5
    "claude-haiku-4-5":       {"input": 0.25, "output": 1.25},
    # Sonnet 4 / 4.5
    "claude-sonnet-4":        {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5":      {"input": 3.00, "output": 15.00},
    # Opus 4
    "claude-opus-4":          {"input": 15.00, "output": 75.00},
}


def _pricing_for(model: str) -> dict[str, float]:
    """Retorna pricing do modelo, com fallback conservador se nao reconhecido."""
    m = (model or "").lower()
    for key, price in MODEL_PRICING.items():
        if m.startswith(key):
            return price
    # Fallback: usa Sonnet como conservador
    return MODEL_PRICING["claude-sonnet-4"]


# Modelos para fallback automatico em caso de erro transitorio
FALLBACK_CHAIN: dict[str, str] = {
    # Sonnet -> Haiku
    "claude-sonnet-4":   "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5": "claude-haiku-4-5-20251001",
    # Opus -> Sonnet
    "claude-opus-4":     "claude-sonnet-4-20250514",
}


def _fallback_for(model: str) -> Optional[str]:
    m = (model or "").lower()
    for key, fb in FALLBACK_CHAIN.items():
        if m.startswith(key):
            return fb
    return None


# ─────────────────────────────────────────────────────────────────────
#  Singleton
# ─────────────────────────────────────────────────────────────────────

_instance: Optional["AIClient"] = None


def get_client() -> "AIClient":
    global _instance
    if _instance is None:
        _instance = AIClient()
    return _instance


class AIClient:
    """Cliente centralizado para a API Anthropic."""

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nao configurada no .env")

        self._client = Anthropic(api_key=api_key)
        self._metrics: dict[str, Any] = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "calls_by_model": {},   # {model_short: {calls, in_tokens, out_tokens, cost_usd}}
            "errors": 0,
            "fallbacks": 0,
        }
        logger.info("AIClient v2 inicializado (custo real por modelo)")

    # ─── API publica ───────────────────────────────────────────────

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            **self._metrics,
            "total_cost_usd": round(self._metrics["total_cost_usd"], 6),
        }

    def message(self, model: str, system: str, user_content,
                max_tokens: int = 1500, images=None,
                allow_fallback: bool = True) -> str:
        """Wrapper que retorna apenas o texto (backward compat)."""
        result = self.message_with_meta(
            model=model, system=system, user_content=user_content,
            max_tokens=max_tokens, images=images, allow_fallback=allow_fallback,
        )
        return result["text"]

    def message_with_meta(self, model: str, system: str, user_content,
                          max_tokens: int = 1500, images=None,
                          allow_fallback: bool = True) -> dict[str, Any]:
        """
        Envia mensagem e retorna dict com {text, model_used, input_tokens,
        output_tokens, cost_usd, duration_ms, fellback}.
        """
        content = self._build_content(user_content, images)

        attempted_models = [model]
        last_error: Optional[Exception] = None
        fellback = False

        for attempt_model in attempted_models:
            start = time.time()
            for attempt in range(3):
                try:
                    resp = self._client.messages.create(
                        model=attempt_model,
                        max_tokens=max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": content}],
                    )
                    duration_ms = round((time.time() - start) * 1000)
                    return self._record_success(
                        resp, attempt_model, duration_ms, fellback=fellback,
                    )

                except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                    last_error = e
                    self._metrics["errors"] += 1
                    logger.warning(f"API transient error em {attempt_model} "
                                   f"(tent {attempt + 1}/3): {e}")
                    if attempt < 2:
                        time.sleep((2 ** attempt))  # backoff: 1s, 2s, 4s
                    continue

                except Exception as e:
                    last_error = e
                    self._metrics["errors"] += 1
                    logger.error(f"API erro definitivo: {e}")
                    break  # erro nao recuperavel, sai do retry

            # Esgotou retries deste modelo — considerar fallback
            if allow_fallback:
                fb = _fallback_for(attempt_model)
                if fb and fb not in attempted_models:
                    logger.warning(f"Caindo para fallback: {attempt_model} -> {fb}")
                    attempted_models.append(fb)
                    self._metrics["fallbacks"] += 1
                    fellback = True

        if last_error:
            raise last_error
        raise RuntimeError("Falha desconhecida em AIClient.message_with_meta")

    # ─── Helpers internos ──────────────────────────────────────────

    def _build_content(self, user_content, images) -> list:
        """Monta content blocks (texto + imagens opcionais)."""
        if isinstance(user_content, str):
            content: list = []
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
            return content
        return user_content

    def _record_success(self, resp, model: str, duration_ms: int,
                        fellback: bool) -> dict[str, Any]:
        """Registra metricas e retorna meta-dict."""
        usage = getattr(resp, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        pricing = _pricing_for(model)
        cost = (input_tokens * pricing["input"]
                + output_tokens * pricing["output"]) / 1_000_000

        # Metricas globais
        self._metrics["total_calls"] += 1
        self._metrics["total_input_tokens"] += input_tokens
        self._metrics["total_output_tokens"] += output_tokens
        self._metrics["total_cost_usd"] += cost

        # Metricas por modelo
        short = self._short_name(model)
        per = self._metrics["calls_by_model"].setdefault(
            short, {"calls": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0}
        )
        per["calls"] += 1
        per["in_tokens"] += input_tokens
        per["out_tokens"] += output_tokens
        per["cost_usd"] = round(per["cost_usd"] + cost, 6)

        text = resp.content[0].text.strip() if resp.content else ""
        logger.debug(
            f"API {short} | in={input_tokens} out={output_tokens} "
            f"${cost:.5f} | {duration_ms}ms"
        )

        return {
            "text": text,
            "model_used": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "duration_ms": duration_ms,
            "fellback": fellback,
        }

    @staticmethod
    def _short_name(model: str) -> str:
        """claude-haiku-4-5-20251001 -> haiku-4-5"""
        parts = model.split("-")
        # Pega 'haiku-4-5' ou 'sonnet-4' etc.
        if len(parts) >= 3:
            return "-".join(parts[1:3])
        return model
