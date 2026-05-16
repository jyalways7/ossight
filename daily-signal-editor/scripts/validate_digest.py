#!/usr/bin/env python3
"""Validate a Daily Signal Editor Markdown brief."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_SECTION_ALIASES = {
    "title": ["# Daily Signal Brief", "Daily Signal Brief)"],
    "executive": ["## Executive Read", "### Executive Read", "오늘 이것만은 꼭"],
    "pattern": ["## Pattern Synthesis", "### Pattern Synthesis", "정보들 사이의 숨은 그림 찾기"],
    "top_signals": ["## Top Signals", "### Top Signals", "깊이 읽어볼 뉴스"],
    "actionable": [
        "## Actionable Artifacts",
        "Actionable Artifacts",
        "Strategy Meeting Agenda",
        "바로 써먹는 콘텐츠",
        "지금 팀원들과 공유",
        "지금 팀원들에게 공유",
    ],
    "caveats": ["## Caveats", "## Caveats / 주의사항", "주의사항"],
}

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
    for section_name, aliases in REQUIRED_SECTION_ALIASES.items():
        if not any(alias in text for alias in aliases):
            errors.append(f"Missing section group: {section_name}")

    links = re.findall(r"\[[^\]]+\]\(https?://[^)]+\)", text)
    if len(links) < 3:
        errors.append("Expected at least 3 source links.")

    if "Why it matters" not in text and "왜 중요한" not in text and "나에게 왜" not in text:
        errors.append("Expected at least one 'Why it matters' or Korean equivalent line.")

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
