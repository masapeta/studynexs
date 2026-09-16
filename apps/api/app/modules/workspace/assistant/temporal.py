"""Temporal semantics — turn a canonical time token into a concrete date range.

The LLM planner maps varied phrasings ("today", "this month's collection",
"between Aug 1 and Aug 31") onto a small set of *canonical tokens* or an explicit
{from,to}. This module deterministically converts that into a range, using the
school's timezone (not the server's) and the school's AcademicYear boundaries.

A range is half-open [start, end): start inclusive, end exclusive. Both a datetime
form (for tz-aware timestamp columns like FeeReceipt.paid_at) and a date form (for
Date columns like Attendance.date) are provided so callers filter correctly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear
from app.db.models.school import School
from app.modules.ai.services.ai_credits import school_timezone

# Canonical relative tokens the planner may emit.
RELATIVE_TOKENS = frozenset(
    {
        "today",
        "yesterday",
        "this_week",
        "last_week",
        "this_month",
        "last_month",
        "this_year",
        "last_year",
        "current_academic_year",
        "previous_academic_year",
        "all_time",
    }
)


@dataclass(frozen=True)
class DateRange:
    """Half-open [start, end). ``label`` is a human phrase for titles.

    Two representations, both half-open:
    - start/end: UTC datetimes for tz-aware timestamp columns (e.g. FeeReceipt.paid_at).
    - start_date/end_date: LOCAL calendar dates for Date columns (e.g. Attendance.date).
      These come from the school-timezone calendar, NOT from .date() of the UTC datetime
      (which would shift a day for +05:30).
    """

    start: datetime | None  # UTC, inclusive; None for all_time
    end: datetime | None  # UTC, exclusive; None for all_time
    label: str
    start_date: date | None = None  # local, inclusive
    end_date: date | None = None  # local, exclusive
    # Temporal intent relative to "today" (school tz): a range wholly in the past is PAST,
    # one containing today is CURRENT, wholly future is FUTURE, all_time is UNSPECIFIED.
    # Used by the historical-honesty guard — NOT keyword-based.
    temporality: str = "UNSPECIFIED"

    @property
    def is_all_time(self) -> bool:
        return self.start is None and self.end is None

    @property
    def is_past(self) -> bool:
        return self.temporality == "PAST"


# ── Semantic-integrity primitives (P0.1) ──────────────────────────────────────
# Temporal meaning must survive from the user's words to execution. These pure
# functions operate on STRUCTURED temporality (never keywords) so the planner
# cannot silently downgrade a historical request into a current-state one.

# Decisions from the integrity check.
INTEGRITY_ALLOW = "ALLOW"
INTEGRITY_BLOCK_UNSUPPORTED = "BLOCK_UNSUPPORTED"  # capability has no history for a PAST ask
INTEGRITY_DROPPED = "TEMPORAL_CONSTRAINT_DROPPED"  # plan lost the user's historical qualifier

# Presence values the planner may declare (semantic layer).
_PAST_PRESENCE = frozenset({"PAST"})
_PERIODIC_PRESENCE = frozenset({"PERIOD", "DATE_SPECIFIC"})


def semantic_temporality(presence: str, semantic_range: "DateRange | None") -> str:
    """Collapse the planner's declared presence + resolved window into one temporality.

    An explicit/carried PAST intent is STICKY and dominates the calendar (spec P1.2 §5/§11,
    P0.1): "who was the teacher in August?" followed by "what about September?" stays PAST
    even though September contains today — a historical follow-up must never silently become
    current. Only when presence does not assert history do the resolved dates decide (so a
    mislabelled CURRENT/FUTURE window is still corrected by real dates).
    """
    p = (presence or "NONE").strip().upper()
    if p == "PAST":
        return "PAST"  # historical intent dominates calendar position
    if semantic_range is not None and not semantic_range.is_all_time:
        return semantic_range.temporality  # PAST / CURRENT / FUTURE from real dates
    if p in _PERIODIC_PRESENCE:
        return "PAST"
    if p in ("CURRENT", "FUTURE"):
        return p
    return "NONE"


def temporal_integrity(
    *,
    semantic: str,
    plan: str,
    supports_historical: bool,
    semantic_concrete: bool = False,
    plan_has_window: bool = False,
) -> str:
    """Compare the user's semantic temporality against the plan's resolved temporality.

    ``semantic_concrete`` = the user's request resolved to a CONCRETE bounded window (a real
    date/month/range), as opposed to a weak/ongoing PAST (e.g. present-perfect "has been
    coming", which is effectively all-time). ``plan_has_window`` = the plan actually applied a
    concrete time window to its params. We check *window applied*, not the window's calendar
    position, because a past-framed window can legitimately resolve to the current month
    (e.g. "September" collection-to-date). Rules:

    - current-state capability + any PAST → BLOCK_UNSUPPORTED (relationship history is not
      kept; refuse rather than answer with the present).
    - event-time capability + PAST + a window was applied → ALLOW.
    - event-time capability + PAST + concrete window intended but NOT applied → the window
      was dropped between understanding and execution → TEMPORAL_CONSTRAINT_DROPPED.
    - event-time capability + PAST + no concrete window intended → ALLOW (all-time/ongoing).
    - semantic not PAST → honour the plan's own temporality for the capability guard.
    """
    sem = (semantic or "NONE").strip().upper()
    pln = (plan or "NONE").strip().upper()
    if sem == "PAST":
        if not supports_historical:
            return INTEGRITY_BLOCK_UNSUPPORTED
        if plan_has_window or pln == "PAST":
            return INTEGRITY_ALLOW
        return INTEGRITY_DROPPED if semantic_concrete else INTEGRITY_ALLOW
    if pln == "PAST" and not supports_historical:
        return INTEGRITY_BLOCK_UNSUPPORTED
    return INTEGRITY_ALLOW


def _to_utc(local_dt: datetime) -> datetime:
    return local_dt.astimezone(timezone.utc)


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _month_number(value: str | None) -> int | None:
    return _MONTHS.get((value or "").strip().lower())


async def _academic_year(
    db: AsyncSession, school_id: uuid.UUID, *, previous: bool
) -> tuple[date, date] | None:
    """Active (or the one before it) academic-year boundaries for the school."""
    rows = (
        await db.execute(
            select(AcademicYear.start_date, AcademicYear.end_date, AcademicYear.is_active)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date.desc())
        )
    ).all()
    if not rows:
        return None
    ordered = [(s, e) for s, e, _ in rows]
    if not previous:
        for s, e, is_active in rows:
            if is_active:
                return (s, e)
        return ordered[0]  # newest as a sane default
    # previous = the one starting before the active year's start.
    active = next(((s, e) for s, e, is_active in rows if is_active), ordered[0])
    for s, e in ordered:
        if s < active[0]:
            return (s, e)
    return None


async def resolve_time_range(
    db: AsyncSession,
    school: School | None,
    school_id: uuid.UUID,
    time: str | dict | None,
) -> DateRange:
    """Resolve a canonical token or {from,to} dict into a concrete DateRange.

    Unknown/missing input → all_time (safe, unfiltered) so callers never crash.
    """
    tz = school_timezone(school)
    now_local = datetime.now(tz)
    today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    today_d = today_local.date()

    def _temporality(start_d: date, end_d: date) -> str:
        # end_d is exclusive. Wholly before today -> PAST; contains today -> CURRENT;
        # wholly after -> FUTURE.
        if end_d <= today_d:
            return "PAST"
        if start_d > today_d:
            return "FUTURE"
        return "CURRENT"

    def local_range(start_d: date, end_d: date, label: str) -> DateRange:
        """Build a range from local calendar dates [start_d, end_d) (end exclusive)."""
        start_local = datetime.combine(start_d, datetime.min.time(), tzinfo=tz)
        end_local = datetime.combine(end_d, datetime.min.time(), tzinfo=tz)
        return DateRange(
            _to_utc(start_local), _to_utc(end_local), label,
            start_date=start_d, end_date=end_d, temporality=_temporality(start_d, end_d),
        )

    # Named month without a year: {"month": "august"} → deterministic year (no LLM guess).
    # Choose the most recent occurrence on/before today's month in the school calendar.
    if isinstance(time, dict) and time.get("month") and not time.get("from"):
        m = _month_number(str(time.get("month")))
        if m:
            year = today_d.year if m <= today_d.month else today_d.year - 1
            if time.get("year"):
                try:
                    year = int(time["year"])
                except (TypeError, ValueError):
                    pass
            start = date(year, m, 1)
            end = date(year + 1, 1, 1) if m == 12 else date(year, m + 1, 1)
            month_label = date(year, m, 1).strftime("%B %Y")
            return local_range(start, end, month_label)

    # Explicit range: {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"} (inclusive to).
    if isinstance(time, dict):
        frm = _parse_iso_date(str(time.get("from") or ""))
        to = _parse_iso_date(str(time.get("to") or ""))
        if frm or to:
            start_local = datetime.combine(frm, datetime.min.time(), tzinfo=tz) if frm else None
            end_excl = to + timedelta(days=1) if to else None  # inclusive 'to' → exclusive end
            end_local = (
                datetime.combine(end_excl, datetime.min.time(), tzinfo=tz) if end_excl else None
            )
            label = f"{frm.isoformat() if frm else '…'} to {to.isoformat() if to else '…'}"
            temporality = "UNSPECIFIED"
            if frm and end_excl:
                temporality = _temporality(frm, end_excl)
            elif end_excl and end_excl <= today_d:
                temporality = "PAST"
            elif frm and frm > today_d:
                temporality = "FUTURE"
            return DateRange(
                _to_utc(start_local) if start_local else None,
                _to_utc(end_local) if end_local else None,
                label,
                start_date=frm,
                end_date=end_excl,
                temporality=temporality,
            )

    token = (time or "").strip().lower() if isinstance(time, str) else ""

    if token in ("", "all_time"):
        return DateRange(None, None, "all time")
    if token == "today":
        return local_range(today_d, today_d + timedelta(days=1), "today")
    if token == "yesterday":
        return local_range(today_d - timedelta(days=1), today_d, "yesterday")
    if token == "this_week":
        start = today_d - timedelta(days=today_d.weekday())  # Monday
        return local_range(start, start + timedelta(days=7), "this week")
    if token == "last_week":
        start = today_d - timedelta(days=today_d.weekday() + 7)
        return local_range(start, start + timedelta(days=7), "last week")
    if token == "this_month":
        start = today_d.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        return local_range(start, end, "this month")
    if token == "last_month":
        first_this = today_d.replace(day=1)
        start = (first_this - timedelta(days=1)).replace(day=1)
        return local_range(start, first_this, "last month")
    if token == "this_year":
        start = today_d.replace(month=1, day=1)
        return local_range(start, start.replace(year=start.year + 1), "this year")
    if token == "last_year":
        start = today_d.replace(year=today_d.year - 1, month=1, day=1)
        return local_range(start, start.replace(year=start.year + 1), "last year")
    if token in ("current_academic_year", "previous_academic_year"):
        ay = await _academic_year(
            db, school_id, previous=(token == "previous_academic_year")
        )
        if ay:
            s, e = ay
            label = (
                "current academic year"
                if token == "current_academic_year"
                else "previous academic year"
            )
            # AcademicYear.end_date is inclusive → exclusive end is next day.
            return local_range(s, e + timedelta(days=1), label)
        return DateRange(None, None, "all time")

    # Unknown token → all_time (never guess a range).
    return DateRange(None, None, "all time")
