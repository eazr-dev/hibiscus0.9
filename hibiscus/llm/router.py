"""
Hibiscus LLM Router
===================
LiteLLM-based tiered routing:
  Tier 1: DeepSeek V3.2 — 80% of calls (primary)
  Tier 2: DeepSeek R1   — 15% of calls (complex reasoning)
  Tier 3: Claude Sonnet — 5% of calls  (safety net / fallback)

Fallback chain: DeepSeek V3.2 → DeepSeek R1 → Claude Sonnet
"""
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import litellm
from litellm import acompletion, completion_cost

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger
from hibiscus.observability.cost_tracker import track_llm_call

logger = get_logger(__name__)

# Configure LiteLLM
litellm.set_verbose = False
if settings.has_langsmith:
    litellm.success_callback = ["langsmith"]

# ── Provider configurations ────────────────────────────────────────────────

_PROVIDER_CONFIG = {
    "deepseek_v3": {
        "model": settings.deepseek_v3_model,
        "api_key": settings.deepseek_api_key,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
    },
    "deepseek_r1": {
        "model": settings.deepseek_r1_model,
        "api_key": settings.deepseek_api_key,
        "temperature": 0.5,  # R1 reasoning needs some creativity
        "max_tokens": settings.reasoning_max_tokens,
        "timeout": settings.reasoning_timeout,
    },
    "claude_sonnet": {
        "model": settings.claude_sonnet_model,
        "api_key": settings.anthropic_api_key,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
    },
}

# Fallback chain: try these in order on failure
_FALLBACK_CHAIN = ["deepseek_v3", "deepseek_r1", "claude_sonnet"]


async def call_llm(
    messages: List[Dict[str, str]],
    tier: str = "deepseek_v3",
    conversation_id: str = "unknown",
    agent: str = "unknown",
    stream: bool = False,
    extra_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make a tiered LLM call with automatic fallback.

    Args:
        messages: Chat messages in OpenAI format
        tier: "deepseek_v3" | "deepseek_r1" | "claude_sonnet"
        conversation_id: For cost tracking
        agent: Agent name for logging
        stream: Whether to stream (returns async generator)
        extra_kwargs: Additional LiteLLM kwargs

    Returns:
        {content, model, tokens_in, tokens_out, cost_usd}
    """
    providers_to_try = _get_fallback_sequence(tier)

    last_error: Optional[Exception] = None
    for provider in providers_to_try:
        config = _PROVIDER_CONFIG[provider].copy()
        if extra_kwargs:
            config.update(extra_kwargs)

        # Skip if no API key
        if not config.get("api_key"):
            logger.warning(
                "llm_provider_skipped",
                provider=provider,
                reason="no_api_key",
                agent=agent,
            )
            continue

        try:
            start = time.time()
            logger.info(
                "llm_call_start",
                provider=provider,
                model=config["model"],
                agent=agent,
                conversation_id=conversation_id,
            )

            response = await acompletion(
                messages=messages,
                model=config["model"],
                api_key=config["api_key"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                timeout=config["timeout"],
                stream=stream,
            )

            latency_ms = int((time.time() - start) * 1000)
            content = response.choices[0].message.content or ""
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0

            # Track cost
            track_llm_call(
                conversation_id=conversation_id,
                model=config["model"],
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                agent=agent,
            )

            logger.info(
                "llm_call_complete",
                provider=provider,
                model=config["model"],
                agent=agent,
                conversation_id=conversation_id,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
            )

            return {
                "content": content,
                "model": config["model"],
                "provider": provider,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            last_error = e
            logger.warning(
                "llm_provider_failed",
                provider=provider,
                model=config.get("model", "unknown"),
                error=str(e),
                agent=agent,
            )
            # Continue to next provider in fallback chain

    # All providers failed
    raise RuntimeError(
        f"All LLM providers exhausted. Last error: {last_error}. "
        f"Check API keys: DeepSeek={settings.has_deepseek}, Anthropic={settings.has_anthropic}"
    )


async def stream_llm(
    messages: List[Dict[str, str]],
    tier: str = "deepseek_v3",
    conversation_id: str = "unknown",
    agent: str = "unknown",
) -> AsyncIterator[str]:
    """
    Stream LLM response tokens as they arrive.
    Yields string chunks for SSE/WebSocket streaming.
    """
    providers_to_try = _get_fallback_sequence(tier)

    for provider in providers_to_try:
        config = _PROVIDER_CONFIG[provider].copy()
        if not config.get("api_key"):
            continue

        try:
            response = await acompletion(
                messages=messages,
                model=config["model"],
                api_key=config["api_key"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                timeout=config["timeout"],
                stream=True,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return  # Success — stop trying providers

        except Exception as e:
            logger.warning(
                "llm_stream_provider_failed",
                provider=provider,
                error=str(e),
            )

    raise RuntimeError("All LLM providers failed for streaming")


def _get_fallback_sequence(requested_tier: str) -> List[str]:
    """Get ordered list of providers to try, starting from requested tier."""
    chain = _FALLBACK_CHAIN
    if requested_tier in chain:
        start_idx = chain.index(requested_tier)
        return chain[start_idx:]
    return chain
