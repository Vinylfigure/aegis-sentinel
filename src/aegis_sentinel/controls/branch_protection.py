"""Branch-protection control check (SOC 2 CM-03 — Approval SOD).

Evaluates a *captured* GitHub branch-protection API response against the
config-level testing attributes of CM-03 (SOC2_Control_Testing_Matrix.md):
B (protection configured), C (approval required before merge), F (bypass /
admin exceptions considered), plus the collection spec's required status
checks. Attribute D (approver differs from requester) is PR-sample
evidence, not branch config, and is out of this function's scope.

Pure and deterministic: same capture in, same verdict out. The capture is
taken elsewhere; a capture the collector could not take (non-200, body
absent) is UNKNOWN(basis_missing), never a guess. A 200 capture with a
setting absent means the setting is off — that is a FAIL, not an UNKNOWN.
"""

from dataclasses import dataclass

CONTROL_ID = "CM-03"
TEST_FUNCTION_VERSION = "0.1.0"

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"

BASIS_MISSING = "basis_missing"


@dataclass(frozen=True)
class Verdict:
    status: str
    reasons: tuple[str, ...] = ()
    unknown_cause: str | None = None


def evaluate(
    capture: dict,
    *,
    required_checks: tuple[str, ...],
    min_approving_reviews: int = 1,
) -> Verdict:
    """Evaluate one captured branch-protection response.

    `capture` is the collector's saved envelope: `status_code` and, for a
    successful read, the API body under `protection`. `required_checks` and
    `min_approving_reviews` come from the frozen collection spec.
    """
    if capture.get("status_code") != 200 or not isinstance(capture.get("protection"), dict):
        return Verdict(
            status=UNKNOWN,
            reasons=("capture is not a successful read: no basis to evaluate",),
            unknown_cause=BASIS_MISSING,
        )

    protection = capture["protection"]
    reasons: list[str] = []

    reviews = protection.get("required_pull_request_reviews")
    if not isinstance(reviews, dict):
        reasons.append("required_pull_request_reviews is not configured")
    else:
        count = reviews.get("required_approving_review_count", 0)
        # bool is an int subclass: `true` from a malformed capture must not
        # satisfy a numeric threshold.
        if not isinstance(count, int) or isinstance(count, bool) or count < min_approving_reviews:
            reasons.append(
                f"required_approving_review_count is {count!r}, "
                f"spec requires >= {min_approving_reviews}"
            )

    checks = protection.get("required_status_checks")
    contexts = checks.get("contexts", []) if isinstance(checks, dict) else []
    for check in required_checks:
        if check not in contexts:
            reasons.append(f"required status check {check!r} is not enforced")

    enforce_admins = protection.get("enforce_admins")
    if not (isinstance(enforce_admins, dict) and enforce_admins.get("enabled") is True):
        reasons.append("enforce_admins is not enabled: admin bypass is possible")

    force_pushes = protection.get("allow_force_pushes")
    if isinstance(force_pushes, dict) and force_pushes.get("enabled") is True:
        reasons.append("allow_force_pushes is enabled")

    if reasons:
        return Verdict(status=FAIL, reasons=tuple(reasons))
    return Verdict(status=PASS)
