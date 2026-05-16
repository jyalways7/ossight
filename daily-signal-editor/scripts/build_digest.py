#!/usr/bin/env python3
"""Build a Markdown daily signal brief from candidate items."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from score_items import item_list, load_json, score_items


def content_angle(item: dict) -> str:
    title = item["title"].rstrip(".")
    topics = ", ".join(item.get("topics", [])[:3])
    return f"What {title.lower()} tells us about {topics}"


def top_topics(items: list[dict], limit: int = 4) -> list[str]:
    counts: dict[str, int] = {}
    for item in items:
        for topic in item.get("topics", []):
            counts[topic] = counts.get(topic, 0) + 1
    return [
        topic
        for topic, _count in sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:limit]
    ]


def synthesize_pattern(top: list[dict], profile: dict) -> str:
    topics = top_topics(top)
    audience = profile.get("audience", "the target audience")
    if not topics:
        return f"For {audience}, the selected signals need more evidence before a directional pattern is clear."
    topic_text = ", ".join(topics)
    return (
        f"Across the selected signals, the common pattern is that {topic_text} are converging into "
        f"repeatable business workflows rather than isolated announcements. For {audience}, this "
        f"suggests a practical shift: track who owns the workflow, what data loop compounds, and "
        f"which local market constraints could slow adoption."
    )


def contrarian_view(top: list[dict]) -> str:
    weaker = [item for item in top if item.get("score", 0) < 4.3]
    if weaker:
        return (
            "The pattern may still be early: some supporting items are secondary or headline-driven, "
            "so look for primary-source confirmation before treating it as a durable market shift."
        )
    return (
        "The biggest counterpoint is that high-quality sources can still reinforce the same narrative; "
        "validate with customer behavior, adoption data, or funding follow-through."
    )


def artifact_label(profile: dict) -> str:
    mode = str(profile.get("output_mode", "")).lower()
    purpose = str(profile.get("purpose", "")).lower()
    audience = str(profile.get("audience", "")).lower()
    if "slack" in mode or "team" in mode or "corporate" in audience:
        return "Slack Team Update"
    if "meeting" in mode or "strategy" in purpose:
        return "Strategy Meeting Agenda"
    if "sales" in mode or "sales" in audience:
        return "Sales Talking Points"
    if "linkedin" in mode or "content" in purpose or "newsletter" in mode:
        return "LinkedIn/Newsletter Hooks"
    if "investment" in purpose or "investor" in audience:
        return "Research Memo Questions"
    return "Next Actions"


def render_artifacts(profile: dict, top: list[dict]) -> list[str]:
    label = artifact_label(profile)
    lines = [f"## Actionable Artifacts: {label}", ""]
    if label == "Slack Team Update":
        lines.extend(
            [
                "*Today’s signal read*",
                "",
                f"- Main pattern: {synthesize_pattern(top, profile)}",
                f"- Discuss: {top[0]['title']} and what it changes for our roadmap.",
                f"- Source to read first: [{top[0]['source_name']}]({top[0]['url']})",
                "- Open question: What customer behavior would prove this is more than narrative?",
                "",
            ]
        )
    elif label == "Strategy Meeting Agenda":
        lines.extend(
            [
                "1. What market assumption should we update?",
                f"2. What does `{top[0]['title']}` imply for our positioning?",
                "3. What evidence would make us change roadmap, hiring, or partnership priorities?",
                "4. What should we monitor next week?",
                "",
            ]
        )
    elif label == "Sales Talking Points":
        lines.extend(
            [
                f"- Customer hook: Teams in this market are reacting to {top[0]['title'].lower()}.",
                "- Discovery question: Where is this workflow still manual or expensive for your team?",
                "- Proof point: Use the top source link as a non-salesy reason to start the conversation.",
                "",
            ]
        )
    elif label == "Research Memo Questions":
        lines.extend(
            [
                "- Thesis candidate: Workflow-specific data and distribution may matter more than thin AI wrappers.",
                "- Counter-signal to check: Are customers paying, or is the theme mostly investor narrative?",
                "- Follow-up evidence: funding rounds, product launches, customer case studies, and regulatory changes.",
                "",
            ]
        )
    else:
        for index, item in enumerate(top[:3], start=1):
            lines.append(f"{index}. Hook: {content_angle(item)}")
            lines.append(f"   Evidence: {item['source_name']} item, score {item['score']} / 5.")
            lines.append("   CTA: Ask readers what workflow, market, or product assumption this changes.")
            lines.append("")
    return lines


def render_digest(profile: dict, scored_items: list[dict], max_signals: int) -> str:
    top = scored_items[:max_signals]
    audience = profile.get("audience", "general business reader")
    purpose = profile.get("purpose", "market research")
    domains = ", ".join(profile.get("domains", []))

    lines: list[str] = [
        "# Daily Signal Brief",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Audience: {audience}",
        f"- Purpose: {purpose}",
        f"- Domains: {domains}",
        "",
        "## Executive Read",
        "",
        synthesize_pattern(top, profile),
        "",
        "## Pattern Synthesis",
        "",
        f"- Directional read: {synthesize_pattern(top, profile)}",
        f"- Contrarian view: {contrarian_view(top)}",
        "- Evidence to verify next: primary-source announcements, customer behavior, funding data, and local-market adoption signals.",
        "",
        "## Top Signals",
        "",
    ]

    for index, item in enumerate(top, start=1):
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- Source: [{item['source_name']}]({item['url']})",
                f"- Score: {item['score']} / 5",
                f"- Signal durability: {item['score_dimensions'].get('signal_durability', 'n/a')} / 5",
                f"- What happened: {item['summary']}",
                f"- Why it matters: {item.get('why_it_matters', 'This may affect the target audience.')}",
                f"- Who cares: {audience}",
                "- What to watch: Look for repeat evidence from primary sources, customer behavior, funding data, or product launches.",
                f"- Content angle: {content_angle(item)}",
                "",
            ]
        )

    lines.extend(
        [
            "## Content Starters",
            "",
        ]
    )
    for index, item in enumerate(top[:3], start=1):
        lines.append(f"{index}. Hook: {content_angle(item)}")
        lines.append(f"   Evidence: {item['source_name']} item, score {item['score']} / 5.")
        lines.append("   CTA: Ask readers what workflow, market, or product assumption this changes.")
        lines.append("")

    lines.extend(render_artifacts(profile, top))

    lines.extend(
        [
            "## Watch Next",
            "",
            "- Confirm whether the same theme appears in at least one primary source.",
            "- Track Korean localization: regulation, distribution, payments, trust, and enterprise buying behavior.",
            "- Turn the strongest signal into one long-form memo and two short-form posts.",
            "",
            "## Caveats",
            "",
            "- This brief uses mock or public RSS-style source metadata for a reproducible local demo.",
            "- This is source-backed research and content ideation, not financial advice.",
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
    parser.add_argument("--max-signals", type=int, default=5)
    args = parser.parse_args()

    scored = score_items(
        item_list(load_json(args.items)),
        load_json(args.sources),
        load_json(args.profile),
    )
    digest = render_digest(load_json(args.profile), scored, args.max_signals)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
