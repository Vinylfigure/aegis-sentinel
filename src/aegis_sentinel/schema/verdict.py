"""Verdict vocabulary and record — PRD-v3 §2, D-V1, D-U1, D-S1.

Five states, never interchangeable: PASS / FAIL / UNKNOWN / EXCLUDED /
EXCEPTION (D-V1: prior NOT_APPLICABLE became EXCLUDED, carrying its
ratification-reference requirement; EXCEPTION is new and requires a
disposition reference).

UNKNOWN decomposition: why-codes are the enum (PRD-v3 §2); the prior
scaffold's D-7 cause families ride along as ``d7_family`` per D-U1 —
see knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md
(basis_missing routes to permission review, identity_fuzzy to a human
resolution queue, no_basis_anywhere is a control-level finding, not
data cleanup). UNKNOWN never maps to satisfied.

Cross-field rules are constructor-enforced (salvaged pattern from the
prior scaffold's ``src/verdict.py`` ``__post_init__``): an invalid
verdict cannot even be constructed, let alone serialized.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from aegis_sentinel.schema.canonical import AegisModel, sha256_canonical

MODULE_VERSION = "schema.verdict@0.1.0"

SHA256_PATTERN = r"^[a-f0-9]{64}$"


class VerdictState(str, Enum):
    """PASS · FAIL · UNKNOWN · EXCLUDED · EXCEPTION — never interchangeable."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    EXCLUDED = "EXCLUDED"
    EXCEPTION = "EXCEPTION"


class UnknownWhyCode(str, Enum):
    """Why an UNKNOWN is unknown (PRD-v3 §2). Propagates; blocks ratification."""

    UNKNOWN_DISCOVERY = "UNKNOWN_DISCOVERY"
    UNKNOWN_OWNER = "UNKNOWN_OWNER"
    UNKNOWN_POPULATION = "UNKNOWN_POPULATION"
    UNKNOWN_EVIDENCE = "UNKNOWN_EVIDENCE"
    UNKNOWN_TESTABILITY = "UNKNOWN_TESTABILITY"


class D7Family(str, Enum):
    """Prior-scaffold D-7 cause families (ride along per D-U1)."""

    BASIS_MISSING = "basis_missing"
    IDENTITY_FUZZY = "identity_fuzzy"
    NO_BASIS_ANYWHERE = "no_basis_anywhere"


#: D-U1 mapping: each D-7 cause family names exactly one why-code.
#: Cited to knowledge/01_corpus/02_design_decisions/
#: Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md.
D7_FAMILY: dict[D7Family, UnknownWhyCode] = {
    D7Family.BASIS_MISSING: UnknownWhyCode.UNKNOWN_EVIDENCE,
    D7Family.IDENTITY_FUZZY: UnknownWhyCode.UNKNOWN_POPULATION,
    D7Family.NO_BASIS_ANYWHERE: UnknownWhyCode.UNKNOWN_TESTABILITY,
}


class VerdictRecord(AegisModel):
    """One verdict over one (claim, assertion, population) triple.

    References ``(manifest_version, snapshot_hash, contract_hash)`` per
    D-S1 — the run refuses to start if the loaded snapshot hash has no
    ratification row, one level up from the prior scaffold's
    ``(spec_id, spec_hash, ratification_ref)``.

    ``evaluated_at`` is an EXPLICIT input: the evaluator is pure and
    never reads a clock (D-P3).

    Constructor-enforced state rules:
    - UNKNOWN requires ``why_code``; ``d7_family`` (when present) must
      map to that why-code via ``D7_FAMILY``.
    - EXCLUDED requires ``ratification_ref`` (D-V1).
    - EXCEPTION requires ``disposition_ref`` (D-V1).
    - FAIL requires ``message`` (D-V1 carried requirement).
    - ``why_code``/``d7_family`` only on UNKNOWN; ``ratification_ref``
      only on EXCLUDED; ``disposition_ref`` only on EXCEPTION — so a
      PASS carries none of them.
    """

    claim_ref: str = Field(min_length=1)
    assertion_ref: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    manifest_version: str = Field(min_length=1)
    snapshot_hash: str = Field(pattern=SHA256_PATTERN)
    contract_hash: str = Field(pattern=SHA256_PATTERN)
    state: VerdictState
    evaluated_at: datetime
    message: str | None = None
    why_code: UnknownWhyCode | None = None
    d7_family: D7Family | None = None
    ratification_ref: str | None = None
    disposition_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    record_hash: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def _state_rules(self) -> "VerdictRecord":
        s = self.state
        if s is VerdictState.UNKNOWN:
            if self.why_code is None:
                raise ValueError("UNKNOWN requires a why_code")
        elif self.why_code is not None or self.d7_family is not None:
            raise ValueError(f"{s.value} may not carry why_code or d7_family")
        if self.d7_family is not None and D7_FAMILY[self.d7_family] is not self.why_code:
            raise ValueError(
                f"d7_family {self.d7_family.value} maps to "
                f"{D7_FAMILY[self.d7_family].value}, not {self.why_code}"
            )
        if s is VerdictState.EXCLUDED:
            if not self.ratification_ref:
                raise ValueError("EXCLUDED requires a ratification_ref")
        elif self.ratification_ref is not None:
            raise ValueError(f"{s.value} may not carry ratification_ref")
        if s is VerdictState.EXCEPTION:
            if not self.disposition_ref:
                raise ValueError("EXCEPTION requires a disposition_ref")
        elif self.disposition_ref is not None:
            raise ValueError(f"{s.value} may not carry disposition_ref")
        if s is VerdictState.FAIL and not self.message:
            raise ValueError("FAIL requires a message")
        return self

    def compute_record_hash(self) -> str:
        """Canonical hash with ``record_hash`` itself nulled (prior semantics)."""
        return sha256_canonical(self, ["record_hash"])

    def sealed(self) -> "VerdictRecord":
        """Return a copy with ``record_hash`` computed and set."""
        return self.model_copy(update={"record_hash": self.compute_record_hash()})
