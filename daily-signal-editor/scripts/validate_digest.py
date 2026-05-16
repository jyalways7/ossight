#!/usr/bin/env python3
"""Validate a Daily Signal Editor Markdown brief."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_SECTIONS = [
    "# Daily Signal Brief",
    "## Executive Read",
    "## Pattern Synthesis",
    "## Top Signals",
    "## Content Starters",
    "## Actionable Artifacts",
    "## Caveats",
]

BLOCKED_INVESTMENT_PHRASES = [
    "buy recommendation",
    "sell recommendation",
    "guaranteed return",
    "매수 추천",
    "매도 추천",
    "수익 보장",
]


def validate(text: str) -> list[str]:
    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing section: {section}")

    links = re.findall(r"\[[^\]]+\]\(https?://[^)]+\)", text)
    if len(links) < 3:
        errors.append("Expected at least 3 source links.")

    if "Why it matters" not in text:
        errors.append("Expected at least one 'Why it matters' line.")

    if "not financial advice" not in text.lower() and "financial advice" in text.lower():
        errors.append("Investment caveat is unclear.")

    lowered = text.lower()
    for phrase in BLOCKED_INVESTMENT_PHRASES:
        if phrase.lower() in lowered:
            errors.append(f"Blocked investment-advice phrase found: {phrase}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    text = Path(args.path).read_text(encoding="utf-8")
    errors = validate(text)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
