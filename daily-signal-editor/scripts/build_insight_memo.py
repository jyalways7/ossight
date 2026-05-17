#!/usr/bin/env python3
"""Build an insight memo from curated daily signal candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from score_items import item_list, load_json, score_items, source_list


TOPIC_LABELS = {
    "ai": "AI",
    "business": "비즈니스",
    "consumer": "소비자 관심",
    "content_ip": "콘텐츠/IP",
    "app_rankings": "앱 순위",
    "social_trends": "소셜 트렌드",
    "startups": "스타트업",
    "vc": "투자",
    "korea": "한국 시장",
    "workflow": "업무 흐름",
    "creator": "크리에이터",
    "product": "제품",
}


def topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, topic)


def primary_topic(item: dict) -> str:
    topics = item.get("topics") or ["business"]
    return str(topics[0] or "business")


def topic_text(topics: list[str]) -> str:
    return ", ".join(topic_label(topic) for topic in topics[:4])


def signal_summary(item: dict) -> str:
    summary = str(item.get("summary", "")).strip()
    if any("\uac00" <= char <= "\ud7a3" for char in summary):
        return summary[:220]
    source = item.get("source_name", "출처")
    title = item.get("title", "이 신호")
    topics = topic_text(item.get("topics", []))
    return f"{source}가 `{title}`를 전했어요. 핵심은 {topics} 관련 변화가 실제 행동으로 이어지는지 보는 거예요."


def select_signals(scored: list[dict], limit: int, max_per_source: int = 3) -> list[dict]:
    selected: list[dict] = []
    per_source: Counter[str] = Counter()
    per_topic: Counter[str] = Counter()

    for item in scored:
        if item.get("topics") == ["general"]:
            continue
        source = str(item.get("source_id", "unknown"))
        topic = primary_topic(item)
        if per_source[source] >= max_per_source:
            continue
        if per_topic[topic] >= 4:
            continue
        selected.append(item)
        per_source[source] += 1
        per_topic[topic] += 1
        if len(selected) >= limit:
            return selected

    for item in scored:
        if item in selected:
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def group_by_topic(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(primary_topic(item), []).append(item)
    return grouped


def strongest_title(items: list[dict], topic: str) -> str:
    for item in items:
        if topic in (item.get("topics") or []):
            return item["title"]
    return items[0]["title"] if items else "오늘의 신호"


def derive_insights(items: list[dict]) -> list[tuple[str, str, str, str]]:
    topics = {topic for item in items for topic in item.get("topics", [])}
    insights: list[tuple[str, str, str, str]] = []

    if {"content_ip", "social_trends", "creator"} & topics:
        insights.append(
            (
                "포맷이 IP가 되고 있어요",
                "콘텐츠의 힘이 작품 하나가 아니라 반복 가능한 포맷, 팬 편집, 챌린지 구조에서 나오고 있어요.",
                "브랜드와 스타트업은 캠페인을 한 번의 노출로 끝내기보다, 사람들이 다시 만들 수 있는 형식을 설계해야 해요.",
                strongest_title(items, "content_ip"),
            )
        )
    if {"app_rankings", "consumer"} & topics:
        insights.append(
            (
                "소비자는 거대한 플랫폼보다 작은 해결책에 반응해요",
                "앱 순위와 소비자 신호는 사람들이 당장 불편한 한 가지 일을 해결해주는 제품에 빠르게 움직인다는 점을 보여줘요.",
                "제품 아이디어를 찾을 때는 큰 카테고리보다 '오늘 바로 설치할 이유'가 있는 작은 일을 먼저 보세요.",
                strongest_title(items, "app_rankings"),
            )
        )
    if {"ai", "workflow", "business", "startups"} & topics:
        insights.append(
            (
                "AI는 기능이 아니라 업무 루틴으로 내려오고 있어요",
                "AI 관련 신호는 모델 성능 경쟁만이 아니라 개발, 콘텐츠, 리서치, 운영 업무에 붙는 흐름으로 읽혀요.",
                "좋은 글감은 'AI가 대단하다'가 아니라 '어떤 업무가 더 짧고 반복 가능해졌나'에서 나와요.",
                strongest_title(items, "ai"),
            )
        )
    if {"korea", "vc", "business"} & topics:
        insights.append(
            (
                "한국 시장에서는 유통과 신뢰가 신호의 강도를 바꿔요",
                "글로벌 트렌드가 바로 한국 기회가 되지는 않아요. 결제, 규제, 커뮤니티, 기업 구매 방식이 채택 속도를 정해요.",
                "해외 신호를 가져올 때는 한국에서 누가 먼저 돈을 내고 반복 사용할지까지 붙여야 설득력이 생겨요.",
                strongest_title(items, "korea"),
            )
        )

    if not insights:
        insights.append(
            (
                "아직은 관찰 단계예요",
                "오늘의 신호만으로 강한 결론을 내리기에는 근거가 부족해요.",
                "같은 방향의 출처가 2-3개 더 쌓이는지 먼저 보세요.",
                items[0]["title"] if items else "추가 소스 필요",
            )
        )
    return insights[:4]


def render_memo(profile: dict, scored: list[dict], max_signals: int) -> str:
    selected = select_signals(scored, max_signals)
    grouped = group_by_topic(selected)
    topic_counts = Counter(topic for item in selected for topic in item.get("topics", []))
    dominant = [topic for topic, _count in topic_counts.most_common(4)]
    insights = derive_insights(selected)

    lines = [
        "# Daily Insight Memo",
        "",
        f"- 날짜: {date.today().isoformat()}",
        f"- 채널: {profile.get('channel_name', 'Market Signal Channel')}",
        f"- 대상: {profile.get('audience', '비즈니스 독자')}",
        f"- 목적: {profile.get('purpose', '시장 리서치와 콘텐츠 기획')}",
        "- 편집 원칙: 특정 뉴스레터 문체를 복제하지 않고, 밀도 높은 시장 해석, 실전 질문, 반대 근거를 가져옵니다.",
        "",
        "## 오늘의 한 줄",
        "",
        f"오늘 신호는 {topic_text(dominant)} 쪽으로 모여요. 핵심은 화제성보다 반복 행동, 지불 의향, 콘텐츠화 가능성을 같이 보는 거예요.",
        "",
        "## 신호 지도",
        "",
    ]

    for topic, items in sorted(grouped.items(), key=lambda row: (-len(row[1]), topic_label(row[0]))):
        top = items[0]
        lines.extend(
            [
                f"### {topic_label(topic)}",
                f"- 대표 신호: [{top['title']}]({top.get('url', '')})",
                f"- 출처: {top.get('source_name', top.get('source_id', 'unknown'))} / 점수 {top.get('score', 'n/a')} / 5",
                f"- 해석: {signal_summary(top)}",
                f"- 왜 중요한가요: {top.get('why_it_matters', '추가 확인이 필요해요.')}",
                "",
            ]
        )

    lines.extend(["## 인사이트", ""])
    for index, (title, observation, implication, evidence_title) in enumerate(insights, start=1):
        lines.extend(
            [
                f"### {index}. {title}",
                f"- 관찰: {observation}",
                f"- 의미: {implication}",
                f"- 근거 신호: `{evidence_title}`",
                "- 다음 확인: 같은 흐름이 다른 출처, 고객 행동, 실제 제품 출시에서도 반복되는지 보세요.",
                "",
            ]
        )

    lines.extend(["## 바로 쓸 수 있는 콘텐츠 앵글", ""])
    for index, item in enumerate(selected[:5], start=1):
        topics = topic_text(item.get("topics", []))
        lines.extend(
            [
                f"{index}. `{item['title']}`로 보는 {topics} 변화",
                f"   - 독자 질문: 이 신호가 내 일, 제품, 투자 가정을 어떻게 바꾸나요?",
                f"   - 근거: [{item.get('source_name', item.get('source_id', 'unknown'))}]({item.get('url', '')})",
                "",
            ]
        )

    lines.extend(
        [
            "## 반대로 볼 점",
            "",
            "- 소셜/앱 순위 신호는 빠르게 식을 수 있어요. 관심의 속도와 지속 사용을 구분해야 해요.",
            "- RSS와 미디어 신호는 공급자 관점일 수 있어요. 실제 고객 행동이나 매출 근거가 붙어야 강해져요.",
            "- 투자 판단이 아니라 리서치와 콘텐츠 기획을 위한 초안이에요.",
            "",
            "## 내일 다시 볼 질문",
            "",
            "1. 오늘 강했던 신호가 다른 출처에서도 반복되나요?",
            "2. 이 흐름을 가장 먼저 돈으로 바꿀 수 있는 사람은 누구인가요?",
            "3. 지금 글로 쓰면 독자가 바로 저장하거나 공유할 이유가 있나요?",
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
    parser.add_argument("--max-signals", type=int, default=14)
    args = parser.parse_args()

    profile = load_json(args.profile)
    scored = score_items(
        item_list(load_json(args.items)),
        source_list(load_json(args.sources)),
        profile,
    )
    output = render_memo(profile, scored, args.max_signals)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
