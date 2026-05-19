#!/usr/bin/env python3
"""Build a Markdown daily signal brief from candidate items."""

from __future__ import annotations

import argparse
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
    "persona_data": "페르소나 데이터",
    "nvidia_ecosystem": "NVIDIA 생태계",
    "sovereign_ai": "소버린 AI",
    "physical_ai": "피지컬 AI",
    "content_ip": "콘텐츠/IP",
    "app_rankings": "앱 순위",
    "social_trends": "소셜 트렌드",
    "physical_world": "현장/오프라인",
    "spatial_reviews": "공간 리뷰",
    "reservation": "예약/대기",
    "retail_offline": "리테일/취향",
    "real_estate": "상권/부동산",
    "foot_traffic": "동선/체류",
    "place": "장소",
    "space": "공간",
    "creator": "크리에이터",
    "apps": "앱",
    "rankings": "순위",
}


def topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, topic)


def topic_text(topics: list[str]) -> str:
    labels = [topic_label(topic) for topic in topics[:3]]
    return ", ".join(labels) if labels else "시장 변화"


def audience_label(value: str) -> str:
    labels = {
        "Korean B2B SaaS founder": "한국 B2B SaaS 창업자",
        "Korean founder-investor": "한국 창업자 겸 투자자",
        "general business reader": "비즈니스 독자",
    }
    return labels.get(value, value)


def purpose_label(value: str) -> str:
    labels = {
        "product strategy and weekly founder newsletter": "제품 전략과 창업자 뉴스레터",
        "market research and content ideation": "시장 리서치와 콘텐츠 기획",
        "market research": "시장 리서치",
    }
    return labels.get(value, value)


def content_angle(item: dict) -> str:
    title = item["title"].rstrip(".")
    return f"`{title}`로 보는 {topic_text(item.get('topics', []))} 변화"


def signal_summary(item: dict) -> str:
    source = item.get("source_name", "출처")
    title = item.get("title", "이 신호")
    topics = topic_text(item.get("topics", []))
    summary = str(item.get("summary", "")).strip()
    if any("\uac00" <= char <= "\ud7a3" for char in summary):
        return summary[:220]
    return (
        f"{source}가 `{title}` 소식을 전했어요. 핵심은 {topics} 관련 변화가 "
        "실제 제품, 고객 접점, 운영 방식으로 이어지고 있다는 점이에요."
    )


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
    audience = audience_label(profile.get("audience", "이 사용자의 업무"))
    if not topics:
        return f"{audience} 관점에서는 아직 방향성을 말하기에 근거가 부족해요. 더 좋은 출처를 먼저 확인해야 해요."
    topics_kr = topic_text(topics)
    if "workflow" in topics or "ai" in topics:
        return (
            f"오늘 신호는 {topics_kr}가 범용 도구에서 실제 업무 단위로 내려오고 있다는 쪽에 가까워요. "
            f"{audience}에게 중요한 질문은 '어떤 모델이 더 좋은가'보다 "
            "'어떤 업무 흐름을 반복 가능하게 만들 수 있는가'예요."
        )
    return (
        f"오늘 신호는 {topics_kr} 쪽으로 모이고 있어요. 바로 결론 내리기보다는, "
        "다음 리서치에서 먼저 확인할 만한 가설로 보는 게 좋아요."
    )


def contrarian_view(top: list[dict]) -> str:
    weaker = [item for item in top if item.get("score", 0) < 4.3]
    if weaker:
        return (
            "아직은 이른 신호일 수 있어요. 일부 항목은 2차 출처나 헤드라인 중심이라, "
            "중요한 판단 전에는 원문 발표나 고객 행동 데이터를 더 확인하세요."
        )
    return (
        "좋은 출처가 같은 이야기를 반복해도 실제 채택과는 다를 수 있어요. "
        "고객 행동, 도입 사례, 후속 투자 흐름으로 확인하세요."
    )


