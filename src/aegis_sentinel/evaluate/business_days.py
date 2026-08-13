"""Business-day math — Mon–Fri, no holiday calendar in V1 (D-P4).

docs/DECISIONS.md D-P4: business days are Monday–Friday; the manifest
carries an optional ``holiday_calendar`` field (empty in V1) so adding
one later is a manifest change, not a code change. The TA-2 TIMING
assertion ("revoked ≤ 5 business days") is evaluated with
:func:`business_days_between` once Okta events land (COL02/EVAL01).

STRICT purity lane (D-P3): pure functions of their date inputs.
"""

from __future__ import annotations

from datetime import date

MODULE_VERSION = "evaluate.business_days@0.1.0"


def is_business_day(day: date) -> bool:
    """True for Monday–Friday (D-P4: no holiday calendar in V1)."""
    return day.weekday() < 5


def _weekdays_through(day: date) -> int:
    """Mon–Fri days from the proleptic-Gregorian epoch through ``day``.

    Ordinal 1 (0001-01-01) is a Monday, so an ordinal ``o`` splits into
    ``o // 7`` full Mon–Sun weeks of 5 business days plus a remainder
    that starts on a Monday and contributes at most 5 more.
    """
    full_weeks, remainder = divmod(day.toordinal(), 7)
    return full_weeks * 5 + min(remainder, 5)


def business_days_between(start: date, end: date) -> int:
    """Business days elapsed from ``start`` to ``end``.

    Counts Mon–Fri days strictly after ``start`` through ``end``
    inclusive — the elapsed-deadline convention TA-2 needs: same-day is
    0, Friday→Monday is 1 (only the Monday counts), a Saturday→Sunday
    span is 0. ``end`` before ``start`` raises: the caller passed a
    reversed interval, and a silently negative count would let a
    reversed timestamp pair look timely.
    """
    if end < start:
        raise ValueError(f"end {end.isoformat()} precedes start {start.isoformat()}")
    return _weekdays_through(end) - _weekdays_through(start)
