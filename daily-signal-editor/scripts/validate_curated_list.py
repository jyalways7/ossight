#!/usr/bin/env python3
"""Validate a Daily Signal Editor curated content queue."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BLOCKED_PHRASES = [
    "buy recommendation",
    "sell recommendation",
    "guaranteed return",
    "매수 추천",
    "매도 추천",
    "수익 보장",
]


def validate(text: str, min_items: int) -> list[str]:
    errors: list[str] = []
    if "# Daily Curated Content Queue" not in text:
        errors.append("Missing title: # Daily Curated Content Queue")
    if "## Ranked Queue" not in text:
        errors.append("Missing section: ## Ranked Queue")
    if "## Source Mix" not in text:
        errors.append("Missing section: ## Source Mix")
    item_count = len(re.findall(r"^####\s+\d+\.", text, flags=re.MULTILINE))
    if item_count < min_items:
        errors.append(f"Expected at least {min_items} curated items, found {item_count}.")
    links = re.findall(r"\[[^\]]+\]\(https?://[^)]+\)", text)
    if len(links) < min_items:
        errors.append(f"Expected at least {min_items} source links, found {len(links)}.")
    lowered = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in lowered:
            errors.append(f"Blocked investment-advice phrase found: {phrase}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--min-items", type=int, default=50)
    args = parser.parse_args()

    text = Path(args.path).read_text(encoding="utf-8")
    errors = validate(text, args.min_items)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
