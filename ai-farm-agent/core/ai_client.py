"""
AI Client v3 — Cliente Anthropic centralizado.

Todas as chamadas ao modelo (agentes, visao, narrador, reparo de JSON)
passam por aqui. Isso garante:
- Custo REAL por modelo, incluindo leitura/escrita de prompt cache
- Prompt caching automatico do system prompt (prefixo estavel)
- `effort` por agente (Sonnet 5: adaptive thinking ligado por padrao)
- Streaming interno (evita timeout HTTP com max_tokens alto)
- Texto extraido so dos blocos `text` (Sonnet 5 devolve blocos `thinking`
  antes do texto — `content[0].text` quebraria)
- Singleton com metricas agregadas
"""

from __future__ import annotations

import copy
import os
import time
import logging
from typing import Any, Optional

from anthropic import Anthropic, APIError, Timeout

logger = logging.getLogger("ai_client")


# Precos por modelo (USD por 1M tokens). Prefixo mais longo vence.
# Fonte: tabela de modelos da Anthropic (2026).
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-5":   {"input": 2.00, "output": 10.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4":   {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input": 1.00, "output": 5.00},
    "claude-opus-5":     {"input": 5.00, "output": 25.00},
    "claude-opus-4":     {"input": 15.00, "output": 75.00},
}

# Multiplicadores do prompt cache sobre o preco de input (TTL de 5 min).
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10

# Modelos que aceitam `output_config.effort`. Em modelos fora desta lista
# o parametro e omitido (ex.: Haiku 4.5 devolve 400 com effort).
_EFFORT_MODELS = (
    "claude-sonnet-5", "claude-sonnet-4-6",
    "claude-opus-5", "claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8",
    "claude-fable",
)


def _pricing_for(model: str) -> dict[str, float]:
    """Pricing do modelo; se desconhecido, usa Sonnet 5."""
    m = (model or "").lower()
    matches = [k for k in MODEL_PRICING if m.startswith(k)]
    if matches:
        return MODEL_PRICING[max(matches, key=len)]
    return MODEL_PRICING["claude-sonnet-5"]


def _supports_effort(model: str) -> bool:
    return (model or "").lower().startswith(_EFFORT_MODELS)


