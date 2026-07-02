"""Curated lesson scripts — oral teacher narration + visual kinds for the player."""
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
                    "Okay — so here's what usually trips people up. "
                    "A lot of us add the top numbers and the bottom numbers separately, right? "
                    "That shortcut only works when the pieces are the same size. "
                    "First, the denominators have to match."
                ),
                "visual_kind": "fraction_bars",
                "caption": "1/2 + 1/3 — pieces are different sizes",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Let me explain it like this. Picture a pizza cut into equal slices. "
                    "One half means two slices out of four. One third is a different cut — different sized pieces. "
                    "Before we add, we need equal slices. That's what finding a common denominator means."
                ),
                "visual_kind": "fraction_bars",
                "caption": "Make equal parts first",
            },
            {
                "title": "See it visually",
                "narration": (
                    "Now look at the bars with me. One half is the same as three sixths. "
                    "One third is two sixths. See — both bars now have six equal parts. "
                    "Add the shaded parts: three plus two gives five sixths."
                ),
                "visual_kind": "fraction_bars",
                "caption": "3/6 + 2/6 = 5/6",
            },
            {
                "title": "Worked example",
                "narration": (
                    "Let's walk through one half plus one third together. "
                    "The smallest denominator that works for both is six. "
                    "One half becomes three sixths. One third becomes two sixths. "
                    "Three sixths plus two sixths — that's five sixths."
                ),
                "visual_kind": "number_line",
                "caption": "LCM of 2 and 3 is 6",
            },
            {
                "title": "Try yourself",
                "narration": (
                    "Alright, your turn. Try one quarter plus one third. "
                    "A common denominator of twelve works nicely. "
                    "One quarter is three twelfths. One third is four twelfths. "
                    "So you get seven twelfths. Replay any step until it clicks."
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
                    "So — where do students usually slip? "
                    "Sometimes we move a number to the other side but flip the sign wrong. "
                    "Or we change only one side of the equation. "
                    "Remember: an equation is like a balanced scale."
                ),
                "visual_kind": "equation",
                "caption": "Both sides must stay equal",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Here's the rule I want you to feel, not just memorise. "
                    "Whatever you do to the left side, you must do to the right side. "
                    "To find x in two x plus four equals ten, subtract four from both sides first."
                ),
                "visual_kind": "equation",
                "caption": "2x + 4 = 10",
            },
            {
                "title": "See it visually",
                "narration": (
                    "Watch the balance. After subtracting four from both sides, two x equals six. "
                    "Now divide both sides by two. So x equals three. "
                    "Quick check: two times three plus four is ten. Perfect — it balances."
                ),
                "visual_kind": "equation",
                "caption": "x = 3",
            },
            {
                "title": "Practice",
                "narration": (
                    "Try this one: three x minus five equals seven. "
                    "Add five to both sides first, then divide by three. "
                    "Pause and replay if you want to hear those steps again."
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
                    "Let's clear up a common mix-up. "
                    "Plants don't eat soil like we eat food, and they don't breathe exactly like us either. "
                    "They actually make their own sugar — using sunlight, water, and carbon dioxide from the air."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Inputs vs outputs",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Inside the leaf, chlorophyll in the chloroplasts traps sunlight energy. "
                    "Water travels up from the roots. "
                    "Carbon dioxide slips in through tiny pores called stomata. "
                    "Those are the three ingredients the plant needs."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Sun + water + CO₂",
            },
            {
                "title": "See it visually",
                "narration": (
                    "Now follow the arrows on the diagram. "
                    "The plant builds glucose — that's its food — and releases oxygen as a by-product. "
                    "That oxygen is what we breathe. "
                    "So the energy flows from the sun into sugar inside the leaf."
                ),
                "visual_kind": "photosynthesis",
                "caption": "Glucose + O₂ out",
            },
            {
                "title": "Remember",
                "narration": (
                    "Say it like a short story: sunlight and water and air go in; food and oxygen come out. "
                    "Replay until you can sketch the diagram from memory."
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
                    "Here's a mistake I see a lot. "
                    "If two angles are fifty and sixty degrees, students sometimes guess the third is ninety. "
                    "Don't guess — the three interior angles of any triangle always add to one hundred eighty degrees."
                ),
                "visual_kind": "triangle",
                "caption": "50° + 60° + ? = 180°",
            },
            {
                "title": "Teacher explains",
                "narration": (
                    "Imagine tearing off the three corners and lining them up on a straight line. "
                    "They make a half turn — one hundred eighty degrees. "
                    "So the missing angle is one eighty minus fifty minus sixty, which is seventy degrees."
                ),
                "visual_kind": "triangle",
                "caption": "70°",
            },
            {
                "title": "Practice",
                "narration": (
                    "Your turn: if two angles are forty and eighty degrees, subtract both from one eighty. "
                    "You should get sixty. Replay if you want to hear that again."
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
            narration=(
                f"Okay — from your recent exam, here's what went wrong. {mistake} "
                "Don't worry, we'll fix it together."
            ),
            visual_kind="generic",
            caption=topic,
        ),
        TutorStepOut(
            id="2",
            title="Teacher explains",
            narration=(
                f"Let me explain {topic} the way your teacher would on the board. "
                "I'll go step by step — tell me to replay any part that feels fast."
            ),
            visual_kind="generic",
            caption="School-approved content",
        ),
        TutorStepOut(
            id="3",
            title="See it visually",
            narration=(
                "Now picture it on the board: labels, arrows, a simple diagram. "
                "Match the picture in your head to the words I'm saying. "
                "Pause and replay until they line up."
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
