"""
HibiscusBench — Main Entry Point
==================================
Run with: python -m hibiscus.evaluation.bench [options]

Options:
    --category health|life|motor|travel|adversarial|cross
    --url http://localhost:8001
    --dry-run  (load test cases, don't call API)
    --ci       (exit 1 if DQ < 0.80)
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import argparse
import asyncio
import sys
from .evaluator import HibiscusEvaluator


async def run(args: argparse.Namespace) -> int:
    evaluator = HibiscusEvaluator(
        base_url=args.url,
        max_concurrent=args.concurrency,
    )

    categories = [args.category] if args.category else None
    results = await evaluator.run_suite(categories=categories, dry_run=args.dry_run)

    if args.dry_run:
        print(f"Dry run: {results['test_cases_loaded']} test cases found")
        return 0

    dq = results.get("dq_score", 0.0)
    meets_target = results.get("meets_phase3_target", False)

    if args.ci and not meets_target:
        print(f"\n❌ CI check failed: DQ={dq:.3f} < 0.800 required")
        return 1

    if meets_target:
        print(f"\n✅ Phase 3 DQ target met: {dq:.3f} >= 0.800")
    else:
        print(f"\n⚠️  DQ below target: {dq:.3f} < 0.800")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="HibiscusBench Evaluation Runner")
    parser.add_argument("--category", default=None,
                        choices=["health", "life", "motor", "travel", "adversarial", "cross"],
                        help="Run only this category")
    parser.add_argument("--url", default="http://localhost:8001",
                        help="Hibiscus API base URL")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Max concurrent API calls")
    parser.add_argument("--dry-run", action="store_true",
                        help="Load test cases without calling API")
    parser.add_argument("--ci", action="store_true",
                        help="Exit with error code if DQ < 0.80")

    args = parser.parse_args()
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
