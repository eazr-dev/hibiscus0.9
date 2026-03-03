"""
HibiscusBench Evaluator
========================
Runs test cases against a live Hibiscus endpoint and scores responses.

Usage:
    # Evaluate all test cases
    evaluator = HibiscusEvaluator(base_url="http://localhost:8001")
    results = await evaluator.run_suite()

    # Evaluate specific category
    results = await evaluator.run_category("life")

    # Evaluate single test case
    result = await evaluator.run_test_case(test_case)
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Optional
import httpx
from .metrics import evaluate_response, aggregate_results, EvalResult
from ..observability.logger import get_logger

logger = get_logger("evaluation.evaluator")

TEST_CASES_DIR = Path(__file__).parent / "test_cases"
REPORTS_DIR = Path(__file__).parent / "reports"


class HibiscusEvaluator:
    """Runs HibiscusBench evaluation against Hibiscus API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: float = 90.0,
        max_concurrent: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run_suite(
        self,
        categories: Optional[list[str]] = None,
        dry_run: bool = False,
    ) -> dict:
        """
        Run the full HibiscusBench suite.

        Args:
            categories: Filter to specific categories (None = all)
            dry_run: If True, load test cases but don't call API

        Returns:
            Aggregated results dict
        """
        test_cases = self._load_all_test_cases(categories)
        logger.info(f"Running HibiscusBench: {len(test_cases)} test cases", dry_run=dry_run)

        if dry_run:
            return {"test_cases_loaded": len(test_cases), "dry_run": True}

        # Run all test cases with concurrency limit
        tasks = [self.run_test_case(tc) for tc in test_cases]
        results: list[EvalResult] = await asyncio.gather(*tasks)

        summary = aggregate_results(results)
        self._save_report(results, summary)

        logger.info(
            "HibiscusBench complete",
            dq_score=summary["dq_score"],
            passed=summary["passed"],
            total=summary["total"],
            meets_phase3=summary["meets_phase3_target"],
        )

        return summary

    async def run_category(self, category: str) -> dict:
        """Run test cases for a specific category."""
        return await self.run_suite(categories=[category])

    async def run_test_case(self, test_case: dict) -> EvalResult:
        """Run a single test case and return EvalResult."""
        async with self._semaphore:
            test_id = test_case.get("test_id", "unknown")
            logger.info(f"Running test case: {test_id}")

            start_ms = time.time() * 1000

            try:
                response_data = await self._call_hibiscus(test_case)
                latency_ms = time.time() * 1000 - start_ms

                response_text = response_data.get("response", "")
                confidence = response_data.get("confidence", 0.5)
                sources = response_data.get("sources", [])

                result = evaluate_response(
                    test_case=test_case,
                    response=response_text,
                    confidence=confidence,
                    sources=sources,
                    latency_ms=latency_ms,
                )

            except Exception as e:
                latency_ms = time.time() * 1000 - start_ms
                logger.error(f"Test case {test_id} failed with exception: {e}")
                result = EvalResult(
                    test_id=test_id,
                    test_name=test_case.get("name", "unknown"),
                    category=test_case.get("category", "unknown"),
                    passed=False,
                    dq_score=0.0,
                    accuracy_score=0.0,
                    grounding_score=0.0,
                    compliance_score=0.0,
                    safety_score=0.0,
                    helpfulness_score=0.0,
                    confidence_score=0.0,
                    failures=[f"API error: {str(e)}"],
                    critical_failure=f"API call failed: {str(e)}",
                    response_snippet="",
                    latency_ms=latency_ms,
                )

            status = "PASS" if result.passed else "FAIL"
            logger.info(
                f"[{status}] {test_id}: DQ={result.dq_score:.3f}",
                critical_failure=result.critical_failure,
            )

            return result

    async def _call_hibiscus(self, test_case: dict) -> dict:
        """Call the Hibiscus chat API for a test case."""
        input_data = test_case.get("input", {})
        payload = {
            "message": input_data.get("message", ""),
            "session_id": input_data.get("session_id", f"eval_{test_case.get('test_id', 'x')}"),
            "user_id": input_data.get("user_id", "eval_user"),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/hibiscus/chat",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    def _load_all_test_cases(self, categories: Optional[list[str]] = None) -> list[dict]:
        """Load all test case JSON files from test_cases directory."""
        test_cases = []

        if not TEST_CASES_DIR.exists():
            logger.warning("test_cases directory not found")
            return []

        for category_dir in TEST_CASES_DIR.iterdir():
            if not category_dir.is_dir():
                continue

            cat_name = category_dir.name
            if categories and cat_name not in categories:
                continue

            for json_file in category_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        tc = json.load(f)
                    tc["_file"] = str(json_file)
                    test_cases.append(tc)
                except Exception as e:
                    logger.error(f"Failed to load test case {json_file}: {e}")

        return sorted(test_cases, key=lambda x: x.get("test_id", ""))

    def _save_report(self, results: list[EvalResult], summary: dict) -> None:
        """Save evaluation report to JSON file."""
        import datetime
        REPORTS_DIR.mkdir(exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORTS_DIR / f"eval_{ts}.json"

        report = {
            "timestamp": ts,
            "summary": summary,
            "results": [
                {
                    "test_id": r.test_id,
                    "test_name": r.test_name,
                    "category": r.category,
                    "passed": r.passed,
                    "dq_score": r.dq_score,
                    "accuracy": r.accuracy_score,
                    "grounding": r.grounding_score,
                    "compliance": r.compliance_score,
                    "safety": r.safety_score,
                    "helpfulness": r.helpfulness_score,
                    "confidence": r.confidence_score,
                    "latency_ms": r.latency_ms,
                    "failures": r.failures,
                    "critical_failure": r.critical_failure,
                    "response_snippet": r.response_snippet,
                }
                for r in results
            ],
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved: {report_file}")
        print(f"\nReport: {report_file}")
        print(f"DQ Score: {summary['dq_score']:.3f} (target: 0.800)")
        print(f"Pass rate: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%})")
        if summary.get("critical_failures"):
            print(f"⚠️  Critical failures: {summary['critical_failures']}")