def is_actionable_signal(item: dict) -> bool:
    why = str(item.get("why_it_matters", "")).lower()
    blocked = [
        "needs a stronger primary-source pattern",
        "더 강한 1차 출처",
        "반복 패턴을 확인",
    ]
    return not any(phrase in why for phrase in blocked)


def artifact_label(profile: dict) -> str:
    mode = str(profile.get("output_mode", "")).lower()
    purpose = str(profile.get("purpose", "")).lower()
    audience = str(profile.get("audience", "")).lower()
    if "slack" in mode or "team" in mode or "corporate" in audience:
        return "팀 공유용 Slack 업데이트"
    if "meeting" in mode or "strategy" in purpose:
        return "전략 회의 안건"
    if "sales" in mode or "sales" in audience:
        return "세일즈 대화 포인트"
    if "linkedin" in mode or "content" in purpose or "newsletter" in mode:
        return "뉴스레터/LinkedIn 훅"
    if "investment" in purpose or "investor" in audience:
        return "리서치 메모 질문"
    return "다음 액션"


def render_artifacts(profile: dict, top: list[dict]) -> list[str]:
    label = artifact_label(profile)
    lines = [f"## 바로 쓸 수 있는 결과물: {label}", ""]
    if label == "팀 공유용 Slack 업데이트":
        lines.extend(
            [
                "*오늘의 신호*",
                "",
                f"- 핵심 흐름: {synthesize_pattern(top, profile)}",
                f"- 같이 볼 것: `{top[0]['title']}`가 우리 로드맵에 주는 의미",
                f"- 먼저 읽을 출처: [{top[0]['source_name']}]({top[0]['url']})",
                "- 확인할 질문: 이게 단순한 화제가 아니라는 걸 어떤 고객 행동으로 확인할 수 있을까요?",
                "",
            ]
        )
    elif label == "전략 회의 안건":
        lines.extend(
            [
                "1. 지금 바꿔야 할 시장 가정이 있나요?",
                f"2. `{top[0]['title']}`는 우리 포지셔닝에 어떤 의미가 있나요?",
                "3. 로드맵, 채용, 파트너십을 바꿀 만큼 강한 근거는 무엇인가요?",
                "4. 다음 주에 다시 볼 지표나 출처는 무엇인가요?",
                "",
            ]
        )
    elif label == "세일즈 대화 포인트":
        lines.extend(
            [
                f"- 대화 시작점: `{top[0]['title']}` 같은 변화가 고객 업무에도 영향을 줄 수 있어요.",
                "- 질문: 이 업무는 아직 어디에서 수동으로 처리되고 있나요?",
                "- 근거: 상위 출처 링크를 먼저 공유하고, 영업보다 문제 확인에 초점을 맞추세요.",
                "",
            ]
        )
    elif label == "리서치 메모 질문":
        lines.extend(
            [
                "- 가설: 얇은 AI 기능보다, 특정 업무의 데이터와 유통 경로를 잡는 제품이 더 오래갈 수 있어요.",
                "- 반대 근거: 고객이 실제로 돈을 내고 있나요, 아니면 투자자 내러티브에 가깝나요?",
                "- 다음 근거: 후속 투자, 제품 출시, 고객 사례, 규제 변화를 확인하세요.",
                "",
            ]
        )
    else:
        for index, item in enumerate(top[:3], start=1):
            lines.append(f"{index}. 훅: {content_angle(item)}")
            lines.append(f"   근거: {item['source_name']} 항목, 점수 {item['score']} / 5")
            lines.append("   독자에게 물을 것: 이 변화가 어떤 업무나 시장 가정을 바꾸나요?")
            lines.append("")
    return lines


