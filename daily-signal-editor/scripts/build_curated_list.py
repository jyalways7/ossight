#!/usr/bin/env python3
"""Build a ranked Markdown queue of curated candidate items."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from score_items import item_list, load_json, score_items, source_list


TOPIC_LABELS = {
    "ai": "AI",
    "business": "비즈니스",
    "developer": "개발자 워크플로",
    "workflow": "업무 흐름",
    "startups": "스타트업",
    "vc": "투자",
    "security": "보안",
    "legal": "규제",
    "korea": "한국 시장",
    "consumer": "소비자 관심",
    "content_ip": "콘텐츠/IP",
    "app_rankings": "앱 순위",
    "social_trends": "소셜 트렌드",
    "creator": "크리에이터",
    "apps": "앱",
    "rankings": "순위",
}


BLOCKED_CONTENT_TERMS = [
    "porn",
    "smutty",
    "sexual",
    "bedroom",
]


def topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, topic)


def audience_label(value: str) -> str:
    labels = {
        "Korean B2B SaaS founder": "한국 B2B SaaS 창업자",
        "Korean founder-investor": "한국 창업자 겸 투자자",
        "general reader": "일반 독자",
    }
    return labels.get(value, value)


def purpose_label(value: str) -> str:
    labels = {
        "product strategy and weekly founder newsletter": "제품 전략과 창업자 뉴스레터",
        "market research and content ideation": "시장 리서치와 콘텐츠 기획",
        "daily research": "데일리 리서치",
    }
    return labels.get(value, value)


def signal_summary(item: dict) -> str:
    source = item.get("source_name", "출처")
    title = item.get("title", "이 신호")
    topics = format_topics(item)
    summary = str(item.get("summary", "")).strip()
    if any("\uac00" <= char <= "\ud7a3" for char in summary):
        return summary[:220]
    return (
        f"{source}가 `{title}` 소식을 전했어요. 핵심은 {topics} 관련 변화가 "
        "실제 제품, 고객 접점, 운영 방식으로 이어지고 있다는 점이에요."
    )


def is_allowed_item(item: dict) -> bool:
    if item.get("topics") == ["general"]:
        return False
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary")).lower()
    return not any(term in text for term in BLOCKED_CONTENT_TERMS)


def primary_topic(item: dict) -> str:
    topics = item.get("topics") or ["unknown"]
    return str(topics[0] or "unknown")


def render_kind_groups(queue: list[dict]) -> list[str]:
    grouped: dict[str, list[dict]] = {}
    for item in queue:
        grouped.setdefault(primary_topic(item), []).append(item)

    lines = ["", "## 신호 종류별 큐레이션", ""]
    for topic, items in sorted(grouped.items(), key=lambda row: (-len(row[1]), topic_label(row[0]))):
        lines.append(f"### {topic_label(topic)}")
        for item in items[:5]:
            lines.append(
                f"- [{item['title']}]({item.get('url', '')}) "
                f"({item.get('source_name', item.get('source_id', 'unknown'))}, {item.get('score', 'n/a')} / 5)"
            )
        if len(items) > 5:
            lines.append(f"- 외 {len(items) - 5}개")
        lines.append("")
    return lines


def select_queue(
    scored_items: list[dict],
    limit: int,
    max_per_source: int,
    max_per_primary_topic: int,
    min_score: float,
    min_audience_fit: float,
) -> list[dict]:
    selected: list[dict] = []
    per_source: Counter[str] = Counter()
    per_topic: Counter[str] = Counter()

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
        topic = primary_topic(item)
        if per_topic[topic] >= max_per_primary_topic:
            continue
        selected.append(item)
        per_source[source] += 1
        per_topic[topic] += 1
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
        source = item.get("source_id", "unknown")
        if per_source[source] >= max_per_source:
            continue
        selected.append(item)
        per_source[source] += 1
        if len(selected) >= limit:
            break
    return selected


def tier_label(score: float) -> str:
    if score >= 4.2:
        return "A. 오늘 바로 볼 신호"
    if score >= 3.6:
        return "B. 글감으로 좋은 후보"
    return "C. 더 확인할 후보"


def format_topics(item: dict) -> str:
    topics = item.get("topics") or []
    return ", ".join(topic_label(topic) for topic in topics[:5]) if topics else "일반"


def render_queue(profile: dict, queue: list[dict], scored_count: int) -> str:
    audience = audience_label(profile.get("audience", "general reader"))
    purpose = purpose_label(profile.get("purpose", "daily research"))
    source_counts = Counter(item.get("source_name", item.get("source_id", "unknown")) for item in queue)

    lines = [
        "# Daily Curated Content Queue",
        "",
        f"- 날짜: {date.today().isoformat()}",
        f"- 대상: {audience}",
        f"- 목적: {purpose}",
        f"- 큐레이션 항목: {len(queue)} / {scored_count}",
        "",
        "## 소스 구성",
        "",
    ]
    for source, count in source_counts.most_common():
        lines.append(f"- {source}: {count}")

    lines.extend(render_kind_groups(queue))

    lines.extend(["", "## 우선순위 큐", ""])
    current_tier = ""
    for index, item in enumerate(queue, start=1):
        tier = tier_label(float(item.get("score", 0)))
        if tier != current_tier:
            current_tier = tier
            lines.extend([f"### {current_tier}", ""])
        lines.extend(
            [
                f"#### {index}. {item['title']}",
                f"- 출처: [{item.get('source_name', item.get('source_id', 'unknown'))}]({item.get('url', '')})",
                f"- 발행일: {item.get('published', 'unknown')}",
                f"- 점수: {item.get('score', 'n/a')} / 5",
                f"- 주제: {format_topics(item)}",
                f"- 정리: {signal_summary(item)}",
                f"- 왜 중요한가요: {item.get('why_it_matters', '아직 판단하려면 근거가 더 필요해요.')}",
                "",
            ]
        )

    lines.extend(
        [
            "## 이렇게 쓰세요",
            "",
            "- A-tier는 오늘 브리프와 전략 해석에 바로 쓰세요.",
            "- B-tier는 콘텐츠 아이디어, 회의 준비, 추가 리서치 후보로 두세요.",
            "- C-tier는 더 강한 1차 출처가 나오기 전까지 약한 신호로 보세요.",
            "- 출처, 대상 적합도, 다음 행동이 모두 분명할 때만 최종 브리프로 올리세요.",
            "",
            "## 주의사항",
            "",
            "- 이 큐는 출처 기반 리서치 초안이에요. 투자 조언이 아니에요.",
            "- 공개 RSS 요약은 불완전할 수 있어요. 중요한 내용은 원문에서 다시 확인하세요.",
            "- 유료 또는 로그인 기반 원문을 그대로 복사하지 마세요.",
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
    parser.add_argument("--max-per-primary-topic", type=int, default=14)
    parser.add_argument("--min-score", type=float, default=2.8)
    parser.add_argument("--min-audience-fit", type=float, default=2.0)
    args = parser.parse_args()

    profile = load_json(args.profile)
    scored = score_items(
        item_list(load_json(args.items)),
        source_list(load_json(args.sources)),
        profile,
    )
    queue = select_queue(
        scored,
        args.limit,
        args.max_per_source,
        args.max_per_primary_topic,
        args.min_score,
        args.min_audience_fit,
    )
    output = render_queue(profile, queue, len(scored))
    Path(args.output).write_text(output, encoding="utf-8")
    print(f"Wrote {len(queue)} curated items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
