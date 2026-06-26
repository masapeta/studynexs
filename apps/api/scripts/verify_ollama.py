"""Verify Ollama fallback configuration (no secrets printed).

Usage:
    python apps/api/scripts/verify_ollama.py
    # or from apps/api:
    python scripts/verify_ollama.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _API_ROOT / ".env"

# Ensure imports resolve when invoked from repo root.
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.core.config import Settings, _ENV_FILE as CONFIG_ENV_FILE
from app.modules.ai.gateway.base import LLMMessage
from app.modules.ai.gateway.ollama import OllamaProvider


def _check_config(s: Settings) -> list[str]:
    issues: list[str] = []
    if not (s.AI_FALLBACK_PROVIDER or "").strip():
        issues.append("AI_FALLBACK_PROVIDER is not set (expected: ollama)")
    if not (s.OLLAMA_BASE_URL or "").strip():
        issues.append("OLLAMA_BASE_URL is not set")
    key = (s.OLLAMA_API_KEY or "").strip()
    if not key and (s.OLLAMA_BASE_URL or "").strip().startswith("https://ollama.com"):
        issues.append("OLLAMA_API_KEY is required when OLLAMA_BASE_URL=https://ollama.com")
    if key.startswith("ssh-"):
        issues.append(
            "OLLAMA_API_KEY looks like an SSH public key - create a real API key at "
            "https://ollama.com (Account -> API keys)"
        )
    elif " " in key:
        issues.append(
            "OLLAMA_API_KEY contains a space — wrap the value in quotes in .env, "
            'e.g. OLLAMA_API_KEY="your-key-here"'
        )
    return issues


async def _ping_ollama(s: Settings) -> None:
    provider = OllamaProvider()
    result = await provider.generate(
        [LLMMessage("user", "Reply with exactly: OK")],
        model=s.OLLAMA_MODEL,
        max_tokens=16,
        temperature=0,
    )
    snippet = (result.text or "").strip().replace("\n", " ")[:80]
    print(f"Ollama response OK — provider={result.provider} model={result.model}")
    print(f"Sample output: {snippet!r}")


def main() -> int:
    s = Settings()
    print("Config check")
    print(f"  env_file={CONFIG_ENV_FILE} (exists={CONFIG_ENV_FILE.is_file()})")
    print(f"  AI_DEFAULT_PROVIDER={s.AI_DEFAULT_PROVIDER}")
    print(f"  AI_FALLBACK_PROVIDER={s.AI_FALLBACK_PROVIDER or '(empty)'}")
    print(f"  OLLAMA_BASE_URL={s.OLLAMA_BASE_URL or '(empty)'}")
    print(f"  OLLAMA_MODEL={s.OLLAMA_MODEL}")
    print(f"  OLLAMA_API_KEY={'set' if (s.OLLAMA_API_KEY or '').strip() else 'not set'}")

    issues = _check_config(s)
    if issues:
        print("\nIssues:")
        for item in issues:
            print(f"  - {item}")
        return 1

    print("\nPinging Ollama...")
    try:
        asyncio.run(_ping_ollama(s))
    except Exception as exc:
        print(f"\nOllama call failed: {type(exc).__name__}: {exc}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
