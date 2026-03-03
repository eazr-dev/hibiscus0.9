"""
Hibiscus Load Test Scaffold
============================
Sends concurrent requests to the Hibiscus chat API and measures latency
distribution across the four complexity tiers (L1–L4).

The script drives load for a fixed duration and collects per-request wall-clock
latency.  At the end it prints a table of P50/P95/P99 latency and error counts
per tier — giving enough signal to verify Phase 3 latency targets:

    L1/L2  →  P95 < 5s
    L3/L4  →  P95 < 15s

Usage:
    python hibiscus/tests/load/load_test.py
    python hibiscus/tests/load/load_test.py --host localhost --port 8001
    python hibiscus/tests/load/load_test.py --n 50 --duration 30
    python hibiscus/tests/load/load_test.py --host localhost --port 8001 --n 100 --duration 60

Arguments:
    --host        Hibiscus API host (default: localhost)
    --port        Hibiscus API port (default: 8001)
    --n           Number of concurrent workers per batch (default: 20)
    --duration    How many seconds to run the test (default: 60)
    --tier        Restrict to a single tier: L1 | L2 | L3 | L4 (default: all)
    --timeout     Per-request timeout in seconds (default: 90)
    --no-stream   Disable streaming and use standard JSON response (default: streaming on)

No dependencies beyond httpx (already in pyproject.toml) and the Python stdlib.
"""

import argparse
import asyncio
import statistics
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Request payloads per tier ─────────────────────────────────────────────────
# Each entry is a (tier_label, message_template).
# {i} is replaced by the worker index so each request gets a unique session_id.

_TIER_MESSAGES: Dict[str, str] = {
    "L1": "What is co-payment in health insurance?",
    "L2": (
        "Explain the difference between term life insurance and whole life insurance "
        "in detail, including the tax implications under Indian tax law."
    ),
    "L3": (
        "Analyze my uploaded health insurance policy and compare it with the "
        "HDFC Optima Secure plan. Highlight coverage gaps and premium differences."
    ),
    "L4": (
        "I am 45 years old, have Type-2 diabetes, and currently pay ₹28,000 per year "
        "for an individual health plan with ₹5 lakh sum insured. Should I buy a super "
        "top-up policy or switch to a comprehensive plan? Also tell me the tax benefit "
        "I can claim under 80D."
    ),
}

# Phase 3 SLA targets (seconds, P95)
_SLA_TARGETS_P95: Dict[str, float] = {
    "L1": 5.0,
    "L2": 5.0,
    "L3": 15.0,
    "L4": 15.0,
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class RequestResult:
    tier: str
    latency_s: float
    status_code: int
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and 200 <= self.status_code < 300


@dataclass
class TierSummary:
    tier: str
    latencies: List[float] = field(default_factory=list)
    error_count: int = 0
    total_count: int = 0

    def add(self, result: RequestResult) -> None:
        self.total_count += 1
        if result.success:
            self.latencies.append(result.latency_s)
        else:
            self.error_count += 1

    def percentile(self, p: float) -> Optional[float]:
        """Return the p-th percentile of successful-request latencies."""
        if not self.latencies:
            return None
        # statistics.quantiles requires at least 2 data points for n=100;
        # for a single data point just return it.
        if len(self.latencies) == 1:
            return self.latencies[0]
        # quantiles(data, n=100) returns 99 cut-points for percentiles 1..99.
        # index = p-1  (0-indexed into the list of 99 cut-points)
        cuts = statistics.quantiles(self.latencies, n=100)
        idx = max(0, min(int(p) - 1, len(cuts) - 1))
        return cuts[idx]

    @property
    def p50(self) -> Optional[float]:
        return self.percentile(50)

    @property
    def p95(self) -> Optional[float]:
        return self.percentile(95)

    @property
    def p99(self) -> Optional[float]:
        return self.percentile(99)

    @property
    def success_count(self) -> int:
        return len(self.latencies)


# ── Single request sender ─────────────────────────────────────────────────────

async def _send_request(
    client,
    base_url: str,
    tier: str,
    worker_id: int,
    use_stream: bool,
    timeout: float,
) -> RequestResult:
    """Send one chat request and return timing + result."""
    session_id = f"lt_{tier}_{worker_id}_{uuid.uuid4().hex[:8]}"
    payload = {
        "message": _TIER_MESSAGES[tier],
        "user_id": "load_test_user",
        "session_id": session_id,
        "stream": use_stream,
    }

    start = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url}/hibiscus/chat",
            json=payload,
            timeout=timeout,
        )
        latency_s = time.perf_counter() - start

        if response.status_code >= 400:
            return RequestResult(
                tier=tier,
                latency_s=latency_s,
                status_code=response.status_code,
                error=f"HTTP {response.status_code}",
            )

        return RequestResult(tier=tier, latency_s=latency_s, status_code=response.status_code)

    except asyncio.TimeoutError:
        latency_s = time.perf_counter() - start
        return RequestResult(tier=tier, latency_s=latency_s, status_code=0, error="timeout")
    except Exception as exc:
        latency_s = time.perf_counter() - start
        return RequestResult(tier=tier, latency_s=latency_s, status_code=0, error=str(exc))


