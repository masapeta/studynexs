"""Topic normalization — free-text topics converge on a canonical aggregation key."""


def normalize_topic(raw: str) -> str:
    """Canonical key: collapse whitespace, casefold. ' Linear  Equations ' == 'linear equations'."""
    return " ".join(raw.split()).casefold()


def display_topic(raw: str) -> str:
    """Original casing with whitespace collapsed — what the UI shows."""
    return " ".join(raw.split())
