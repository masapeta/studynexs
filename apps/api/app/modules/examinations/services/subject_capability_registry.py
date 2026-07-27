"""Declarative Subject Capability Registry for Academic Evaluation Intelligence v1.

The registry is intentionally data-driven: it tells AEI what the platform may claim for a
subject/capability, but it does not evaluate answers. Runtime evaluation behavior is wired in
later AEI batches through providers, reasoners, and policy.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

CapabilityMode = Literal[
    "supported",
    "partial",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
]

SUPPORTED_MODES: set[str] = {
    "supported",
    "partial",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
}

REVIEW_REQUIRED_MODES: set[str] = {
    "partial",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
}

DEFAULT_REGISTRY_VERSION = "v1"
DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / f"subject_capability_registry.{DEFAULT_REGISTRY_VERSION}.json"
)


class SubjectCapabilityRegistryError(ValueError):
    """Raised when the Subject Capability Registry is malformed."""


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Resolved capability metadata for one subject capability."""

    subject: str
    area: str
    capability: str
    mode: CapabilityMode
    description: str = ""

    @property
    def teacher_review_required(self) -> bool:
        return self.mode in REVIEW_REQUIRED_MODES

    @property
    def supported_for_final_suggestion(self) -> bool:
        return self.mode == "supported"

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "area": self.area,
            "capability": self.capability,
            "mode": self.mode,
            "description": self.description,
            "teacher_review_required": self.teacher_review_required,
            "supported_for_final_suggestion": self.supported_for_final_suggestion,
        }


class SubjectCapabilityRegistry:
    """Read-only AEI capability registry.

    Unknown subjects/capabilities resolve to ``unsupported`` instead of raising at runtime. The
    registry file itself is validated on load so typos in configured modes fail loudly.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._validate()

    @classmethod
    def load_default(cls) -> "SubjectCapabilityRegistry":
        return cls.load_from_path(DEFAULT_REGISTRY_PATH)

    @classmethod
    def load_from_path(cls, path: Path) -> "SubjectCapabilityRegistry":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(data)

    @property
    def version(self) -> str:
        version = self._data.get("version")
        return version if isinstance(version, str) else ""

    def subjects(self) -> list[str]:
        subjects = self._data.get("subjects", {})
        return sorted(subjects.keys()) if isinstance(subjects, dict) else []

    def capabilities_for(self, subject: str, *, area: str = "evaluation") -> dict[str, Any]:
        subject_key = normalize_registry_key(subject)
        area_key = normalize_registry_key(area)
        subjects = self._data.get("subjects", {})
        subject_data = subjects.get(subject_key, {}) if isinstance(subjects, dict) else {}
        area_data = subject_data.get(area_key, {}) if isinstance(subject_data, dict) else {}
        return area_data if isinstance(area_data, dict) else {}

    def resolve(
        self,
        subject: str,
        capability: str,
        *,
        area: str = "evaluation",
    ) -> CapabilityDescriptor:
        subject_key = normalize_registry_key(subject)
        area_key = normalize_registry_key(area)
        capability_key = normalize_registry_key(capability)
        capability_data = self.capabilities_for(subject_key, area=area_key).get(capability_key)

        if not isinstance(capability_data, dict):
            return CapabilityDescriptor(
                subject=subject_key,
                area=area_key,
                capability=capability_key,
                mode="unsupported",
                description="Capability is not declared in the AEI Subject Capability Registry.",
            )

        mode = capability_data.get("mode", "unsupported")
        description = capability_data.get("description", "")
        return CapabilityDescriptor(
            subject=subject_key,
            area=area_key,
            capability=capability_key,
            mode=mode,
            description=description if isinstance(description, str) else "",
        )

    def _validate(self) -> None:
        version = self._data.get("version")
        if not isinstance(version, str) or not version.strip():
            raise SubjectCapabilityRegistryError("Subject Capability Registry requires a version")

        subjects = self._data.get("subjects")
        if not isinstance(subjects, dict) or not subjects:
            raise SubjectCapabilityRegistryError("Subject Capability Registry requires subjects")

        for subject, subject_data in subjects.items():
            if not isinstance(subject_data, dict):
                raise SubjectCapabilityRegistryError(f"Subject {subject!r} must be an object")
            for area, capabilities in subject_data.items():
                if not isinstance(capabilities, dict):
                    raise SubjectCapabilityRegistryError(
                        f"Subject {subject!r} area {area!r} must be an object"
                    )
                for capability, descriptor in capabilities.items():
                    if not isinstance(descriptor, dict):
                        raise SubjectCapabilityRegistryError(
                            f"Capability {subject}.{area}.{capability} must be an object"
                        )
                    mode = descriptor.get("mode")
                    if mode not in SUPPORTED_MODES:
                        raise SubjectCapabilityRegistryError(
                            f"Capability {subject}.{area}.{capability} has invalid mode {mode!r}"
                        )


def normalize_registry_key(value: str) -> str:
    """Normalize user-facing subject/capability labels into registry keys."""

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")
