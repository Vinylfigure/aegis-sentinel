"""The type checker (TYP01). An assurance program that cannot prove its
claims fails to compile instead of executing and lying — compile errors
are the product behaving like its name (PRD-v3 §3)."""

from aegis_sentinel.compile.checker import (
    CollectorPlan,
    CompileError,
    CompileReport,
    compile_claims,
)

__all__ = ["CollectorPlan", "CompileError", "CompileReport", "compile_claims"]
