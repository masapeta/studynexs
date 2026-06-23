"""Curated lesson scripts — teacher-style narration + visual kinds for the player."""
from __future__ import annotations

from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorStepOut

LESSON_TEMPLATES: dict[str, dict] = {
    "fractions": {
        "topic": "Fractions — adding with different denominators",
        "subject_name": "Mathematics",
        "visual_kind": "fraction_bars",
        "steps": [
            {
                "title": "What went wrong",
                "narration": (
                    "Many students add the top numbers and bottom numbers separately. "
                    "That only works when the pieces are the same size — the denominators must match first."
                ),
                "visual_kind": "fraction_bars",
                "caption": "1/2 + 1/3 — pieces are different sizes",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Think of a pizza cut into equal slices. One half means two out of four slices. "
                    "One third means a different cut. Before adding, we make equal slices — a common denominator."
                ),
                "visual_kind": "fraction_bars",
                "caption": "Make equal parts first",
            },
            {
                "title": "See it visually",
                "narration": (
                    "One half is the same as three sixths. One third is two sixths. "
                    "Now both bars have six equal parts. Add the shaded parts: three plus two is five sixths."
                ),
                "visual_kind": "fraction_bars",
                "caption": "3/6 + 2/6 = 5/6",
            },
            {
                "title": "Worked example",
                "narration": (
                    "For one half plus one third: the least common denominator is six. "
                    "One half becomes three sixths. One third becomes two sixths. "
                    "Three sixths plus two sixths equals five sixths."
                ),
                "visual_kind": "number_line",
                "caption": "LCM of 2 and 3 is 6",
            },
            {
                "title": "Try yourself",
                "narration": (
                    "Practice: one quarter plus one third. Find a common denominator of twelve. "
                    "One quarter is three twelfths. One third is four twelfths. The answer is seven twelfths. "
                    "Pause and replay any step until it feels clear."
                ),
                "visual_kind": "fraction_bars",
                "caption": "Your turn — replay if needed",
            },
        ],
    },
    "linear_equations": {
        "topic": "Linear equations — keeping balance",
        "subject_name": "Mathematics",
        "steps": [
            {
                "title": "What went wrong",
                "narration": (
                    "A common mistake is moving a number to the other side but changing the sign incorrectly, "
                    "or doing different operations on only one side. An equation is like a balanced scale."
                ),
                "visual_kind": "equation",
                "caption": "Both sides must stay equal",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Whatever you do to the left side, you must do to the right side. "
                    "To find x in two x plus four equals ten, subtract four from both sides first."
                ),
                "visual_kind": "equation",
                "caption": "2x + 4 = 10",
            },
            {
                "title": "See it visually",
                "narration": (
                    "After subtracting four from both sides, two x equals six. "
                    "Divide both sides by two. x equals three. Check: two times three plus four is ten. Correct."
                ),
                "visual_kind": "equation",
                "caption": "x = 3",
            },
            {
                "title": "Practice",
                "narration": (
                    "Try three x minus five equals seven. Add five to both sides, then divide by three. "
                    "Replay this step if you want to hear it again slowly."
                ),
                "visual_kind": "equation",
                "caption": "Balance every step",
            },
        ],
    },
    "photosynthesis": {
        "topic": "Photosynthesis — how plants make food",
        "subject_name": "Science",
        "steps": [
            {
                "title": "What went wrong",
                "narration": (
                    "Students sometimes say plants eat soil, or only breathe like us. "
                    "Plants make their own sugar using sunlight, water, and carbon dioxide from air."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Inputs vs outputs",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Inside the leaf, chlorophyll in chloroplasts traps sunlight energy. "
                    "Water travels up from roots. Carbon dioxide enters through tiny stomata pores."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Sun + water + CO₂",
            },
            {
                "title": "See it visually",
                "narration": (
                    "The plant builds glucose — food — and releases oxygen as a by-product. "
                    "That oxygen is what we breathe. The arrow of energy flows from sun to sugar."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Glucose + O₂ out",
            },
            {
                "title": "Remember",
                "narration": (
                    "Say it like a story: sunlight and water and air in; food and oxygen out. "
                    "Pause and replay until you can draw the diagram from memory."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Draw & label",
            },
        ],
    },
    "triangles": {
        "topic": "Triangles — angles sum to 180°",
        "subject_name": "Mathematics",
        "steps": [
            {
                "title": "What went wrong",
                "narration": (
                    "If two angles are fifty and sixty degrees, the third is not ninety by guesswork. "
                    "The three interior angles of any triangle always add to one hundred eighty degrees."
                ),
                "visual_kind": "triangle",
                "caption": "50° + 60° + ? = 180°",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Imagine tearing the three corners and placing them on a straight line. "
                    "They form a half turn — one hundred eighty degrees. So missing angle equals "
                    "one eighty minus fifty minus sixty, which is seventy degrees."
                ),
                "visual_kind": "triangle",
                "caption": "70°",
            },
            {
                "title": "Practice",
                "narration": (
                    "For forty and eighty degrees, subtract both from one eighty to get sixty. "
                    "Replay if you need to hear the steps again."
                ),
                "visual_kind": "triangle",
                "caption": "Always check the sum",
            },
        ],
    },
}


def match_lesson_key(topic: str) -> str:
    t = topic.lower()
    if "fraction" in t or "denominator" in t:
        return "fractions"
    if "linear" in t or "equation" in t or "algebra" in t:
        return "linear_equations"
    if "photo" in t or "chlorophyll" in t or "plant" in t:
        return "photosynthesis"
    if "triangle" in t or "angle" in t:
        return "triangles"
    return "generic"


def slugify_lesson_key(topic: str) -> str:
    key = match_lesson_key(topic)
    if key != "generic":
        return key
    return "topic-" + "".join(c if c.isalnum() else "-" for c in topic.lower()).strip("-")[:48]


def build_lesson_from_template(
    lesson_key: str,
    *,
    topic: str,
    subject_name: str,
    mastery_pct: float | None = None,
    trigger: str = "weak_topic",
    mistake_summary: str | None = None,
) -> TutorLessonOut:
    tpl = LESSON_TEMPLATES.get(lesson_key)
    if tpl:
        steps = [
            TutorStepOut(id=str(i + 1), **s)
            for i, s in enumerate(tpl["steps"])
        ]
        return TutorLessonOut(
            lesson_key=lesson_key,
            topic=tpl.get("topic", topic),
            subject_name=tpl.get("subject_name", subject_name),
            mastery_pct=mastery_pct,
            trigger=trigger,
            mistake_summary=mistake_summary,
            steps=steps,
        )

    mistake = mistake_summary or "Let's clear this concept step by step."
    steps = [
        TutorStepOut(
            id="1",
            title="What went wrong",
            narration=f"From your recent exam: {mistake}",
            visual_kind="generic",
            caption=topic,
        ),
        TutorStepOut(
            id="2",
            title="Teacher explains",
            narration=(
                f"Let's understand {topic} clearly. "
                "Your teacher approves every explanation from your school's syllabus — "
                "not random internet answers."
            ),
            visual_kind="generic",
            caption="School-approved content",
        ),
        TutorStepOut(
            id="3",
            title="See it visually",
            narration=(
                "Picture the idea on the board: labels, arrows, and a simple diagram. "
                "Use pause and replay until the picture matches the words in your head."
            ),
            visual_kind="generic",
            caption="Draw along mentally",
        ),
        TutorStepOut(
            id="4",
            title="Practice",
            narration=(
                "Try one similar question from your workbook. "
                "If it still feels hard, replay this lesson — good learners repeat until it clicks."
            ),
            visual_kind="generic",
            caption="Retry builds memory",
        ),
    ]
    return TutorLessonOut(
        lesson_key=lesson_key,
        topic=topic,
        subject_name=subject_name,
        mastery_pct=mastery_pct,
        trigger=trigger,
        mistake_summary=mistake_summary,
        steps=steps,
    )