# ── Load test runner ──────────────────────────────────────────────────────────

async def run_load_test(
    base_url: str,
    n_concurrent: int,
    duration_seconds: int,
    tiers: List[str],
    use_stream: bool = True,
    timeout: float = 90.0,
) -> Dict[str, TierSummary]:
    """
    Drive concurrent load against the Hibiscus chat API for duration_seconds.

    Args:
        base_url:         Base URL e.g. "http://localhost:8001"
        n_concurrent:     Number of concurrent workers per batch
        duration_seconds: How long to sustain load (wall-clock seconds)
        tiers:            List of tier labels to include, e.g. ["L1", "L2"]
        use_stream:       Whether to request streaming responses
        timeout:          Per-request timeout in seconds

    Returns:
        Dict mapping tier label to TierSummary with collected latencies.
    """
    summaries: Dict[str, TierSummary] = {t: TierSummary(tier=t) for t in tiers}
    results: List[RequestResult] = []
    deadline = time.monotonic() + duration_seconds
    batch_num = 0

    import httpx

    # Use a single AsyncClient with connection pooling across all requests.
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=n_concurrent * 2, max_keepalive_connections=n_concurrent),
        timeout=httpx.Timeout(timeout),
    ) as client:
        while time.monotonic() < deadline:
            batch_num += 1
            # Distribute workers round-robin across tiers
            batch_tiers = [tiers[i % len(tiers)] for i in range(n_concurrent)]

            tasks = [
                _send_request(
                    client=client,
                    base_url=base_url,
                    tier=batch_tiers[i],
                    worker_id=(batch_num * n_concurrent) + i,
                    use_stream=use_stream,
                    timeout=timeout,
                )
                for i in range(n_concurrent)
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in batch_results:
                if isinstance(r, Exception):
                    # gather() with return_exceptions=True — treat as error result
                    for tier in tiers:
                        err_result = RequestResult(
                            tier=tier, latency_s=0.0, status_code=0, error=str(r)
                        )
                        results.append(err_result)
                        summaries[tier].add(err_result)
                    break
                results.append(r)
                summaries[r.tier].add(r)

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break

            # Brief yield to avoid tight-looping when requests are very fast
            await asyncio.sleep(0)

    print(f"\nLoad test complete: {len(results)} requests in {duration_seconds}s "
          f"({batch_num} batches of {n_concurrent} workers)")

    return summaries


# ── Results printer ───────────────────────────────────────────────────────────

def print_results(results: Dict[str, TierSummary]) -> None:
    """Print a formatted latency table with SLA pass/fail indicators."""
    col_w = [6, 12, 10, 8, 8, 8, 10, 6]
    headers = ["Tier", "Requests", "Success%", "P50(s)", "P95(s)", "P99(s)", "SLA P95", "Pass"]
    sep = "+-" + "-+-".join("-" * w for w in col_w) + "-+"

    def fmt(val, width):
        return str(val).ljust(width) if isinstance(val, str) else f"{val:.2f}".ljust(width)

    print("\n" + sep)
    print("| " + " | ".join(h.ljust(col_w[i]) for i, h in enumerate(headers)) + " |")
    print(sep)

    all_pass = True
    for tier in sorted(results.keys()):
        s = results[tier]
        if s.total_count == 0:
            continue

        success_pct = (s.success_count / s.total_count * 100) if s.total_count else 0.0
        p50 = s.p50
        p95 = s.p95
        p99 = s.p99
        sla = _SLA_TARGETS_P95.get(tier, 15.0)

        p50_str = f"{p50:.2f}" if p50 is not None else "n/a"
        p95_str = f"{p95:.2f}" if p95 is not None else "n/a"
        p99_str = f"{p99:.2f}" if p99 is not None else "n/a"

        if p95 is not None:
            passed = p95 <= sla
            pass_str = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
        else:
            pass_str = "n/a"

        row = [
            tier,
            f"{s.success_count}/{s.total_count}",
            f"{success_pct:.1f}%",
            p50_str,
            p95_str,
            p99_str,
            f"<{sla:.0f}s",
            pass_str,
        ]
        print("| " + " | ".join(str(v).ljust(col_w[i]) for i, v in enumerate(row)) + " |")

    print(sep)

    # Summary line
    total_requests = sum(s.total_count for s in results.values())
    total_errors = sum(s.error_count for s in results.values())
    print(f"\nTotal requests: {total_requests}  |  Errors: {total_errors}  |  "
          f"Overall SLA: {'ALL PASS' if all_pass else 'SOME FAIL'}")

    if total_errors > 0:
        print(f"\nWarning: {total_errors} error(s) encountered. "
              "Check that hibiscus-api is running and reachable.")


# ── Health check ──────────────────────────────────────────────────────────────

async def check_health(base_url: str, timeout: float = 10.0) -> bool:
    """Verify the API is reachable before starting the load test."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{base_url}/hibiscus/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"API health: {data.get('status', 'unknown')} "
                      f"(version {data.get('version', '?')})")
                return True
            print(f"Warning: health check returned HTTP {resp.status_code}")
            return False
    except Exception as exc:
        print(f"Error: cannot reach {base_url}/hibiscus/health — {exc}")
        return False


# ── CLI entry point ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hibiscus load test scaffold — measures P50/P95/P99 latency per tier.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick smoke test (20 workers, 30 seconds, all tiers):
  python hibiscus/tests/load/load_test.py --duration 30

  # Full Phase 3 load test (100 workers, 60 seconds):
  python hibiscus/tests/load/load_test.py --n 100 --duration 60

  # L1-only latency check:
  python hibiscus/tests/load/load_test.py --tier L1 --duration 20

  # Non-streaming responses:
  python hibiscus/tests/load/load_test.py --no-stream --duration 30
        """,
    )
    parser.add_argument("--host", default="localhost", help="Hibiscus API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="Hibiscus API port (default: 8001)")
    parser.add_argument(
        "--n", type=int, default=20,
        help="Number of concurrent workers per batch (default: 20)",
    )
    parser.add_argument(
        "--duration", type=int, default=60,
        help="Test duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--tier",
        choices=["L1", "L2", "L3", "L4"],
        default=None,
        help="Restrict to a single tier (default: all tiers)",
    )
    parser.add_argument(
        "--timeout", type=float, default=90.0,
        help="Per-request timeout in seconds (default: 90)",
    )
    parser.add_argument(
        "--no-stream", action="store_true", dest="no_stream",
        help="Use standard JSON responses instead of streaming SSE (default: streaming)",
    )
    parser.add_argument(
        "--skip-health-check", action="store_true",
        help="Skip the initial health check and start load immediately",
    )
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    base_url = f"http://{args.host}:{args.port}"
    tiers = [args.tier] if args.tier else list(_TIER_MESSAGES.keys())
    use_stream = not args.no_stream

    print("=" * 60)
    print("Hibiscus Load Test")
    print("=" * 60)
    print(f"  Target:      {base_url}")
    print(f"  Tiers:       {', '.join(tiers)}")
    print(f"  Workers:     {args.n} concurrent per batch")
    print(f"  Duration:    {args.duration}s")
    print(f"  Timeout:     {args.timeout}s per request")
    print(f"  Streaming:   {'yes' if use_stream else 'no'}")
    print("=" * 60)

    # Health check
    if not args.skip_health_check:
        healthy = await check_health(base_url)
        if not healthy:
            print("\nAborting: API health check failed. Use --skip-health-check to override.")
            return
    print()

    # Run
    start_wall = time.monotonic()
    summaries = await run_load_test(
        base_url=base_url,
        n_concurrent=args.n,
        duration_seconds=args.duration,
        tiers=tiers,
        use_stream=use_stream,
        timeout=args.timeout,
    )
    elapsed = time.monotonic() - start_wall

    # Report
    print_results(summaries)
    print(f"\nWall-clock elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(_main())
