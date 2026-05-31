"""Export OpenAPI schema for API v1 contract. Usage: python scripts/export_openapi.py"""
from __future__ import annotations

import json
from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "api" / "openapi-v1.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    OUT.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
