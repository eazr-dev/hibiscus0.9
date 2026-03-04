"""
Hibiscus Structured Logger
==========================
Every pipeline step logs here. Where logs stop = where the pipeline is broken.

Every log entry includes:
  request_id, session_id, user_id, timestamp, level, component,
  agent_name (if applicable), model_used, tokens_in, tokens_out,
  latency_ms, confidence, message
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import logging
import sys
import time
from typing import Any, Optional

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON output in production, pretty in dev."""
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)

    # Standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_int,
    )

    # Structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(name)


class PipelineLogger:
    """
    Helper for logging Hibiscus pipeline steps consistently.
    Use at every node in the LangGraph.
    """

    def __init__(self, component: str, request_id: str, session_id: str, user_id: str):
        self._log = get_logger(component)
        self._component = component
        self._request_id = request_id
        self._session_id = session_id
        self._user_id = user_id
        self._start_time = time.time()

    def _base(self) -> dict[str, Any]:
        return {
            "request_id": self._request_id,
            "session_id": self._session_id,
            "user_id": self._user_id,
            "component": self._component,
        }

    def step_start(self, step: str, **kwargs: Any) -> None:
        self._log.info(f"{step}_start", **self._base(), **kwargs)

    def step_complete(
        self,
        step: str,
        latency_ms: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        if latency_ms is None:
            latency_ms = int((time.time() - self._start_time) * 1000)
        self._log.info(f"{step}_complete", latency_ms=latency_ms, **self._base(), **kwargs)

    def tool_call(self, tool: str, args_summary: str, **kwargs: Any) -> None:
        self._log.info(
            "tool_call",
            tool=tool,
            args_summary=args_summary,
            **self._base(),
            **kwargs,
        )

    def tool_result(
        self, tool: str, success: bool, latency_ms: int, **kwargs: Any
    ) -> None:
        self._log.info(
            "tool_result",
            tool=tool,
            success=success,
            latency_ms=latency_ms,
            **self._base(),
            **kwargs,
        )

    def agent_start(self, agent: str, model: str, task: str, **kwargs: Any) -> None:
        self._log.info(
            "agent_start",
            agent=agent,
            model=model,
            task=task,
            **self._base(),
            **kwargs,
        )

    def agent_complete(
        self,
        agent: str,
        confidence: float,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        **kwargs: Any,
    ) -> None:
        self._log.info(
            "agent_complete",
            agent=agent,
            confidence=confidence,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            **self._base(),
            **kwargs,
        )

    def guardrail(self, guardrail: str, passed: bool, reason: str = "", **kwargs: Any) -> None:
        level = "info" if passed else "warning"
        getattr(self._log, level)(
            "guardrail_check",
            guardrail=guardrail,
            passed=passed,
            reason=reason,
            **self._base(),
            **kwargs,
        )

    def error(self, step: str, error: str, **kwargs: Any) -> None:
        self._log.error(f"{step}_error", error=error, **self._base(), **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log.warning(msg, **self._base(), **kwargs)
