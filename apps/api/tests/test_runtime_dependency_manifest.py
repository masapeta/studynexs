"""Runtime dependency manifests must declare directly imported production packages."""

from __future__ import annotations

import tomllib
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]


def test_security_document_and_pdf_dependencies_are_directly_declared():
    project = tomllib.loads((API_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = "\n".join(project["dependencies"]).lower()
    requirements = (API_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()

    for package in ("cryptography", "pypdf", "pillow", "pytesseract", "weasyprint"):
        assert package in dependencies
        assert package in requirements


def test_pdf_native_runtime_is_declared_in_the_container_image():
    dockerfile = (API_ROOT / "Dockerfile").read_text(encoding="utf-8")

    for package in (
        "libfontconfig.so.1",
        "libgobject-2.0.so.0",
        "libharfbuzz.so.0",
        "libharfbuzz-subset.so.0",
        "libpango-1.0.so.0",
        "libpangoft2-1.0.so.0",
        "font-noto-devanagari",
        "font-noto-telugu",
        'XDG_CACHE_HOME="/app/.cache"',
    ):
        assert package in dockerfile
