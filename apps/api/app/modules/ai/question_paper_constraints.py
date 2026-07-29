"""Provider-independent limits for exact question-paper generation."""

QUESTION_OUTPUT_TOKEN_BUDGET = 6_000

# Conservative output estimates include question text, answer key, options, and JSON overhead.
# The generation call currently permits 8,000 output tokens; reserving roughly 2,000 tokens for
# section wrappers and model variance makes valid Studio plans substantially less likely to be
# truncated mid-JSON.
QUESTION_OUTPUT_TOKEN_WEIGHTS: dict[str, int] = {
    "mcq": 90,
    "fill_blank": 60,
    "match": 120,
    "true_false": 60,
    "very_short": 70,
    "short": 120,
    "long": 220,
    "very_long": 320,
}


def estimated_question_output_tokens(question_type_counts: list[tuple[str, int]]) -> int:
    """Return a deterministic conservative output estimate for a section plan."""
    return sum(
        QUESTION_OUTPUT_TOKEN_WEIGHTS[question_type] * question_count
        for question_type, question_count in question_type_counts
    )
