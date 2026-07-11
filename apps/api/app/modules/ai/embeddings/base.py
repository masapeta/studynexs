"""Embedding provider interface — provider→model separation.

A provider (OpenAI, Ollama, SentenceTransformers, Azure, Gemini, …) exposes one or more
named models, each with a fixed vector dimension. Callers pick a model by name; the provider
validates it belongs to it. This keeps StudyNexs provider-agnostic while letting each provider
grow its model list over time without any architectural change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmbeddingModel:
    """One embedding model exposed by a provider."""

    name: str
    dimensions: int


@dataclass
class EmbeddingResult:
    """Vectors plus the metadata the RAG layer and metering need."""

    vectors: list[list[float]]
    provider: str
    model: str
    dimensions: int
    tokens: int = 0  # provider-reported usage where available (for cost metering)

    def __post_init__(self) -> None:
        if self.vectors and len(self.vectors[0]) != self.dimensions:
            raise ValueError(
                f"embedding dimension mismatch: got {len(self.vectors[0])}, "
                f"expected {self.dimensions} for {self.provider}/{self.model}"
            )


class EmbeddingProvider(ABC):
    """Base class for embedding providers. Subclasses declare their models and implement embed."""

    #: provider key used in config (e.g. "openai")
    name: str = ""
    #: model-name → EmbeddingModel. A provider may expose several.
    models: dict[str, EmbeddingModel] = field(default_factory=dict)
    #: the model used when none is specified
    default_model_name: str = ""

    def resolve_model(self, model: str | None) -> EmbeddingModel:
        """Return the EmbeddingModel for ``model`` (or the provider default). Fail loud on a
        model that this provider does not expose — never silently embed with the wrong model."""
        name = model or self.default_model_name
        spec = self.models.get(name)
        if spec is None:
            raise ValueError(
                f"{self.name!r} does not expose embedding model {name!r}; "
                f"available: {sorted(self.models)}"
            )
        return spec

    @abstractmethod
    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbeddingResult:
        """Embed a batch of texts with the given (or default) model."""
        raise NotImplementedError
