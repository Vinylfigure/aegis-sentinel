"""Exhaustive unit tests for business-day math (D-P4: Mon–Fri, no holidays).

2026-01-02 is a Friday; 2026-01-05 a Monday — the week anchors below.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from aegis_sentinel.evaluate import business_days_between, is_business_day

FRI = date(2026, 1, 2)
SAT = date(2026, 1, 3)
SUN = date(2026, 1, 4)
MON = date(2026, 1, 5)


def test_is_business_day_over_a_full_week() -> None:
    week = [MON + timedelta(days=i) for i in range(7)]
    assert [is_business_day(d) for d in week] == [True] * 5 + [False, False]


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (MON, MON, 0),  # same-day: zero elapsed
        (FRI, FRI, 0),
        (SAT, SAT, 0),
        (FRI, MON, 1),  # the canonical Fri→Mon case: only Monday counts
        (FRI, SAT, 0),  # weekend endpoints contribute nothing
        (FRI, SUN, 0),
        (SAT, SUN, 0),
        (SAT, MON, 1),
        (SUN, MON, 1),
        (MON, date(2026, 1, 9), 4),  # Mon→Fri same week
        (FRI, date(2026, 1, 9), 5),  # Fri→Fri: one full business week
        (MON, date(2026, 1, 12), 5),  # Mon→Mon across a weekend
        (SUN, date(2026, 1, 10), 5),  # Sun→Sat: the enclosed business week
        (MON, date(2026, 2, 2), 20),  # four full weeks
    ],
)
def test_business_days_between(start: date, end: date, expected: int) -> None:
    assert business_days_between(start, end) == expected


def test_reversed_interval_raises() -> None:
    with pytest.raises(ValueError, match="precedes"):
        business_days_between(MON, FRI)


def test_matches_naive_count_for_every_pair_in_a_six_week_window() -> None:
    """The O(1) arithmetic must equal the day-by-day count, every pair."""
    days = [date(2026, 1, 1) + timedelta(days=i) for i in range(42)]
    for i, start in enumerate(days):
        for end in days[i:]:
            naive = sum(
                1
                for offset in range(1, (end - start).days + 1)
                if is_business_day(start + timedelta(days=offset))
            )
            assert business_days_between(start, end) == naive, (start, end)
