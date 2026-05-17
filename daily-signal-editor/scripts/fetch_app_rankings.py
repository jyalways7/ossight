#!/usr/bin/env python3
"""Fetch public app ranking sources into Daily Signal Editor item JSON."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from score_items import load_json


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def fetch_json(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "daily-signal-editor/0.1 (+public app rankings)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def apple_feed_items(source: dict[str, Any], payload: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    feed = payload.get("feed", {})
    results = feed.get("results", [])[:limit]
    items: list[dict[str, Any]] = []
    for index, app in enumerate(results, start=1):
        name = app.get("name") or f"App rank {index}"
        artist = app.get("artistName", "확인 필요")
        genres = [genre.get("name", "") for genre in app.get("genres", []) if genre.get("name")]
        genre_text = ", ".join(genres[:3]) or "확인 필요"
        topics = ["app_rankings", "consumer", "product"]
        if any("game" in genre.lower() for genre in genres):
            topics.append("content_ip")
        items.append(
            {
                "id": f"{source['id']}-{index}",
                "source_id": source["id"],
                "title": f"#{index} {name} on {source['name']}",
                "url": app.get("url") or source.get("url", ""),
                "published": today(),
                "summary": f"{name} 앱이 {source['name']}에서 {index}위에 올랐어요. 퍼블리셔는 {artist}, 카테고리는 {genre_text}예요.",
                "topics": topics,
                "freshness": 5,
                "business_impact": 4 if index <= 3 else 3,
                "novelty": 4 if index <= 5 else 3,
                "content_potential": 4 if index <= 5 else 3,
                "why_it_matters": "앱 순위 변화는 사람들이 실제로 설치하고 써보는 관심사를 보여줘요. 제품 아이디어, 카테고리 경쟁, 콘텐츠 훅을 찾을 때 좋은 초기 신호예요.",
            }
        )
    return items


def fetch_source(source: dict[str, Any], timeout: int, limit: int) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
    url = source.get("api_url")
    if not url:
        return [], {"source_id": source.get("id", "unknown"), "error": "missing api_url"}
    try:
        payload = fetch_json(url, timeout)
        if source.get("provider") == "apple-rss-json" or "rss.applemarketingtools.com" in url:
            return apple_feed_items(source, payload, limit), None
        return [], {"source_id": source.get("id", "unknown"), "error": "unsupported app ranking provider"}
    except Exception as exc:
        return [], {"source_id": source.get("id", "unknown"), "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-items-per-source", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    sources = load_json(args.sources)
    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        items, error = fetch_source(source, args.timeout, args.max_items_per_source)
        all_items.extend(items)
        if error:
            errors.append(error)

    Path(args.output).write_text(
        json.dumps({"items": all_items, "errors": errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(all_items)} app ranking items to {args.output}")
    if errors:
        print(f"Encountered {len(errors)} source errors.")
    return 0 if all_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