def estimate_cost(model: str, input_tokens: int, output_tokens: int,
                  cache_read_tokens: int = 0, cache_write_tokens: int = 0) -> float:
    """Custo em USD de uma chamada, contando o prompt cache."""
    p = _pricing_for(model)
    return (
        input_tokens * p["input"]
        + cache_write_tokens * p["input"] * CACHE_WRITE_MULTIPLIER
        + cache_read_tokens * p["input"] * CACHE_READ_MULTIPLIER
        + output_tokens * p["output"]
    ) / 1_000_000


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

        # O SDK ja faz retry com backoff em 408/409/429/5xx e erros de rede.
        # Timeout de leitura curto: em streaming ele vale ENTRE pedacos da
        # resposta. Sem ele, uma conexao engasgada deixava a tarefa parada
        # em "Analisando" por ate 10 minutos (default do SDK).
        self._client = Anthropic(
            api_key=api_key, max_retries=2,
            timeout=Timeout(180.0, connect=10.0, read=60.0),
        )
        self._metrics: dict[str, Any] = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cache_read_tokens": 0,
            "total_cache_write_tokens": 0,
            "total_cost_usd": 0.0,
            "calls_by_model": {},   # {model_short: {calls, in_tokens, out_tokens, cost_usd}}
            "calls_by_agent": {},   # {agent: {calls, cost_usd}}
            "errors": 0,
            "truncated": 0,
        }
        logger.info("AIClient v3 inicializado (cache + effort + custo real)")

    # ─── API publica ───────────────────────────────────────────────

    @property
    def metrics(self) -> dict[str, Any]:
        """Copia profunda — quem guarda um snapshot nao ve alteracoes futuras."""
        snapshot = copy.deepcopy(self._metrics)
        snapshot["total_cost_usd"] = round(snapshot["total_cost_usd"], 6)
        return snapshot

    def message(self, model: str, system: str, user_content,
                max_tokens: int = 8000, images=None,
                effort: Optional[str] = None, agent: str = "") -> str:
        """Wrapper que retorna apenas o texto."""
        return self.message_with_meta(
            model=model, system=system, user_content=user_content,
            max_tokens=max_tokens, images=images, effort=effort, agent=agent,
        )["text"]

    def message_with_meta(self, model: str, system: str, user_content,
                          max_tokens: int = 8000, images=None,
                          effort: Optional[str] = None,
                          agent: str = "") -> dict[str, Any]:
        """
        Envia mensagem e retorna {text, model_used, input_tokens,
        output_tokens, cache_read_tokens, cache_write_tokens, cost_usd,
        duration_ms, stop_reason}.
        """
        params: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user",
                          "content": self._build_content(user_content, images)}],
        }
        if system:
            # System prompt e o prefixo estavel de cada agente: marcado para
            # cache. Abaixo do minimo cacheavel (1024 tokens no Sonnet 5) a
            # API simplesmente nao cacheia — sem custo extra.
            params["system"] = [{"type": "text", "text": system,
                                 "cache_control": {"type": "ephemeral"}}]
        if effort and _supports_effort(model):
            params["output_config"] = {"effort": effort}

        start = time.time()
        try:
            with self._client.messages.stream(**params) as stream:
                resp = stream.get_final_message()
        except APIError as e:
            self._metrics["errors"] += 1
            logger.error(f"API erro ({agent or 'sem agente'}): {e}")
            raise

        duration_ms = round((time.time() - start) * 1000)

        if resp.stop_reason == "refusal":
            self._metrics["errors"] += 1
            details = getattr(resp, "stop_details", None)
            category = getattr(details, "category", None) if details else None
            raise RuntimeError(f"Modelo recusou a tarefa (categoria: {category})")
        if resp.stop_reason == "max_tokens":
            self._metrics["truncated"] += 1
            logger.warning(f"Resposta truncada em max_tokens={max_tokens} "
                           f"({agent or model})")

        return self._record_success(resp, model, duration_ms, agent)

    # ─── Helpers internos ──────────────────────────────────────────

    def _build_content(self, user_content, images) -> list:
        """Monta content blocks (imagens opcionais + texto)."""
        if not isinstance(user_content, str):
            return user_content
        content: list = []
        for img in images or []:
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

    def _record_success(self, resp, model: str, duration_ms: int,
                        agent: str) -> dict[str, Any]:
        """Registra metricas e retorna meta-dict."""
        usage = resp.usage
        input_tokens = usage.input_tokens or 0
        output_tokens = usage.output_tokens or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0

        cost = estimate_cost(model, input_tokens, output_tokens,
                             cache_read, cache_write)

        m = self._metrics
        m["total_calls"] += 1
        m["total_input_tokens"] += input_tokens
        m["total_output_tokens"] += output_tokens
        m["total_cache_read_tokens"] += cache_read
        m["total_cache_write_tokens"] += cache_write
        m["total_cost_usd"] += cost

        short = self._short_name(model)
        per = m["calls_by_model"].setdefault(
            short, {"calls": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0}
        )
        per["calls"] += 1
        per["in_tokens"] += input_tokens
        per["out_tokens"] += output_tokens
        per["cost_usd"] = round(per["cost_usd"] + cost, 6)

        if agent:
            per_agent = m["calls_by_agent"].setdefault(
                agent, {"calls": 0, "cost_usd": 0.0}
            )
            per_agent["calls"] += 1
            per_agent["cost_usd"] = round(per_agent["cost_usd"] + cost, 6)

        # Sonnet 5 devolve blocos `thinking` antes do texto — so o texto importa.
        text = "".join(
            b.text for b in resp.content if getattr(b, "type", "") == "text"
        ).strip()
        logger.debug(
            f"API {short} [{agent}] | in={input_tokens} cache_r={cache_read} "
            f"cache_w={cache_write} out={output_tokens} ${cost:.5f} | {duration_ms}ms"
        )

        return {
            "text": text,
            "model_used": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read,
            "cache_write_tokens": cache_write,
            "cost_usd": round(cost, 6),
            "duration_ms": duration_ms,
            "stop_reason": resp.stop_reason,
        }

    @staticmethod
    def _short_name(model: str) -> str:
        """claude-sonnet-5 -> sonnet-5 ; claude-haiku-4-5-20251001 -> haiku-4-5"""
        parts = model.split("-")
        if len(parts) >= 4 and parts[3].isdigit() and len(parts[3]) <= 2:
            return "-".join(parts[1:4])
        if len(parts) >= 3:
            return "-".join(parts[1:3])
        return model
