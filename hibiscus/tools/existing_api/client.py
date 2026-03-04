"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Resilient HTTP client for existing EAZR Node.js API calls.
Circuit breaker, retries, exponential backoff, timeouts.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.existing_api.client")

# ── Timeout presets per operation type ─────────────────────────────────────────
TIMEOUTS: Dict[str, float] = {
    "extraction": 30.0,    # Large PDFs can take time
    "scoring": 10.0,       # Computation-heavy but bounded
    "reporting": 15.0,     # Report generation
    "compliance": 10.0,    # Rule-based check
    "billing": 10.0,       # Bill audit
    "default": 10.0,
}

MAX_RETRIES = 3
BACKOFF_BASE = 1.0        # seconds — doubles each retry (1, 2, 4)
CIRCUIT_BREAKER_THRESHOLD = 5    # failures before opening circuit
CIRCUIT_BREAKER_WINDOW = 60.0    # seconds — rolling window for failure tracking
CIRCUIT_BREAKER_RECOVERY = 30.0  # seconds — wait before half-open probe


@dataclass
class CircuitBreakerState:
    """Tracks failures to implement the circuit breaker pattern."""
    failures: list = field(default_factory=list)  # timestamps of recent failures
    opened_at: Optional[float] = None             # when circuit opened (None = closed)

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        elapsed = time.time() - self.opened_at
        if elapsed >= CIRCUIT_BREAKER_RECOVERY:
            # Half-open — allow one probe
            return False
        return True

    def record_failure(self) -> None:
        now = time.time()
        self.failures = [t for t in self.failures if now - t < CIRCUIT_BREAKER_WINDOW]
        self.failures.append(now)
        if len(self.failures) >= CIRCUIT_BREAKER_THRESHOLD:
            self.opened_at = now
            logger.warning(
                "circuit_breaker_opened",
                failures=len(self.failures),
                window_seconds=CIRCUIT_BREAKER_WINDOW,
            )

    def record_success(self) -> None:
        self.failures.clear()
        if self.opened_at is not None:
            logger.info("circuit_breaker_closed", recovery="probe succeeded")
            self.opened_at = None


# Module-level circuit breaker (shared across all calls to the existing API)
_circuit = CircuitBreakerState()


class ExistingAPIError(Exception):
    """Raised when the existing EAZR API is unreachable or returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


async def call_existing_api(
    method: str,
    path: str,
    *,
    operation: str = "default",
    json_body: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make a resilient HTTP call to the existing EAZR Node.js API.

    Args:
        method:    HTTP method (GET, POST, PUT, DELETE).
        path:      API path (e.g., "/api/v1/extract").
        operation: Operation name for timeout lookup and logging.
        json_body: JSON request body.
        files:     Multipart file upload dict.
        params:    URL query parameters.

    Returns:
        Parsed JSON response as dict.

    Raises:
        ExistingAPIError: On all failure modes after exhausting retries.
    """
    if _circuit.is_open:
        logger.warning("circuit_breaker_reject", operation=operation, path=path)
        raise ExistingAPIError(
            f"Circuit breaker is OPEN — the existing API has been unreachable. "
            f"I'm having trouble connecting to the analysis service right now. "
            f"Please try again in a moment.",
        )

    timeout = TIMEOUTS.get(operation, TIMEOUTS["default"])
    base_url = getattr(settings, "existing_api_base_url", "http://localhost:3000")
    url = f"{base_url}{path}"

    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "existing_api_call_start",
                operation=operation,
                method=method,
                path=path,
                attempt=attempt,
            )

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_body,
                    files=files,
                    params=params,
                )

            if response.status_code >= 500:
                raise ExistingAPIError(
                    f"Server error {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            if response.status_code >= 400:
                raise ExistingAPIError(
                    f"Client error {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            result = response.json()
            _circuit.record_success()
            logger.info(
                "existing_api_call_success",
                operation=operation,
                path=path,
                status=response.status_code,
                attempt=attempt,
            )
            return result

        except (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout) as exc:
            last_error = exc
            _circuit.record_failure()
            logger.warning(
                "existing_api_call_retry",
                operation=operation,
                path=path,
                attempt=attempt,
                error=str(exc),
            )
            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        except ExistingAPIError:
            _circuit.record_failure()
            raise

        except Exception as exc:
            last_error = exc
            _circuit.record_failure()
            logger.error(
                "existing_api_call_unexpected",
                operation=operation,
                path=path,
                attempt=attempt,
                error=str(exc),
            )
            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

    raise ExistingAPIError(
        f"I'm having trouble analyzing your document right now. "
        f"The analysis service didn't respond after {MAX_RETRIES} attempts. "
        f"Please try again shortly. (operation={operation}, error={last_error})",
    )
