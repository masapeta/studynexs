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

    def period_term(self, concept: str) -> str | None:
        """The school's word for an academic period concept ('term'/'academic_year')."""
        return self.period_terms.get(concept)


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
)
SCHOOL_C_PACK = SchoolPack(
    slug="school_c",
    class_incharge_term="Homeroom",
    class_label_format="{grade} / Div {section}",  # grade="Year 2", section="A" -> "Year 2 / Div A"
    period_terms={"term": "Annual", "academic_year": "Academic Year"},
    grading=GradingScale(bands=((80, "Distinction"), (60, "Merit"), (40, "Pass"), (0, "Fail"))),
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
