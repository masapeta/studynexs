"""Tests for teacher-style SSML speech preparation."""

from app.modules.tutor.services.speech_prepare import (
    build_teacher_ssml,
    prepare_teacher_speech_text,
    rate_for_step_title,
)


def test_rate_slower_for_teacher_explains():
    assert rate_for_step_title("Teacher explains") == "-16%"
    assert rate_for_step_title("What went wrong") == "-10%"


def test_prepare_teacher_speech_text_uses_plain_paragraph_pauses():
    plain = prepare_teacher_speech_text("First idea. Second idea?")
    assert "<speak" not in plain
    assert "version" not in plain
    assert "First idea." in plain
    assert "Second idea?" in plain
    assert "\n\n" in plain


def test_build_teacher_ssml_inserts_pauses_and_prosody():
    ssml = build_teacher_ssml(
        "First idea. Second idea?",
        "en-IN-NeerjaExpressiveNeural",
        rate="-14%",
    )
    assert ssml.startswith("<speak")
    assert "NeerjaExpressiveNeural" in ssml
    assert "<break time=" in ssml
    assert "rate='-14%'" in ssml
    assert "First idea." in ssml
    assert "Second idea?" in ssml
