"""Evaluate — the pure typed-assertion evaluator (EVAL01 lane).

STRICT purity lane (D-P3): no LLM, no network, no clock reads, no
randomness, no environment access — ``evaluated_at`` is always an
explicit parameter. Enforced by tests/test_verdict_path_purity.py and
scripts/check-purity.sh.
"""

from aegis_sentinel.evaluate.business_days import (
    business_days_between,
    is_business_day,
)
from aegis_sentinel.evaluate.minimal import evaluate_feed_claim

__all__ = [
    "is_business_day",
    "business_days_between",
    "evaluate_feed_claim",
]
