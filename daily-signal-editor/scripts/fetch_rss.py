#!/usr/bin/env python3
"""Fetch public RSS/Atom feeds into Daily Signal Editor item JSON."""

from __future__ import annotations

import argparse
import email.utils
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from score_items import load_json


TOPIC_KEYWORDS = {
    "ai": ["ai", "agent", "llm", "model", "openai", "anthropic", "automation"],
    "startups": ["startup", "founder", "yc", "seed", "growth"],
    "vc": ["vc", "venture", "funding", "investment", "investor"],
    "business": ["business", "market", "revenue", "pricing", "sales", "enterprise"],
    "developer": ["developer", "code", "github", "open source", "api"],
    "korea": ["korea", "korean", "한국", "국내", "스타트업"],
}


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def child_text(node: ET.Element, names: list[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    for child in list(node):
        tag = child.tag.split("}", 1)[-1]
        if tag in names and child.text:
            return child.text.strip()
    return ""


def child_link(node: ET.Element) -> str:
    link = child_text(node, ["link"])
    if link:
        return link
    for child in list(node):
        tag = child.tag.split("}", 1)[-1]
        if tag == "link" and child.attrib.get("href"):
            return child.attrib["href"]
    return ""


def parse_date(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except (TypeError, ValueError):
        return value[:10]


def freshness_score(value: str) -> int:
    try:
        published = datetime.fromisoformat(value[:10]).date()
        today = datetime.now(timezone.utc).date()
        days = (today - published).days
    except ValueError:
        return 3
    if days <= 3:
        return 5
    if days <= 14:
        return 4
    if days <= 60:
        return 3
    if days <= 180:
        return 2
    return 1


def infer_topics(text: str, defaults: list[str]) -> list[str]:
    lowered = text.lower()
    topics = set()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            topics.add(topic)
    if not topics:
        topics.update(defaults[:2])
    return sorted(topics)


def score_hint(text: str, base: int = 3) -> int:
    lowered = text.lower()
    strong_terms = ["ai", "agent", "startup", "market", "workflow", "funding", "enterprise"]
    weak_terms = ["joins", "welcome", "congratulations", "podcast", "event"]
    score = base + sum(1 for term in strong_terms if term in lowered) // 2
    if any(term in lowered for term in weak_terms):
        score -= 1
    return max(1, min(5, score))


def fetch_feed(source: dict[str, Any], timeout: int, max_items: int) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        source["feed_url"],
        headers={"User-Agent": "daily-signal-editor/0.1 (+public RSS demo)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        xml_bytes = response.read()

    root = ET.fromstring(xml_bytes)
    nodes = root.findall(".//item")
    if not nodes:
        nodes = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    items: list[dict[str, Any]] = []
    for index, node in enumerate(nodes[:max_items], start=1):
        title = strip_tags(child_text(node, ["title"]))
        url = child_link(node)
        summary = strip_tags(
            child_text(node, ["description", "summary", "content", "encoded"])
        )
        published = parse_date(child_text(node, ["pubDate", "published", "updated"]))
        text = f"{title} {summary}"
        topics = infer_topics(text, source.get("domains", []))
        freshness = freshness_score(published)
        impact = score_hint(text, 3)
        content = score_hint(text, 3)
        items.append(
            {
                "id": f"{source['id']}-{index}",
                "source_id": source["id"],
                "title": title or f"{source['name']} item {index}",
                "url": url or source.get("url", ""),
                "published": published,
                "summary": summary[:420] or "No summary provided by feed.",
                "topics": topics,
                "freshness": freshness,
                "business_impact": impact,
                "novelty": 3,
                "content_potential": content,
                "why_it_matters": "This public feed item may indicate a useful market, product, technology, or narrative signal for the target audience.",
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-items-per-source", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    sources = load_json(args.sources)
    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        if not source.get("feed_url"):
            continue
        try:
            all_items.extend(fetch_feed(source, args.timeout, args.max_items_per_source))
        except Exception as exc:  # noqa: BLE001 - keep feed errors non-fatal for demos.
            errors.append({"source": source.get("id", "unknown"), "error": str(exc)})

    payload = {"items": all_items, "errors": errors}
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_items)} items to {args.output}")
    if errors:
        print(f"Feed errors: {len(errors)}")
        for error in errors:
            print(f"- {error['source']}: {error['error']}")
    return 0 if all_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
