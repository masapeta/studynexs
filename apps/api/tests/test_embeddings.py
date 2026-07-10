"""Shared Embedding Service — provider→model abstraction, determinism, and a live OpenAI check.

Unit tests use the offline deterministic stub (no cost/network). One integration test hits real
OpenAI and is skipped unless an API key is configured."""

import pytest

from app.core.config import get_settings
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.base import EmbeddingProvider
from app.modules.ai.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider


def _svc() -> EmbeddingService:
    return EmbeddingService(provider=StubEmbeddingProvider())


@pytest.mark.asyncio
async def test_stub_embeddings_are_deterministic_and_unit_length():
    svc = _svc()
    a1 = await svc.embed_one("Photosynthesis in plants", feature="test")
    a2 = await svc.embed_one("Photosynthesis in plants", feature="test")
    b = await svc.embed_one("The French Revolution", feature="test")
    assert a1 == a2  # same text → same vector
    assert a1 != b  # different text → different vector
    assert len(a1) == svc.dimensions()
    assert abs(sum(x * x for x in a1) ** 0.5 - 1.0) < 1e-6  # unit-normalized


@pytest.mark.asyncio
async def test_batch_preserves_order_and_shape():
    svc = _svc()
    texts = ["alpha", "beta", "gamma"]
    result = await svc.embed(texts, feature="test")
    assert len(result.vectors) == 3
    assert result.dimensions == svc.dimensions()
    # order preserved: embedding of texts[i] matches a standalone embed of the same text
    solo = await svc.embed_one("beta", feature="test")
    assert result.vectors[1] == solo


@pytest.mark.asyncio
async def test_empty_input_returns_no_vectors():
    result = await _svc().embed([], feature="test")
    assert result.vectors == []


def test_provider_model_separation_and_unknown_model_rejected():
    p = OpenAIEmbeddingProvider()
    # Provider exposes multiple models with distinct dimensions.
    assert p.resolve_model(None).name == "text-embedding-3-small"
    assert p.resolve_model("text-embedding-3-small").dimensions == 1536
    assert p.resolve_model("text-embedding-3-large").dimensions == 3072
    # A model not exposed by this provider is rejected, not silently accepted.
    with pytest.raises(ValueError):
        p.resolve_model("some-other-providers-model")


def test_result_dimension_mismatch_is_caught():
    from app.modules.ai.embeddings.base import EmbeddingResult

    with pytest.raises(ValueError):
        EmbeddingResult(vectors=[[0.1, 0.2]], provider="x", model="m", dimensions=1536)


def test_service_is_provider_agnostic_via_injection():
    # No app code names a concrete provider; the service takes any EmbeddingProvider.
    assert isinstance(_svc()._provider, EmbeddingProvider)


@pytest.mark.asyncio
@pytest.mark.skipif(
    not get_settings().OPENAI_API_KEY, reason="no OPENAI_API_KEY configured"
)
async def test_openai_live_embedding_small_model():
    """Live check: OpenAI returns 1536-dim vectors for text-embedding-3-small."""
    svc = EmbeddingService(provider=OpenAIEmbeddingProvider())
    result = await svc.embed(["StudyNexs curriculum intelligence"], feature="test", model=None)
    assert result.provider == "openai"
    assert result.model == "text-embedding-3-small"
    assert result.dimensions == 1536
    assert len(result.vectors[0]) == 1536
    assert result.tokens > 0
