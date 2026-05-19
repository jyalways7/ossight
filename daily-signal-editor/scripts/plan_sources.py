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
    "public_data",
    "public_report",
    "media",
    "community",
    "social_signal",
    "app_rankings",
    "youtube",
    "map_review",
    "reservation",
    "commerce",
    "real_estate",
]

CATEGORY_DIVERSITY_ORDER = [
    "business",
    "consumer",
    "persona_data",
    "nvidia_ecosystem",
    "sovereign_ai",
    "physical_ai",
    "physical_world",
    "spatial_reviews",
    "reservation",
    "retail_offline",
    "real_estate",
    "content_ip",
    "social_trends",
    "app_rankings",
    "investing",
    "korea",
    "ai",
]


def terms_from_profile(profile: dict[str, Any]) -> set[str]:
    terms = set()
    for key in ("audience", "purpose", "domains", "source_mix", "output_mode", "lens_team"):
        terms |= normalize_terms(profile.get(key))
    terms |= normalize_terms(list((profile.get("source_category_mix") or {}).keys()))
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


def source_category(source: dict[str, Any]) -> str:
    if source.get("source_category"):
        return str(source["source_category"])
    domains = normalize_terms(source.get("domains"))
    source_type = source.get("source_type")
    if source_type == "app_rankings":
        return "app_rankings"
    if source_type == "map_review":
        return "spatial_reviews"
    if source_type == "reservation":
        return "reservation"
    if source_type == "real_estate":
        return "real_estate"
    if source_type == "commerce":
        return "retail_offline"
    if source_type == "persona_data":
        return "persona_data"
    if source_type == "ecosystem_data":
        return "nvidia_ecosystem"
    if {"persona", "personas", "synthetic-persona", "demographic", "페르소나"} & domains:
        return "persona_data"
    if {"nvidia", "nemotron", "cuda", "dgx", "inception", "gpu"} & domains:
        return "nvidia_ecosystem"
    if {"sovereign-ai", "sovereign_ai", "k-ai", "foundation-model", "소버린"} & domains:
        return "sovereign_ai"
    if {"physical-ai", "physical_ai", "robotics", "digital-twin", "omniverse", "factory"} & domains:
        return "physical_ai"
    if source_type in {"social_signal", "community"}:
        return "social_trends"
    if {"offline", "space", "place", "physical", "popup", "store", "foot_traffic", "waiting"} & domains:
        return "physical_world"
    if {"real-estate", "commercial-real-estate", "lease", "rent", "vacancy", "상권", "임대"} & domains:
        return "real_estate"
    if {"reservation", "waiting", "queue", "예약", "대기"} & domains:
        return "reservation"
    if "content_ip" in domains or "creator" in domains or "youtube" in domains:
        return "content_ip"
    if "consumer" in domains or "retail" in domains or "commerce" in domains:
        return "consumer"
    if "wealth" in domains or "finance" in domains or "macro" in domains or "public-markets" in domains:
        return "investing"
    if "korea" in domains:
        return "korea"
    if "ai" in domains:
        return "ai"
    return "business"


def category_quota(profile: dict[str, Any], max_sources: int) -> dict[str, int]:
    raw = profile.get("source_category_mix") or {}
    quotas: dict[str, int] = {}
    for category, value in raw.items():
        if isinstance(value, float) and value <= 1:
            quotas[category] = max(1, round(max_sources * value))
        else:
            quotas[category] = max(1, int(value))
    return quotas


def source_score(source: dict[str, Any], profile: dict[str, Any], index: int, seed: int) -> float:
    terms = terms_from_profile(profile)
    persona_profile_terms = persona_terms(profile)
    source_personas = normalize_terms(source.get("personas"))
    score = float(source.get("quality", 3)) * 1.2
    score += max(0, 4 - int(source.get("tier", 3))) * 0.7
    score += overlap_score(source.get("domains"), terms) * 1.2
    score += overlap_score(source_category(source), terms) * 0.9
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
    category_counts: dict[str, int] = {}

    def can_add(source: dict[str, Any]) -> bool:
        source_type = source.get("source_type", "unknown")
        return type_counts.get(source_type, 0) < max_per_type and source not in selected

    def add_source(source: dict[str, Any]) -> None:
        source_type = source.get("source_type", "unknown")
        category = source_category(source)
        selected.append(source)
        type_counts[source_type] = type_counts.get(source_type, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    quotas = category_quota(profile, max_sources)
    for category in CATEGORY_DIVERSITY_ORDER:
        quota = quotas.get(category, 0)
        if quota <= 0:
            continue
        for source in scored:
            if len(selected) >= max_sources or category_counts.get(category, 0) >= quota:
                break
            if source_category(source) == category and can_add(source):
                add_source(source)

    for source in scored:
        if not can_add(source):
            continue
        add_source(source)
        if len(selected) >= max_sources:
            return selected

    for source in scored:
        if source not in selected:
            add_source(source)
        if len(selected) >= max_sources:
            break
    return selected


def public_source_view(source: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "name",
        "url",
        "feed_url",
        "api_url",
        "source_type",
        "source_category",
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
    parser.add_argument("--app-output")
    parser.add_argument("--manual-output")
    parser.add_argument("--max-sources", type=int, default=12)
    parser.add_argument("--max-per-type", type=int, default=3)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    registry = load_json(args.registry)
    profile = load_json(args.profile)
    seed = args.seed if args.seed is not None else date.today().toordinal()
    selected = select_sources(registry, profile, args.max_sources, args.max_per_type, seed)
    rss_sources = [source for source in selected if source.get("feed_url")]
    app_sources = [source for source in selected if source.get("api_url")]
    manual_sources = [
        source
        for source in selected
        if (
            source.get("source_type") in {"social_signal", "youtube", "app_rankings", "map_review", "reservation", "commerce", "real_estate"}
            or source_category(source)
            in {"social_trends", "app_rankings", "physical_world", "spatial_reviews", "reservation", "retail_offline", "real_estate"}
        )
        and not source.get("feed_url")
        and not source.get("api_url")
    ]
    watchlist = [source for source in selected if not source.get("feed_url")]

    payload = {
        "profile": profile,
        "seed": seed,
        "selected_sources": [public_source_view(source) for source in selected],
        "rss_sources": [public_source_view(source) for source in rss_sources],
        "app_ranking_sources": [public_source_view(source) for source in app_sources],
        "manual_signal_sources": [public_source_view(source) for source in manual_sources],
        "watchlist_sources": [public_source_view(source) for source in watchlist],
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.rss_output:
        Path(args.rss_output).write_text(
            json.dumps([public_source_view(source) for source in rss_sources], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.app_output:
        Path(args.app_output).write_text(
            json.dumps([public_source_view(source) for source in app_sources], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.manual_output:
        Path(args.manual_output).write_text(
            json.dumps([public_source_view(source) for source in manual_sources], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(
        f"Selected {len(selected)} sources "
        f"({len(rss_sources)} RSS, {len(app_sources)} app ranking, {len(manual_sources)} manual, {len(watchlist)} watchlist) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
