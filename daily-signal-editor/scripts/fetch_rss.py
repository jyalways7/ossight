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
    "ai": ["ai", "agent", "agents", "llm", "model", "openai", "anthropic", "automation", "claude", "codex"],
    "workflow": ["workflow", "workflows", "brief", "briefs", "packet", "packets", "plan", "plans", "diagnosis", "updates"],
    "startups": ["startup", "startups", "founder", "founders", "yc", "seed", "growth"],
    "vc": ["vc", "venture", "funding", "investment", "investor"],
    "business": ["business", "market", "revenue", "pricing", "sales", "enterprise", "operations", "pipeline"],
    "developer": ["developer", "developers", "code", "github", "open source", "api", "data science"],
    "security": ["ctf", "security", "vulnerability", "privacy"],
    "legal": ["legal", "law", "privacy", "regulatory", "governance", "compliance", "법률", "규제"],
    "korea": ["korea", "korean", "한국", "국내", "스타트업"],
}


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def attr_content(html_text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return strip_tags(match.group(1))
    return ""


def fetch_page_context(url: str, timeout: int) -> str:
    if not url.startswith(("http://", "https://")):
        return ""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "daily-signal-editor/0.1 (+public page context)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            return ""
        html_text = response.read(600_000).decode("utf-8", errors="ignore")

    meta = attr_content(
        html_text,
        [
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        ],
    )
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html_text, flags=re.IGNORECASE | re.DOTALL)
    paragraph_text = " ".join(strip_tags(paragraph) for paragraph in paragraphs[:4])
    context = " ".join(part for part in [meta, paragraph_text] if part)
    return context[:900]


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
        if any(has_keyword(lowered, keyword) for keyword in keywords):
            topics.add(topic)
    if not topics:
        topics.add("general")
    return sorted(topics)


def has_keyword(text: str, keyword: str) -> bool:
    if re.search(r"[가-힣]", keyword):
        return keyword in text
    escaped = re.escape(keyword.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def score_hint(text: str, base: int = 3) -> int:
    lowered = text.lower()
    strong_terms = ["ai", "agent", "startup", "market", "workflow", "funding", "enterprise"]
    weak_terms = ["joins", "welcome", "congratulations", "podcast", "event"]
    score = base + sum(1 for term in strong_terms if has_keyword(lowered, term)) // 2
    if any(has_keyword(lowered, term) for term in weak_terms):
        score -= 1
    return max(1, min(5, score))


def novelty_hint(text: str) -> int:
    lowered = text.lower()
    if any(term in lowered for term in ["new", "launch", "announces", "introduces", "goes public", "funding"]):
        return 4
    if any(term in lowered for term in ["joins", "welcome", "congratulations"]):
        return 2
    return 3


def why_it_matters(text: str, topics: list[str]) -> str:
    lowered = text.lower()
    topic_set = set(topics)
    if "databricks" in lowered and "agent" in lowered:
        return "Enterprise AI agents are being tested inside data-heavy work environments, which makes reliability, evaluation, and workflow integration more important than generic chat capability."
    if "legal" in topic_set and "ai" in topic_set:
        return "Domain-specific AI agents are moving into regulated professional workflows, which makes trust, data access, and review loops central product questions."
    if "sales" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "AI work assistants are expanding from engineering into revenue workflows, creating concrete B2B SaaS use cases around account research, pipeline review, and meeting prep."
    if "operations" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "Operational teams are being offered AI-generated decision packets and status updates, which points to workflow software shifting from dashboards to prepared judgment artifacts."
    if "data science" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "AI coding agents are being packaged for analytical workflows, suggesting demand for tools that turn messy work inputs into root-cause briefs and dashboard specs."
    if "goes public" in lowered or "operating system" in lowered:
        return "A vertical workflow company reaching public-market scale is evidence that narrow operating systems can compound when they own daily work data."
    if "incorporation" in lowered:
        return "Changes in accepted incorporation paths affect where founders can start and scale, which can shift cross-border startup formation and investor access."
    if "general partner" in lowered:
        return "A platform investor's partner hire can reveal which founder backgrounds, sectors, or networks the platform expects to matter next."
    if "security" in topic_set:
        return "Developer community shifts in security practice can become early signals for tooling, hiring, and education demand."
    return "This item is a candidate signal, but it needs a stronger primary-source pattern before it should drive strategy."


def fetch_feed(
    source: dict[str, Any],
    timeout: int,
    max_items: int,
    enrich_pages: bool,
) -> list[dict[str, Any]]:
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
        page_context = ""
        if enrich_pages and url:
            try:
                page_context = fetch_page_context(url, timeout)
            except Exception:
                page_context = ""
        if len(summary) < 80 and page_context:
            summary = page_context
        text = f"{title} {summary}"
        topics = infer_topics(text, source.get("domains", []))
        freshness = freshness_score(published)
        impact = score_hint(text, 3)
        content = score_hint(text, 3)
        novelty = novelty_hint(text)
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
                "novelty": novelty,
                "content_potential": content,
                "why_it_matters": why_it_matters(text, topics),
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-items-per-source", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--no-enrich-pages", action="store_true")
    args = parser.parse_args()

    sources = load_json(args.sources)
    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        if not source.get("feed_url"):
            continue
        try:
            all_items.extend(
                fetch_feed(
                    source,
                    args.timeout,
                    args.max_items_per_source,
                    enrich_pages=not args.no_enrich_pages,
                )
            )
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
