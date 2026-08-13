"""The Aegis type checker (TYP01) — E-codes + collector-plan compilation.

PRD-v3 §3: for every (claim, assertion, population) triple the compiler
matches required evidence properties against the usable capability
registry and either compiles a collector plan or refuses with an error
a human can act on (E204 temporal insufficiency, E117 missing
capability, E302 schema-version drift). Compile errors are the product
behaving like its name.

STRICT purity lane (D-P3): no LLM, no network, no clock reads, no
randomness, no environment access. Registered file-by-file in
tests/test_verdict_path_purity.py.
"""

from aegis_sentinel.compile.errors import (
    CompileError,
    E117MissingCapability,
    E204TemporalInsufficiency,
    E302SchemaVersionDrift,
)
from aegis_sentinel.compile.typecheck import (
    ClaimCompilation,
    CompiledCollectorPlan,
    CompileResult,
    compile_program,
    executable_collectors,
    period_days,
)

__all__ = [
    # errors
    "CompileError",
    "E117MissingCapability",
    "E204TemporalInsufficiency",
    "E302SchemaVersionDrift",
    # typecheck
    "CompiledCollectorPlan",
    "ClaimCompilation",
    "CompileResult",
    "compile_program",
    "executable_collectors",
    "period_days",
]
