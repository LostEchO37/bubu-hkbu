#!/usr/bin/env python3
"""Quick check that LLM credentials work. Run from project root."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import chat_completion
from core.profile import StudentProfile


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY first.", file=sys.stderr)
        sys.exit(1)
    try:
        text = chat_completion("Reply with exactly: OK", [], StudentProfile())
        print("Success:", text)
    except Exception as exc:
        print("Failed:", exc, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
