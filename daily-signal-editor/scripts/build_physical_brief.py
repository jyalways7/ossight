#!/usr/bin/env python3
"""Build a physical-world signal brief from candidate items."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from score_items import item_list, load_json, score_items, source_list


PHYSICAL_TOPICS = {
    "physical_world",
    "spatial_reviews",
    "reservation",
    "retail_offline",
    "real_estate",
    "foot_traffic",
    "place",
    "space",
    "persona_data",
    "nvidia_ecosystem",
    "sovereign_ai",
    "physical_ai",
}


EVIDENCE_TERMS = {
    "movement": ["route", "mobility", "foot", "traffic", "동선", "이동", "유동"],
    "dwell": ["dwell", "stay", "seat", "table", "체류", "좌석", "머무"],
    "queue": ["queue", "waiting", "waitlist", "reservation", "대기", "웨이팅", "예약", "줄"],
    "payment": ["paid", "price", "spend", "purchase", "결제", "가격", "구매", "돈"],
    "photo": ["photo", "geotag", "camera", "instagram", "사진", "포토", "찍"],
    "object": ["object", "home", "living", "retail", "brand", "goods", "물건", "소품", "굿즈", "리테일"],
    "route": ["course", "nearby", "neighborhood", "route", "코스", "근처", "동네"],
    "copy": ["copy", "replicate", "format", "popup", "pop-up", "복제", "포맷", "팝업"],
    "video_route": ["youtube", "vlog", "shorts", "walkthrough", "day in", "브이로그", "쇼츠", "코스 영상", "방문기"],
    "persona": ["persona", "personas", "demographic", "census", "segment", "페르소나", "인구통계", "세그먼트"],
    "infrastructure": ["nvidia", "gpu", "dgx", "blackwell", "ai factory", "sovereign", "인프라", "소버린", "팩토리"],
}


def profile_label(profile: dict, key: str, default: str) -> str:
    return str(profile.get(key) or default)


def evidence_labels(item: dict) -> str:
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "why_it_matters")).lower()
    labels = [
        label
        for label, terms in EVIDENCE_TERMS.items()
        if any(term.lower() in text for term in terms)
    ]
    if not labels:
        topics = set(item.get("topics") or [])
        if "reservation" in topics:
            labels.append("queue")
        if "spatial_reviews" in topics:
            labels.extend(["photo", "dwell"])
        if "real_estate" in topics:
            labels.extend(["movement", "copy"])
        if "retail_offline" in topics:
            labels.extend(["object", "payment"])
    deduped = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return " / ".join(deduped[:4]) if deduped else "scene"


def hidden_desire(item: dict) -> str:
    topics = set(item.get("topics") or [])
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    if str(item.get("source_id", "")).startswith("youtube-"):
        return "사람들은 장소 하나보다 실패하지 않는 하루의 순서와, 도착했을 때 찍을 장면을 미리 확인하고 싶어 해요."
    if "persona_data" in topics:
        return "관찰된 장면을 평균적인 소비자 취향이 아니라, 한국의 연령·지역·직업·생활 맥락별 욕망으로 해석하고 싶어 해요."
    if "nvidia_ecosystem" in topics or "sovereign_ai" in topics or "physical_ai" in topics:
        return "한국의 AI 수요가 추상적 관심이 아니라 개발자, 스타트업, 대기업, 제조 현장의 실제 실행 역량으로 연결되길 원해요."
    if "reservation" in topics or "waiting" in text:
        return "사람들은 좋은 선택을 놓치지 않았다는 확신과, 시간을 들일 만한 장소라는 사회적 증거를 원해요."
    if "spatial_reviews" in topics or "photo" in evidence_labels(item):
        return "사람들은 경험 자체만이 아니라, 자기 취향을 설명해 주는 장면을 원해요."
    if "real_estate" in topics:
        return "브랜드와 운영자는 관심이 매출과 반복 방문으로 바뀔 수 있는 동네를 찾고 있어요."
    if "retail_offline" in topics:
        return "취향이 말이 아니라 물건, 진열, 방, 옷차림으로 확인되길 원해요."
    return "온라인에서 말하던 취향이 실제 이동, 체류, 구매, 촬영으로 굳어지는 중일 수 있어요."


def business_translation(item: dict) -> str:
    topics = set(item.get("topics") or [])
    if str(item.get("source_id", "")).startswith("youtube-"):
        return "브이로그와 쇼츠의 방문 순서를 지도 코스, 예약 패키지, 팝업 동선, 로컬 콘텐츠 상품으로 번역할 수 있어요."
    if "persona_data" in topics:
        return "현장 신호별로 3-5개 한국 페르소나를 붙여 제품 메시지, 공간 동선, 가격, 콘텐츠 훅을 시뮬레이션하세요."
    if "nvidia_ecosystem" in topics or "sovereign_ai" in topics:
        return "소버린 AI와 한국 개발자 생태계 데이터를 결합해 B2B/B2G/스타트업별 채택 경로를 분리하세요."
    if "physical_ai" in topics:
        return "공간·제조·모빌리티 현장 신호를 디지털 트윈, 로봇, 시뮬레이션, 에이전트 운영 기회로 번역하세요."
    if "reservation" in topics:
        return "예약/대기 데이터를 상품 기획, 지역별 출점, 멤버십, 방문 전 콘텐츠로 바꿀 수 있어요."
    if "spatial_reviews" in topics:
        return "리뷰 언어와 사진 구도를 공간 설계, 메뉴 배치, 입면, 굿즈, 방문 코스로 번역하세요."
    if "real_estate" in topics:
        return "팝업용 attention 상권과 장기 운영용 repeat 상권을 분리해 입지 전략을 짜야 해요."
    if "retail_offline" in topics:
        return "온라인 큐레이션을 오프라인 진열, 체험, 패키지, 선물 동선으로 확장할 수 있어요."
    return "이 장면이 반복된다면 제품, 공간, 서비스 의식, 콘텐츠 포맷 중 무엇으로 포장할지 정해야 해요."


def persona_interpretation(item: dict) -> str:
    topics = set(item.get("topics") or [])
    if not ({"persona_data", "nvidia_ecosystem", "sovereign_ai", "physical_ai"} & topics):
        return ""
    if "persona_data" in topics:
        return "로컬 라이프스타일 탐색자, 업무일 운영자, 가족 물류 구매자, AI 빌더를 나눠 같은 장면의 방문 이유와 지불 이유를 비교하세요."
    if "physical_ai" in topics:
        return "제조 현장 운영자, 로봇/모빌리티 빌더, 엔터프라이즈 AI 스폰서, AI 빌더로 나눠 실행 가능성을 보세요."
    return "AI 빌더, 엔터프라이즈 AI 스폰서, 스타트업 창업자, 공공/대기업 의사결정자를 분리해 채택 경로를 보세요."


def tech_infra_connection(item: dict) -> str:
    topics = set(item.get("topics") or [])
    if "persona_data" in topics:
        return "Nemotron-Personas-Korea를 현장 신호별 시나리오 생성, 메시지 평가, 에이전트 테스트 데이터로 붙일 수 있어요."
    if "sovereign_ai" in topics:
        return "한국어·규제·공공/산업 데이터가 필요한 제품은 소버린 AI 인프라와 연결해 feasibility를 봐야 해요."
    if "physical_ai" in topics:
        return "로봇, 제조, 모빌리티, 공간 운영 문제는 디지털 트윈·시뮬레이션·AI 팩토리 역량과 연결됩니다."
    if "nvidia_ecosystem" in topics:
        return "NVIDIA Korea 개발자·스타트업·대기업 생태계가 실제 배포 파트너와 학습 경로를 제공합니다."
    return ""


def counter_signal(item: dict) -> str:
    topics = set(item.get("topics") or [])
    if str(item.get("source_id", "")).startswith("youtube-"):
        return "영상 조회와 댓글만 강하고 지도 리뷰, 대기, 결제, 재방문 근거가 약하면 촬영용 관심일 수 있어요."
    if "persona_data" in topics:
        return "합성 페르소나는 실제 조사나 결제 데이터를 대체하지 못해요. 해석 보조와 가설 생성으로 제한해야 해요."
    if "nvidia_ecosystem" in topics or "sovereign_ai" in topics or "physical_ai" in topics:
        return "인프라 발표가 실제 현장 채택으로 이어지는지는 별도 문제예요. 개발자 사용, PoC, 예산, 배포 사례를 확인해야 해요."
    if "social_trends" in topics:
        return "공개 사진과 게시물만 강하고 리뷰, 대기, 결제, 재방문 근거가 약하면 일회성 관심일 수 있어요."
    if "reservation" in topics:
        return "예약이 어려운 이유가 공급 부족이나 이벤트 때문인지, 반복 수요 때문인지 분리해야 해요."
    if "real_estate" in topics:
        return "상권 가격이 이미 기대를 반영했다면 새 운영자가 가져갈 초과수익은 작을 수 있어요."
    return "같은 장면이 다른 요일, 다른 동네, 다른 출처에서도 반복되는지 확인해야 해요."


def next_observation(item: dict) -> str:
    topics = set(item.get("topics") or [])
    if str(item.get("source_id", "")).startswith("youtube-"):
        return "같은 장소가 여러 크리에이터의 코스에 반복되는지, 댓글에 위치/예약/가격 질문이 붙는지 보세요."
    if "persona_data" in topics:
        return "같은 현장 신호를 연령, 지역, 직업, 가족 구조별 페르소나로 나눠 다른 해석이 나오는지 테스트하세요."
    if "nvidia_ecosystem" in topics or "sovereign_ai" in topics or "physical_ai" in topics:
        return "NVIDIA Korea 발표, Hugging Face 데이터셋, 개발자 행사, 대기업 AI 팩토리 사례가 같은 방향을 가리키는지 확인하세요."
    if "spatial_reviews" in topics:
        return "최근 30일 리뷰의 사진 구도, 불만, 재방문 표현, 주변 코스 언급을 다시 보세요."
    if "reservation" in topics:
        return "평일/주말, 점심/저녁, 예약 오픈 직후의 잔여 좌석과 대기 언어를 비교하세요."
    if "real_estate" in topics:
        return "유동인구, 업종 밀도, 공실, 임대료, 주변 신규 브랜드 입점을 같이 확인하세요."
    if "retail_offline" in topics:
        return "온라인 랭킹 상품이 오프라인 진열, 팝업, 선물 수요로 이어지는지 보세요."
    return "현장 사진, 지도 리뷰, 예약 표면, 커머스 랭킹 중 하나로 교차 확인하세요."


def render(profile: dict, scored: list[dict], limit: int) -> str:
    selected = scored[:limit]
    lines = [
        "# Physical World Signal Brief",
        "",
        f"- 날짜: {date.today().isoformat()}",
        f"- 대상: {profile_label(profile, 'audience', '한국 창업자 겸 공간/생활 트렌드 에디터')}",
        f"- 목적: {profile_label(profile, 'purpose', '현장성이 있는 세계관의 신호 발굴')}",
        "",
        "## 오늘의 현장 신호",
        "",
    ]
    for index, item in enumerate(selected, start=1):
        persona = persona_interpretation(item)
        infra = tech_infra_connection(item)
        lines.extend(
            [
                f"### {index}. {item.get('title', 'Untitled signal')}",
                f"- 출처: [{item.get('source_name', item.get('source_id', 'unknown'))}]({item.get('url', '')})",
                f"- 점수: {item.get('score', 'n/a')} / 5",
                f"- 장면: {str(item.get('summary', '')).strip()[:220]}",
                f"- 현장 근거: {evidence_labels(item)}",
                f"- 숨어 있는 욕망: {hidden_desire(item)}",
                f"- 사업 번역: {business_translation(item)}",
            ]
        )
        if persona:
            lines.append(f"- 페르소나 해석: {persona}")
        if infra:
            lines.append(f"- 기술/인프라 연결: {infra}")
        lines.extend(
            [
                f"- 반대로 볼 점: {counter_signal(item)}",
                f"- 다음 관찰: {next_observation(item)}",
                "",
            ]
        )
    lines.extend(
        [
            "## 흐름 읽기",
            "",
            "장면이 반복되면 습관이고, 습관에 돈과 시간이 붙으면 시장이에요. 이 브리프는 말보다 이동, 체류, 대기, 결제, 촬영, 물건, 경로, 복제의 흔적을 우선합니다.",
            "",
            "## 주의사항",
            "",
            "- 공개 표면과 수동 관찰을 바탕으로 만든 리서치 초안이에요.",
            "- 지도 리뷰, 예약, 지오태그, 커머스 표면은 플랫폼 약관과 공개 범위 안에서만 사용하세요.",
            "- YouTube, 쇼츠, 지오태그 같은 시각 신호는 지도 리뷰, 대기, 결제, 공공 데이터로 교차 확인하세요.",
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
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    profile = load_json(args.profile)
    scored = score_items(
        item_list(load_json(args.items)),
        source_list(load_json(args.sources)),
        profile,
    )
    physical_scored = [
        item for item in scored if PHYSICAL_TOPICS & set(item.get("topics") or [])
    ]
    if physical_scored:
        scored = physical_scored
    Path(args.output).write_text(render(profile, scored, args.limit), encoding="utf-8")
    print(f"Wrote {min(args.limit, len(scored))} physical-world signals to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
