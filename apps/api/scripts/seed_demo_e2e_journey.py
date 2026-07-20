"""Deprecated — use seed_reference_school.py instead."""
from __future__ import annotations

import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import seed_reference_school

if __name__ == "__main__":
    seed_reference_school.main()
