#!/usr/bin/env python3
"""Score candidate source items for Daily Signal Editor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


WEIGHTS = {
    "freshness": 1.0,
    "source_quality": 1.2,
    "audience_fit": 1.4,
    "business_impact": 1.3,
    "novelty": 1.0,
    "signal_durability": 0.8,
    "content_potential": 1.1,
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_terms(values: list[str] | str | None) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        values = [values]
    return {value.strip().lower() for value in values if value.strip()}


def audience_fit(item: dict[str, Any], profile: dict[str, Any]) -> float:
    profile_terms = normalize_terms(profile.get("domains"))
    profile_terms |= normalize_terms(profile.get("audience"))
    profile_terms |= normalize_terms(profile.get("purpose"))
    item_terms = normalize_terms(item.get("topics"))
    text = " ".join(
        str(item.get(key, "")) for key in ("title", "summary", "why_it_matters")
    ).lower()

    matches = len(profile_terms & item_terms)
    text_matches = sum(1 for term in profile_terms if term and term in text)
    raw = 2.0 + matches * 0.8 + text_matches * 0.35
    return min(5.0, raw)


def score_items(
    items: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    source_by_id = {source["id"]: source for source in sources}
    scored: list[dict[str, Any]] = []

    for item in items:
        source = source_by_id.get(item.get("source_id"), {})
        durability = item.get("signal_durability")
        if durability is None:
            durability = min(
                5.0,
                (float(item.get("business_impact", 3)) + float(item.get("novelty", 3))) / 2 + 0.5,
            )
        dimensions = {
            "freshness": float(item.get("freshness", 3)),
            "source_quality": float(source.get("quality", 3)),
            "audience_fit": audience_fit(item, profile),
            "business_impact": float(item.get("business_impact", 3)),
            "novelty": float(item.get("novelty", 3)),
            "signal_durability": float(durability),
            "content_potential": float(item.get("content_potential", 3)),
        }
        weighted = sum(dimensions[key] * WEIGHTS[key] for key in WEIGHTS)
        max_weighted = 5 * sum(WEIGHTS.values())
        total = round((weighted / max_weighted) * 5, 2)
        scored.append(
            {
                **item,
                "source_name": source.get("name", item.get("source_id", "unknown")),
                "source_url": source.get("url"),
                "score": total,
                "score_dimensions": {key: round(value, 2) for key, value in dimensions.items()},
            }
        )

    return sorted(scored, key=lambda row: row["score"], reverse=True)


def item_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload, list):
        return payload
    raise TypeError("items input must be a list or an object with an 'items' list")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--items", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    scored = score_items(
        item_list(load_json(args.items)),
        load_json(args.sources),
        load_json(args.profile),
    )
    if args.limit:
        scored = scored[: args.limit]
    print(json.dumps(scored, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
