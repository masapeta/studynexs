from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
    ConfidenceProvider,
    LanguageProvider,
    MathProvider,
    ScientificProvider,
    TextProvider,
    VisualProvider,
    default_providers,
)


class _CustomProvider:
    name = "custom"

    def __init__(self) -> None:
        self.calls = 0

    def supports(self, answer: AcademicAnswer) -> bool:
        return answer.subject == "custom"

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        self.calls += 1
        metadata = dict(answer.metadata)
        metadata["custom"] = True
        return answer.model_copy(update={"metadata": metadata})


def test_default_provider_order_is_stable():
    providers = default_providers()

    assert [provider.name for provider in providers] == [
        "text",
        "language",
        "math",
        "scientific",
        "visual",
        "confidence",
    ]
    assert isinstance(providers[0], TextProvider)
    assert isinstance(providers[1], LanguageProvider)
    assert isinstance(providers[2], MathProvider)
    assert isinstance(providers[3], ScientificProvider)
    assert isinstance(providers[4], VisualProvider)
    assert isinstance(providers[5], ConfidenceProvider)


def test_engine_runs_supported_custom_provider_only():
    provider = _CustomProvider()
    engine = AcademicUnderstandingEngine(providers=[provider])

    unsupported = engine.understand(AcademicAnswer(raw_input="answer", subject="math"))
    supported = engine.understand(AcademicAnswer(raw_input="answer", subject="custom"))

    assert provider.calls == 1
    assert "custom" not in unsupported.metadata
    assert supported.metadata["custom"] is True
    assert unsupported.metadata["provider_trace"] == [
        {"provider": "custom", "status": "skipped", "supported": False}
    ]
    assert supported.metadata["provider_trace"] == [
        {"provider": "custom", "status": "executed", "supported": True}
    ]


def test_engine_enriches_text_and_math_without_mutating_raw_input():
    original = AcademicAnswer(raw_input="  5½  ", subject="mathematics", question_type="short")

    enriched = AcademicUnderstandingEngine().understand(original)

    assert enriched is not original
    assert original.raw_input == "  5½  "
    assert original.normalized_input is None
    assert enriched.raw_input == "  5½  "
    assert enriched.normalized_input == "5½"
    assert enriched.math_type == "numeric_like"
    assert enriched.metadata["providers"]["text"]["blank"] is False
    assert enriched.metadata["providers"]["math"]["math_type"] == "numeric_like"


def test_language_provider_detects_script_and_code_mixing():
    answer = AcademicAnswer(raw_input="factorisation कैसे करना?", subject="mathematics")

    enriched = AcademicUnderstandingEngine().understand(answer)

    assert enriched.detected_script == "mixed"
    assert enriched.code_mixed is True
    assert enriched.metadata["providers"]["language"]["scripts"] == ["devanagari", "latin"]


def test_language_provider_uses_subject_for_language_subjects():
    answer = AcademicAnswer(raw_input="ధన్యవాదాలు", subject="Telugu")

    enriched = AcademicUnderstandingEngine().understand(answer)

    assert enriched.detected_language == "te"
    assert enriched.detected_script == "telugu"
    assert enriched.code_mixed is False


def test_visual_provider_classifies_visual_question_type_without_checklist():
    answer = AcademicAnswer(
        raw_input="[answer-sheet image region]",
        subject="biology",
        question_type="diagram",
    )

    enriched = AcademicUnderstandingEngine().understand(answer)

    assert enriched.visual_type == "diagram"
    assert enriched.metadata["providers"]["visual"] == {"visual_type": "diagram"}
    assert "checklist" not in enriched.metadata["providers"]["visual"]


def test_scientific_provider_detects_equation_like_without_reasoning():
    answer = AcademicAnswer(raw_input="H2 + O2 -> H2O", subject="chemistry")

    enriched = AcademicUnderstandingEngine().understand(answer)

    assert enriched.scientific_type == "chemical_equation_like"
    assert enriched.metadata["providers"]["scientific"]["scientific_type"] == (
        "chemical_equation_like"
    )
    assert "balanced" not in enriched.metadata["providers"]["scientific"]


def test_confidence_provider_does_not_compute_top_level_confidence_in_batch_2():
    answer = AcademicAnswer(raw_input="answer")

    enriched = AcademicUnderstandingEngine().understand(answer)

    assert enriched.confidence is None
    assert enriched.metadata["providers"]["confidence"]["computed"] is False
