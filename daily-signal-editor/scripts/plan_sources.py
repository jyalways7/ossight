#!/usr/bin/env python3
"""Select and rotate sources for Daily Signal Editor."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from score_items import load_json, normalize_terms


ACCESS_WEIGHT = {
    "rss": 0.6,
    "public_web": 0.3,
    "public_report": 0.3,
    "mixed_public_paid": -0.2,
}


TYPE_DIVERSITY_ORDER = [
    "official_blog",
    "vc_blog",
    "newsletter",
    "public_report",
    "media",
    "community",
    "youtube",
]


def terms_from_profile(profile: dict[str, Any]) -> set[str]:
    terms = set()
    for key in ("audience", "purpose", "domains", "source_mix", "output_mode", "lens_team"):
        terms |= normalize_terms(profile.get(key))
    return terms


def persona_terms(profile: dict[str, Any]) -> set[str]:
    terms = normalize_terms(profile.get("audience"))
    terms |= normalize_terms(profile.get("purpose"))
    terms |= normalize_terms(profile.get("output_mode"))
    return terms


def overlap_score(source_values: list[str] | str | None, profile_terms: set[str]) -> float:
    values = normalize_terms(source_values)
    exact = len(values & profile_terms)
    fuzzy = 0
    for value in values:
        for term in profile_terms:
            if len(value) >= 3 and (value in term or term in value):
                fuzzy += 1
                break
    return exact * 1.0 + fuzzy * 0.4


def source_score(source: dict[str, Any], profile: dict[str, Any], index: int, seed: int) -> float:
    terms = terms_from_profile(profile)
    persona_profile_terms = persona_terms(profile)
    source_personas = normalize_terms(source.get("personas"))
    score = float(source.get("quality", 3)) * 1.2
    score += max(0, 4 - int(source.get("tier", 3))) * 0.7
    score += overlap_score(source.get("domains"), terms) * 1.2
    persona_match = overlap_score(source.get("personas"), terms)
    score += persona_match * 1.25
    score += overlap_score(source.get("geography"), terms) * 0.7
    score += ACCESS_WEIGHT.get(source.get("access", ""), 0)
    if source_personas and persona_profile_terms and persona_match == 0:
        score -= 1.4
    if source.get("source_type") in {"filings", "public_data"} and not (
        {"investor", "analyst", "strategy", "corporate"} & persona_profile_terms
    ):
        score -= 0.9
    # Stable rotation jitter: sources with similar scores change order by day/seed.
    score += ((index + seed) % 7) * 0.03
    return round(score, 3)


def select_sources(
    registry: list[dict[str, Any]],
    profile: dict[str, Any],
    max_sources: int,
    max_per_type: int,
    seed: int,
) -> list[dict[str, Any]]:
    scored = [
        {**source, "selection_score": source_score(source, profile, index, seed)}
        for index, source in enumerate(registry)
    ]
    scored.sort(
        key=lambda source: (
            -source["selection_score"],
            TYPE_DIVERSITY_ORDER.index(source.get("source_type"))
            if source.get("source_type") in TYPE_DIVERSITY_ORDER
            else 99,
            source["id"],
        )
    )

    selected: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}
    for source in scored:
        source_type = source.get("source_type", "unknown")
        if type_counts.get(source_type, 0) >= max_per_type:
            continue
        selected.append(source)
        type_counts[source_type] = type_counts.get(source_type, 0) + 1
        if len(selected) >= max_sources:
            return selected

    for source in scored:
        if source not in selected:
            selected.append(source)
        if len(selected) >= max_sources:
            break
    return selected


def public_source_view(source: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "name",
        "url",
        "feed_url",
        "source_type",
        "access",
        "tier",
        "quality",
        "cadence",
        "domains",
        "personas",
        "geography",
        "selection_score",
        "notes",
    ]
    return {key: source[key] for key in keys if key in source}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rss-output")
    parser.add_argument("--max-sources", type=int, default=12)
    parser.add_argument("--max-per-type", type=int, default=3)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    registry = load_json(args.registry)
    profile = load_json(args.profile)
    seed = args.seed if args.seed is not None else date.today().toordinal()
    selected = select_sources(registry, profile, args.max_sources, args.max_per_type, seed)
    rss_sources = [source for source in selected if source.get("feed_url")]
    watchlist = [source for source in selected if not source.get("feed_url")]

    payload = {
        "profile": profile,
        "seed": seed,
        "selected_sources": [public_source_view(source) for source in selected],
        "rss_sources": [public_source_view(source) for source in rss_sources],
        "watchlist_sources": [public_source_view(source) for source in watchlist],
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.rss_output:
        Path(args.rss_output).write_text(
            json.dumps([public_source_view(source) for source in rss_sources], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(
        f"Selected {len(selected)} sources "
        f"({len(rss_sources)} RSS, {len(watchlist)} watchlist) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
