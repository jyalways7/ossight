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


def infer_app_context(name: str, source: dict[str, Any]) -> tuple[str, str]:
    lowered = name.lower()
    is_paid = "paid" in source.get("id", "") or "paid" in source.get("api_url", "")

    if any(term in lowered for term in ["gemini", "claude", "chatgpt", "ai"]):
        return (
            "AI 보조 앱",
            "AI 앱이 상위권에 있다는 건 사용자가 검색이나 브라우저보다 대화형 도구를 더 자주 여는 습관을 만들고 있다는 신호예요. 이제 경쟁은 모델 성능만이 아니라 첫 화면, 저장된 맥락, 모바일 사용 빈도에서 갈려요.",
        )
    if any(term in lowered for term in ["카페", "order", "오더", "reservation", "예약", "queue", "대기"]):
        return (
            "로컬 경험/예약",
            "카페 주문이나 예약 앱이 올라오는 건 사람들이 좋은 장소를 찾는 것만큼 기다리지 않는 경험을 원한다는 뜻이에요. 로컬 비즈니스에서는 결제 전 대기 시간, 재방문 루틴, 픽업 동선이 제품 기회가 돼요.",
        )
    if any(term in lowered for term in ["planner", "schedule", "calendar", "grid", "위젯", "스케줄", "플래너", "daygrid"]):
        return (
            "개인 생산성/일정",
            "일정 앱이 유료 상위권에 있다는 건 사용자가 범용 캘린더보다 더 작고 시각적인 루틴 관리에 돈을 낸다는 신호예요. 특히 위젯과 한눈에 보는 화면은 매일 열어야 하는 앱의 방어력이 될 수 있어요.",
        )
    if any(term in lowered for term in ["film", "camera", "analog", "필터", "카메라", "photo", "사진", "berryfilm", "gika"]):
        return (
            "카메라/필터",
            "카메라와 필터 앱이 유료 순위에 반복해서 보이면 소비자가 생성형 AI보다 '내 취향처럼 보이는 결과물'에 바로 지갑을 연다는 뜻이에요. 콘텐츠 도구는 기능 수보다 감성 프리셋, 공유 장면, 팬층이 더 중요해질 수 있어요.",
        )
    if any(term in lowered for term in ["story", "스토리", "꾸미", "template", "템플릿", "chakk"]):
        return (
            "소셜 콘텐츠 제작",
            "스토리 꾸미기 앱이 올라온다는 건 사람들의 제작 니즈가 전문 편집보다 빠른 표현과 공유용 템플릿에 가깝다는 신호예요. 크리에이터 툴은 무거운 편집기보다 반복 가능한 포맷을 빨리 제공할 때 퍼질 수 있어요.",
        )
    if any(term in lowered for term in ["drama", "short", "숏폼", "vigloo", "webtoon", "웹툰", "game", "게임"]):
        return (
            "숏폼/콘텐츠 소비",
            "숏폼 콘텐츠 앱이 상위권에 있으면 사용자의 여가 시간이 긴 영상보다 짧고 연속적인 서사로 쪼개지고 있다는 신호예요. IP 사업자는 작품 자체보다 회차 구조, 클립 확산, 결제 전환을 같이 봐야 해요.",
        )
    if any(term in lowered for term in ["anki", "flashcard", "능력", "시험", "study", "공부", "학습", "한국사"]):
        return (
            "학습/시험 준비",
            "학습 앱이 유료 순위에 남아 있다는 건 시험이나 자격증처럼 결과가 분명한 문제에는 여전히 결제 의향이 강하다는 뜻이에요. 교육 앱은 넓은 강의보다 반복 학습, 진도 추적, 합격까지의 압축 루틴이 더 설득력 있어요.",
        )
    if any(term in lowered for term in ["adblock", "광고차단", "vpn", "privacy", "보안", "유니콘"]):
        return (
            "프라이버시/차단",
            "광고 차단이나 프라이버시 앱이 유료권에 있다는 건 사용자가 편의보다 방해받지 않는 사용 경험에 값을 치른다는 신호예요. 브라우징, 콘텐츠, 커머스 제품은 광고 밀도와 신뢰 비용을 더 민감하게 봐야 해요.",
        )

    if is_paid:
        return (
            "유료 니치 앱",
            "유료 순위에 오른 앱은 무료 대체재가 있어도 사용자가 특정 문제 해결에 바로 돈을 냈다는 뜻이에요. 앱 이름이 말하는 한 가지 약속, 결제 전 신뢰 장치, 반복 사용 맥락을 같이 보면 제품 아이디어가 더 선명해져요.",
        )
    return (
        "무료 소비자 앱",
        "무료 상위권 앱은 사용자가 지금 당장 시험해볼 만큼 진입 장벽이 낮다는 신호예요. 다만 설치는 관심이고 유지가 검증이므로, 다음에는 리뷰와 재방문 이유를 함께 봐야 해요.",
    )


def apple_feed_items(source: dict[str, Any], payload: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    feed = payload.get("feed", {})
    results = feed.get("results", [])[:limit]
    items: list[dict[str, Any]] = []
    for index, app in enumerate(results, start=1):
        name = app.get("name") or f"App rank {index}"
        artist = app.get("artistName", "확인 필요")
        genres = [genre.get("name", "") for genre in app.get("genres", []) if genre.get("name")]
        inferred_category, why = infer_app_context(name, source)
        genre_text = ", ".join(genres[:3]) or inferred_category
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
                "summary": f"{name} 앱이 {source['name']}에서 {index}위에 올랐어요. 퍼블리셔는 {artist}, 추정 카테고리는 {genre_text}예요.",
                "topics": topics,
                "freshness": 5,
                "business_impact": 4 if index <= 3 else 3,
                "novelty": 4 if index <= 5 else 3,
                "content_potential": 4 if index <= 5 else 3,
                "why_it_matters": why,
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
