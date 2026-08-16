"""Typed assertion evaluators (EVAL01): pure functions from captured
evidence to verdict records — re-performable, clock-free, id-free (the
D-P3 determinism bans are AST-enforced on this package). The walking
skeleton ships the minimal EXISTENCE evaluator; the full typed evaluator
lands with EVAL01."""

from aegis_sentinel.evaluate.minimal import (
    RECORD_SCHEMA_VERSION,
    TEST_FUNCTION_VERSION,
    VOLATILE_FIELDS,
    canonical_record_hash,
    evaluate_existence,
)

__all__ = [
    "RECORD_SCHEMA_VERSION",
    "TEST_FUNCTION_VERSION",
    "VOLATILE_FIELDS",
    "canonical_record_hash",
    "evaluate_existence",
]
