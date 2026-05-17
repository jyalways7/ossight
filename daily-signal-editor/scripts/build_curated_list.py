#!/usr/bin/env python3
"""Build a ranked Markdown queue of curated candidate items."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from score_items import item_list, load_json, score_items


BLOCKED_CONTENT_TERMS = [
    "porn",
    "smutty",
    "sexual",
    "bedroom",
]


def is_allowed_item(item: dict) -> bool:
    if item.get("topics") == ["general"]:
        return False
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary")).lower()
    return not any(term in text for term in BLOCKED_CONTENT_TERMS)


def select_queue(
    scored_items: list[dict],
    limit: int,
    max_per_source: int,
    min_score: float,
    min_audience_fit: float,
) -> list[dict]:
    selected: list[dict] = []
    per_source: Counter[str] = Counter()

    for item in scored_items:
        if item.get("score", 0) < min_score:
            continue
        if item.get("score_dimensions", {}).get("audience_fit", 0) < min_audience_fit:
            continue
        if not is_allowed_item(item):
            continue
        source = item.get("source_id", "unknown")
        if per_source[source] >= max_per_source:
            continue
        selected.append(item)
        per_source[source] += 1
        if len(selected) >= limit:
            return selected

    for item in scored_items:
        if item in selected:
            continue
        if item.get("score", 0) < min_score:
            continue
        if item.get("score_dimensions", {}).get("audience_fit", 0) < min_audience_fit:
            continue
        if not is_allowed_item(item):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def tier_label(score: float) -> str:
    if score >= 4.2:
        return "A. Lead Signals"
    if score >= 3.6:
        return "B. Strong Candidates"
    return "C. Watchlist"


def format_topics(item: dict) -> str:
    topics = item.get("topics") or []
    return ", ".join(topics[:5]) if topics else "general"


def render_queue(profile: dict, queue: list[dict], scored_count: int) -> str:
    audience = profile.get("audience", "general reader")
    purpose = profile.get("purpose", "daily research")
    source_counts = Counter(item.get("source_name", item.get("source_id", "unknown")) for item in queue)

    lines = [
        "# Daily Curated Content Queue",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Audience: {audience}",
        f"- Purpose: {purpose}",
        f"- Curated items: {len(queue)} / {scored_count}",
        "",
        "## Source Mix",
        "",
    ]
    for source, count in source_counts.most_common():
        lines.append(f"- {source}: {count}")

    lines.extend(["", "## Ranked Queue", ""])
    current_tier = ""
    for index, item in enumerate(queue, start=1):
        tier = tier_label(float(item.get("score", 0)))
        if tier != current_tier:
            current_tier = tier
            lines.extend([f"### {current_tier}", ""])
        lines.extend(
            [
                f"#### {index}. {item['title']}",
                f"- Source: [{item.get('source_name', item.get('source_id', 'unknown'))}]({item.get('url', '')})",
                f"- Published: {item.get('published', 'unknown')}",
                f"- Score: {item.get('score', 'n/a')} / 5",
                f"- Topics: {format_topics(item)}",
                f"- Summary: {item.get('summary', 'No summary available.')}",
                f"- Why it matters: {item.get('why_it_matters', 'Needs more evidence before use.')}",
                "",
            ]
        )

    lines.extend(
        [
            "## How To Use This Queue",
            "",
            "- Use A-tier items for the daily brief and strategic synthesis.",
            "- Use B-tier items for content ideas, meeting prep, and follow-up reading.",
            "- Use C-tier items as weak signals unless confirmed by stronger primary sources.",
            "- Promote an item only when it has source evidence, audience fit, and a clear next action.",
            "",
            "## Caveats",
            "",
            "- This queue is source-backed curation, not investment advice.",
            "- Public RSS summaries can be incomplete; verify high-impact claims with the original source.",
            "- Do not copy paid or login-only source text into generated outputs.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--items", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--max-per-source", type=int, default=8)
    parser.add_argument("--min-score", type=float, default=2.8)
    parser.add_argument("--min-audience-fit", type=float, default=2.0)
    args = parser.parse_args()

    profile = load_json(args.profile)
    scored = score_items(
        item_list(load_json(args.items)),
        load_json(args.sources),
        profile,
    )
    queue = select_queue(scored, args.limit, args.max_per_source, args.min_score, args.min_audience_fit)
    output = render_queue(profile, queue, len(scored))
    Path(args.output).write_text(output, encoding="utf-8")
    print(f"Wrote {len(queue)} curated items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
