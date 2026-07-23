"""Build tutor lesson steps from an approved ConceptCard."""
from __future__ import annotations

from app.db.models.concept_card import ConceptCard
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorStepOut


def build_lesson_from_concept_card(
    *,
    card: ConceptCard,
    concept: CurriculumConcept,
    subject_name: str = "Curriculum",
    mastery_pct: float | None = None,
    trigger: str = "concept_card",
    mistake_summary: str | None = None,
) -> TutorLessonOut:
    steps: list[TutorStepOut] = [
        TutorStepOut(
            id="explain",
            title="Teacher explains",
            narration=card.explanation,
            visual_kind=card.visual_kind or "generic",
            caption=concept.title,
        )
    ]

    examples = card.examples or []
    for idx, example in enumerate(examples[:3], start=1):
        steps.append(
            TutorStepOut(
                id=f"example-{idx}",
                title=f"Example {idx}",
                narration=str(example),
                visual_kind=card.visual_kind or "generic",
            )
        )

    hints = card.hints or []
    if hints:
        steps.append(
            TutorStepOut(
                id="hints",
                title="Hints",
                narration=" ".join(str(h) for h in hints[:3]),
                visual_kind="generic",
            )
        )

    steps.append(
        TutorStepOut(
            id="practice",
            title="Try yourself",
            narration=(
                f"Practice {concept.title} on your own. "
                "Replay any step until it clicks."
            ),
            visual_kind=card.visual_kind or "generic",
        )
    )

    return TutorLessonOut(
        lesson_key=concept.slug,
        topic=concept.title,
        subject_name=subject_name,
        mastery_pct=mastery_pct,
        trigger=trigger,
        mistake_summary=mistake_summary,
        pack_id=concept.pack_id,
        concept_id=concept.id,
        concept_slug=concept.slug,
        steps=steps,
    )