def render_digest(profile: dict, scored_items: list[dict], max_signals: int) -> str:
    top = select_signals(scored_items, max_signals)
    audience = audience_label(profile.get("audience", "일반 비즈니스 독자"))
    purpose = purpose_label(profile.get("purpose", "시장 리서치"))
    domains = ", ".join(topic_label(domain) for domain in profile.get("domains", []))

    lines: list[str] = [
        "# Daily Signal Brief",
        "",
        f"- 날짜: {date.today().isoformat()}",
        f"- 대상: {audience}",
        f"- 목적: {purpose}",
        f"- 관심 영역: {domains}",
        "",
        "## 오늘 이것만은 꼭",
        "",
        synthesize_pattern(top, profile),
        "",
        "## 흐름 읽기",
        "",
        f"- 방향성: {synthesize_pattern(top, profile)}",
        f"- 반대로 볼 점: {contrarian_view(top)}",
        "- 다음에 확인할 근거: 원문 발표, 고객 행동, 투자 데이터, 한국 시장 도입 사례",
        "",
        "## 오늘의 상위 신호",
        "",
    ]

    for index, item in enumerate(top, start=1):
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- 출처: [{item['source_name']}]({item['url']})",
                f"- 점수: {item['score']} / 5",
                f"- 신호 지속성: {item['score_dimensions'].get('signal_durability', 'n/a')} / 5",
                f"- 무슨 일이 있었나요: {signal_summary(item)}",
                f"- 왜 중요한가요: {item.get('why_it_matters', '아직 판단하려면 근거가 더 필요해요.')}",
                f"- 누가 봐야 하나요: {audience}",
                "- 다음에 볼 것: 원문 발표, 고객 행동, 후속 투자, 실제 제품 출시가 반복되는지 확인하세요.",
                f"- 콘텐츠 각도: {content_angle(item)}",
                "",
            ]
        )

    lines.extend(
        [
            "## 바로 쓸 수 있는 글감",
            "",
        ]
    )
    for index, item in enumerate(top[:3], start=1):
        lines.append(f"{index}. 훅: {content_angle(item)}")
        lines.append(f"   근거: {item['source_name']} 항목, 점수 {item['score']} / 5")
        lines.append("   독자에게 물을 것: 이 변화가 어떤 업무나 시장 가정을 바꾸나요?")
        lines.append("")

    lines.extend(render_artifacts(profile, top))

    lines.extend(
        [
            "## 다음에 볼 것",
            "",
            "- 같은 흐름이 1차 출처에서도 반복되는지 확인하세요.",
            "- 한국 시장에서는 규제, 유통, 결제, 신뢰, 기업 구매 방식을 같이 보세요.",
            "- 가장 강한 신호 하나를 긴 글 1개와 짧은 글 2개로 바꿔보세요.",
            "",
            "## 주의사항",
            "",
            "- 이 브리프는 공개 RSS와 공개 출처 메타데이터를 바탕으로 만든 리서치 초안이에요.",
            "- 투자 판단이 아니라 리서치와 콘텐츠 기획을 돕기 위한 자료예요.",
            "- 유료 또는 로그인 기반 원문을 그대로 복사하지 마세요.",
            "",
        ]
    )

    return "\n".join(lines)


def select_signals(scored_items: list[dict], max_signals: int, max_per_source: int = 2) -> list[dict]:
    selected: list[dict] = []
    per_source: dict[str, int] = {}

    for item in [row for row in scored_items if is_actionable_signal(row)]:
        source = item.get("source_id", "unknown")
        if per_source.get(source, 0) >= max_per_source:
            continue
        if item.get("topics") == ["general"] and len(scored_items) > max_signals:
            continue
        selected.append(item)
        per_source[source] = per_source.get(source, 0) + 1
        if len(selected) >= max_signals:
            return selected

    for item in scored_items:
        if item in selected:
            continue
        source = item.get("source_id", "unknown")
        if per_source.get(source, 0) >= max_per_source:
            continue
        selected.append(item)
        per_source[source] = per_source.get(source, 0) + 1
        if len(selected) >= max_signals:
            return selected

    return selected


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
        source_list(load_json(args.sources)),
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
