"""SchoolPack — school-specific SEMANTIC configuration (P1.6).

The universal runtime (planner, derivation, conversation, capability contracts, relationship
registry) is school-agnostic. Everything that legitimately varies by school lives here as
CONFIGURATION, not code:

  - terminology (what a class-incharge is called; the "teachers" column heading)
  - academic structure (how a class label is composed/displayed from grade + section)
  - grading (percentage boundaries -> letter)
  - role interpretation (which roles are staff / admin)
  - period terminology (term / semester labels)

Strict architectural rule (from the P1.6 brief):
  A SchoolPack MAY configure semantics. It MUST NOT become a second authorization engine, a
  second data adapter, or a bag of arbitrary Python callbacks. So a pack is *plain data* plus
  a couple of *pure, deterministic* formatting/label functions — no DB access, no permission
  decisions, no side effects.

The default StudyNexsPack reproduces the current reference-school behaviour EXACTLY (labels
byte-for-byte), so introducing the pack changes no output. School A/B/C variants exist only to
prove the runtime is driven by configuration, not by the reference school's assumptions.
"""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GradingScale:
    """Percentage -> letter bands, highest-first. Pure data; no pass/fail is implied."""

    # (min_percent_inclusive, letter), evaluated highest band first.
    bands: tuple[tuple[float, str], ...] = (
        (90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (0, "F"),
    )

    def letter_for(self, percent: float | None) -> str | None:
        if percent is None:
            return None
        for threshold, letter in self.bands:
            if percent >= threshold:
                return letter
        return None


@dataclass(frozen=True)
class AttendancePolicy:
    """How a school turns raw attendance rows into a percentage — a BUSINESS RULE the school
    configures, not something the universal engine decides (spec §4, §5, §21).

    Two knobs, both per attendance status:
      credit    — how much each status counts toward "attended" (present=1.0, half_day=0.5, …).
      denominator — which statuses count in the denominator (a status absent from this set is
                    EXCLUDED, e.g. a school that drops excused-style statuses from the base).

    The arithmetic stays authoritative and deterministic here; the engine only asks the policy
    to score already-fetched counts. Defaults reproduce the reference convention exactly
    (present/late/half_day credited @1.0, everything counted) so behaviour is unchanged.
    """

    credit: dict[str, float] = field(default_factory=lambda: {
        "present": 1.0, "late": 1.0, "half_day": 1.0, "absent": 0.0,
    })
    # Statuses that count toward the denominator. None = "count every recorded status".
    denominator: frozenset[str] | None = None

    def percentage(self, counts: dict[str, int]) -> float | None:
        """Score a {status: count} map into a percentage, or None when the base is empty.

        Deterministic and pure: the engine fetches counts, the policy scores them. An unknown
        status contributes 0 credit and (if no explicit denominator set) still counts in the base.
        """
        base = 0
        credited = 0.0
        for status, n in counts.items():
            if self.denominator is not None and status not in self.denominator:
                continue
            base += n
            credited += self.credit.get(status, 0.0) * n
        if base <= 0:
            return None
        return round(credited / base * 100, 1)


@dataclass(frozen=True)
class SchoolPack:
    """School-specific semantic configuration (plain data + pure label helpers)."""

    slug: str = "studynexs"
    # Terminology: canonical concept -> the school's display term.
    class_incharge_term: str = "Class Teacher"       # form tutor / homeroom / etc.
    teachers_column_label: str = "Teachers"
    period_terms: dict[str, str] = field(default_factory=lambda: {
        "term": "Term", "academic_year": "Academic Year",
    })
    # Academic structure: how a class LABEL is composed from grade + section. "{grade} {section}"
    # reproduces the reference school ("Class 10" + "A" -> "Class 10 A"); School B could use
    # "{grade} · {section}" or swap in "Division".
    class_label_format: str = "{grade} {section}"
    # Grading rule. None means the school has NOT configured a letter-grade model, so the
    # runtime must report an honest limitation rather than invent one (spec §14, §19).
    grading: GradingScale | None = field(default_factory=GradingScale)
    # Attendance calculation policy (a business rule the school configures — §4/§5). Default
    # reproduces the reference convention (present/late/half_day credited @1.0, all counted).
    attendance: AttendancePolicy = field(default_factory=AttendancePolicy)
    # Role interpretation (which role strings count as staff / admin for display purposes; the
    # AUTHORITATIVE authorization enforcement stays server-side in P1.1 — the pack never decides
    # access, it only labels).
    admin_roles: frozenset[str] = frozenset({"admin", "super_admin"})

    # ── Pure label helpers (deterministic, no I/O) ──────────────────────────────

    def class_label(self, grade: str, section: str) -> str:
        return self.class_label_format.format(
            grade=(grade or "").strip(), section=(section or "").strip()
        ).strip()

    @property
    def supports_grading(self) -> bool:
        """Whether this school configured a letter-grade model (else: honest limitation)."""
        return self.grading is not None

    def grade_letter(self, percent: float | None) -> str | None:
        if self.grading is None:
            return None
        return self.grading.letter_for(percent)

    def attendance_percentage(self, counts: dict[str, int]) -> float | None:
        """Score raw {status: count} into a percentage under this school's policy (§4)."""
        return self.attendance.percentage(counts)

    def period_term(self, concept: str) -> str | None:
        """The school's word for an academic period concept ('term'/'academic_year')."""
        return self.period_terms.get(concept)

    def period_concept(self, word: str) -> str | None:
        """Reverse: the universal concept THIS school means by a period word, or None.

        Semantic equivalence is never invented (spec §12): "Semester" maps to the 'term'
        concept only for a school that configured that word. A word this school didn't
        configure returns None, so the runtime clarifies rather than guessing an alias.
        """
        target = (word or "").strip().casefold()
        if not target:
            return None
        for concept, label in self.period_terms.items():
            if label.casefold() == target:
                return concept
        return None


# The production default: current reference-school behaviour, unchanged.
_STUDYNEXS_PACK = SchoolPack()

# Conceptual test packs (P1.4 §19) — proof that differences are configuration, not code. NOT
# wired to any production tenant; used only by the 3-school configuration test.
SCHOOL_A_PACK = SchoolPack(slug="school_a")  # identical to StudyNexs default (proves parity)
SCHOOL_B_PACK = SchoolPack(
    slug="school_b",
    class_incharge_term="Form Tutor",
    class_label_format="{grade} {section}",  # grade="Grade 2", section="Blue" -> "Grade 2 Blue"
    period_terms={"term": "Semester", "academic_year": "Academic Year"},
    grading=GradingScale(bands=((70, "A"), (55, "B"), (40, "C"), (0, "D"))),
    # Business rule: a late arrival is only a partial attend, and half_day counts fully.
    attendance=AttendancePolicy(
        credit={"present": 1.0, "late": 0.5, "half_day": 1.0, "absent": 0.0},
    ),
)
SCHOOL_C_PACK = SchoolPack(
    slug="school_c",
    class_incharge_term="Homeroom",
    class_label_format="{grade} / Div {section}",  # grade="Year 2", section="A" -> "Year 2 / Div A"
    period_terms={"term": "Annual", "academic_year": "Academic Year"},
    grading=GradingScale(bands=((80, "Distinction"), (60, "Merit"), (40, "Pass"), (0, "Fail"))),
    # Business rule: half_day is EXCLUDED from the denominator entirely (not counted either way).
    attendance=AttendancePolicy(
        credit={"present": 1.0, "late": 1.0, "half_day": 0.0, "absent": 0.0},
        denominator=frozenset({"present", "late", "absent"}),
    ),
)

# A deliberately INCOMPLETE pack (spec §19): no grading configured. The runtime must return an
# honest limitation for grade questions and never borrow another school's grading model.
SCHOOL_MINIMAL_PACK = SchoolPack(slug="school_minimal", grading=None)

_PACKS = {
    p.slug: p
    for p in (
        _STUDYNEXS_PACK,
        SCHOOL_A_PACK,
        SCHOOL_B_PACK,
        SCHOOL_C_PACK,
        SCHOOL_MINIMAL_PACK,
    )
}

# Tenant slug -> pack slug. Empty means every real tenant uses the default pack (a single
# production SchoolPack over the current PostgreSQL/services). This is the onboarding seam a
# future flow would populate to assign a pack per school; the cross-school benchmark registers
# conceptual mappings here. It carries NO authorization or data-access meaning.
_TENANT_PACKS: dict[str, str] = {}

# The pack active for the CURRENT turn, bound from the authenticated tenant by the service
# (spec §23 blind execution). Every no-arg get_school_pack() reads this, so the universal
# runtime obtains school semantics without any call-site plumbing or engine change. Defaults
# to StudyNexs, so behaviour is byte-identical for real tenants.
_active_pack: contextvars.ContextVar[SchoolPack] = contextvars.ContextVar(
    "active_school_pack", default=_STUDYNEXS_PACK
)


def register_tenant_pack(tenant_slug: str, pack_slug: str) -> None:
    """Map a tenant to a SchoolPack (onboarding seam; also used by the benchmark/tests)."""
    _TENANT_PACKS[tenant_slug] = pack_slug


def pack_for_tenant(tenant_slug: str | None) -> SchoolPack:
    """Resolve the SchoolPack for a tenant. Unmapped/unknown tenants use the default pack."""
    if not tenant_slug:
        return _STUDYNEXS_PACK
    return _PACKS.get(_TENANT_PACKS.get(tenant_slug, ""), _STUDYNEXS_PACK)


@contextmanager
def use_school_pack(pack: SchoolPack) -> Iterator[None]:
    """Bind the active SchoolPack for the current turn (blind: driven by the tenant)."""
    token = _active_pack.set(pack)
    try:
        yield
    finally:
        _active_pack.reset(token)


def get_school_pack(slug: str | None = None) -> SchoolPack:
    """Return a SchoolPack. With an explicit slug, look it up; otherwise return the pack
    bound for the current turn (default StudyNexs when none is bound)."""
    if slug:
        return _PACKS.get(slug, _STUDYNEXS_PACK)
    return _active_pack.get()
