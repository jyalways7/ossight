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
    "ai": [
        "ai",
        "agent",
        "agents",
        "llm",
        "model",
        "openai",
        "anthropic",
        "automation",
        "claude",
        "codex",
        "grok",
        "deepfake",
        "world model",
        "self-improving",
        "artificial intelligence",
        "모델",
        "인공지능",
    ],
    "workflow": ["workflow", "workflows", "brief", "briefs", "packet", "packets", "plan", "plans", "diagnosis", "updates"],
    "startups": ["startup", "startups", "founder", "founders", "yc", "seed", "growth"],
    "vc": ["vc", "venture", "funding", "investment", "investor"],
    "business": [
        "business",
        "market",
        "revenue",
        "pricing",
        "sales",
        "enterprise",
        "operations",
        "pipeline",
        "ipo",
        "goes public",
        "funding",
        "retention",
        "customer",
        "고객",
        "시장",
        "투자",
    ],
    "developer": ["developer", "developers", "code", "github", "open source", "api", "data science", "코드", "개발"],
    "consumer": ["consumer", "shopping", "retail", "brand", "commerce", "lifestyle", "trend", "소비", "쇼핑", "브랜드", "라이프스타일"],
    "persona_data": ["persona", "personas", "synthetic persona", "demographic", "census", "페르소나", "합성 데이터", "인구통계"],
    "nvidia_ecosystem": ["nvidia", "nemotron", "cuda", "dgx", "inception", "gpu", "엔비디아"],
    "sovereign_ai": ["sovereign ai", "sovereign", "foundation model", "k-ai", "소버린", "파운데이션 모델"],
    "physical_ai": ["physical ai", "robotics", "robot", "digital twin", "omniverse", "factory", "피지컬 ai", "로봇", "디지털 트윈", "팩토리"],
    "content_ip": ["creator", "creators", "content", "ip", "streaming", "youtube", "gaming", "game", "entertainment", "fan", "콘텐츠", "크리에이터", "팬덤", "게임", "엔터"],
    "app_rankings": ["app", "apps", "mobile app", "app store", "ranking", "rankings", "앱", "모바일", "순위"],
    "social_trends": ["trend", "trending", "viral", "meme", "x.com", "threads", "youtube", "shorts", "틱톡", "인급동", "밈", "바이럴"],
    "physical_world": ["offline", "physical", "space", "place", "store", "popup", "pop-up", "restaurant", "cafe", "hotel", "공간", "장소", "매장", "팝업", "오프라인", "카페", "호텔"],
    "spatial_reviews": ["review", "reviews", "rating", "map", "geotag", "photo spot", "place review", "리뷰", "지도", "별점", "포토스팟", "방문자"],
    "reservation": ["reservation", "booking", "waitlist", "waiting", "queue", "table", "예약", "대기", "웨이팅", "줄", "캐치테이블", "테이블링"],
    "retail_offline": ["retail", "shop", "brand", "merchandising", "flagship", "department store", "리테일", "쇼룸", "플래그십", "백화점", "편집숍"],
    "real_estate": ["real estate", "commercial real estate", "lease", "rent", "vacancy", "foot traffic", "상권", "임대", "공실", "유동인구", "상가"],
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
    strong_terms = ["ai", "agent", "startup", "market", "workflow", "funding", "enterprise", "consumer", "creator", "ranking", "app", "content", "brand", "offline", "space", "place", "reservation", "queue", "retail", "persona", "nvidia", "nemotron", "sovereign", "physical ai", "상권", "공간", "예약", "대기", "페르소나", "소버린"]
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
    legal_signal = any(
        has_keyword(lowered, term)
        for term in ["legal", "law", "privacy", "regulatory", "governance", "compliance", "법률", "규제"]
    )
    if "databricks" in lowered and "agent" in lowered:
        return "엔터프라이즈 AI 에이전트가 데이터가 많은 업무 환경에서 검증되고 있어요. 이제 중요한 건 채팅 성능보다 신뢰성, 평가, 업무 통합이에요."
    if "coding model" in lowered or "coding agent" in lowered or "claude code" in lowered:
        return "코딩 에이전트가 개발자 플랫폼의 진입점이 되고 있어요. 가격, 오픈소스 대안, 워크플로 락인이 모두 전략 변수가 돼요."
    if "cloud" in lowered and ("infrastructure" in lowered or "aws" in lowered):
        return "AI 네이티브 클라우드 수요가 커지면서 인프라 스타트업의 경쟁 기준이 바뀌고 있어요. 단순 성능보다 개발 속도와 배포 경험이 중요해져요."
    if "customer interview" in lowered or "listen labs" in lowered:
        return "고객 인터뷰와 PMF 학습이 반복 가능한 소프트웨어 업무로 바뀌고 있어요. 창업자에게는 리서치 자동화 제품의 기회가 생겨요."
    if "slackbot" in lowered or "workplace ai" in lowered:
        return "협업 도구 안의 AI가 단순 도우미에서 업무 에이전트로 바뀌고 있어요. 데이터 접근권, 권한 관리, 일상 업무 점유가 경쟁력이 돼요."
    if "self-improving" in lowered or "world model" in lowered:
        return "프런티어 AI 기업들이 데모를 넘어 제품화된 연구 루프를 만들고 있어요. 방어력과 상용화 속도를 함께 봐야 해요."
    if "hiring" in lowered or "talent" in lowered:
        return "AI 스타트업은 제품만큼 채용 내러티브로도 경쟁하고 있어요. 좋은 인재를 끌어오는 방식 자체가 카테고리 신호가 돼요."
    if "legal action" in lowered and ("apple" in lowered or "platform" in lowered):
        return "AI 유통은 플랫폼 협상력이 좌우하는 시장이 되고 있어요. 노출 위치, 사용자 맥락, 수익화를 누가 쥐는지 봐야 해요."
    if legal_signal and "ai" in topic_set:
        return "도메인 특화 AI 에이전트가 규제 산업으로 들어가고 있어요. 신뢰, 데이터 접근, 검토 절차가 제품의 핵심 질문이 돼요."
    if "sales" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "AI 업무 도구가 개발을 넘어 매출 조직으로 확장되고 있어요. 계정 리서치, 파이프라인 점검, 미팅 준비가 B2B SaaS 유스케이스가 돼요."
    if "operations" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "운영팀은 대시보드보다 바로 판단할 수 있는 브리프와 업데이트를 원해요. 업무 소프트웨어의 중심이 준비된 판단 자료로 이동하고 있어요."
    if "data science" in lowered and ("codex" in lowered or "ai" in topic_set):
        return "AI 코딩 에이전트가 분석 업무용으로 포장되고 있어요. 복잡한 업무 입력을 원인 분석과 대시보드 기획으로 바꾸는 도구 수요가 보여요."
    if "goes public" in lowered or "operating system" in lowered:
        return "특정 업종의 워크플로 회사가 상장 규모까지 커졌다는 건, 좁은 운영체제가 매일 쓰는 데이터를 잡으면 커질 수 있다는 신호예요."
    if "incorporation" in lowered:
        return "법인 설립 경로가 바뀌면 창업자가 어디에서 시작하고 투자받을지도 달라져요. 국경을 넘는 스타트업 형성에 영향을 줄 수 있어요."
    if "general partner" in lowered:
        return "VC의 파트너 영입은 앞으로 어떤 창업자 배경, 섹터, 네트워크를 중요하게 볼지 보여주는 신호가 될 수 있어요."
    if "security" in topic_set:
        return "개발자 커뮤니티의 보안 습관 변화는 도구, 채용, 교육 수요의 초기 신호가 될 수 있어요."
    if "app_rankings" in topic_set:
        return "앱 순위는 사람들이 실제로 설치하고 써보는 관심사를 보여줘요. 제품 아이디어와 카테고리 변화를 찾을 때 좋은 초기 신호예요."
    if "content_ip" in topic_set:
        return "콘텐츠와 IP 흐름은 팬덤, 커머스, 게임, 오프라인 경험으로 확장될 수 있어요. 단순 조회수보다 반복 소비와 2차 수익화를 봐야 해요."
    if "consumer" in topic_set:
        return "소비자 관심의 변화는 가격, 채널, 브랜드 메시지를 바꿔요. 사람들이 실제로 시간과 돈을 쓰는 이유를 확인해야 해요."
    if "physical_world" in topic_set:
        return "오프라인 신호는 사람이 실제로 이동하고 머물고 돈을 내는 흔적이에요. 말보다 강한 수요 증거가 될 수 있어요."
    if "spatial_reviews" in topic_set:
        return "공간 리뷰는 만족도보다 방문 동기, 사진 구도, 불편, 재방문 언어를 봐야 해요. 공간이 어떤 욕망을 해결하는지 드러나요."
    if "reservation" in topic_set:
        return "예약과 대기는 시간 비용을 감수한 수요예요. 유행인지 반복 루틴인지 확인하면 더 강한 사업 신호가 돼요."
    if "retail_offline" in topic_set:
        return "리테일 신호는 취향이 물건과 진열, 동선으로 굳어지는 순간을 보여줘요. 온라인 언어가 오프라인 매출로 바뀌는지 봐야 해요."
    if "real_estate" in topic_set:
        return "상권과 임대 신호는 공급자가 어디에 베팅하는지 보여줘요. 브랜드와 사람의 흐름이 공간 가격을 바꾸는지 확인해야 해요."
    if "persona_data" in topic_set:
        return "페르소나 데이터는 관찰된 장면을 한국 사용자 맥락으로 해석하게 해줘요. 현장 신호를 제품 가설과 시나리오 평가로 바꿀 수 있어요."
    if "nvidia_ecosystem" in topic_set:
        return "NVIDIA 생태계 신호는 한국 AI 개발자, 스타트업, 대기업, 인프라가 어디에 모이는지 보여줘요. 실행 가능한 기술 채택 맥락을 읽어야 해요."
    if "sovereign_ai" in topic_set:
        return "소버린 AI 신호는 한국어, 규제, 산업 데이터, 공공 인프라가 결합되는 방향을 보여줘요. 로컬 제품 전략의 기준점이 될 수 있어요."
    if "physical_ai" in topic_set:
        return "피지컬 AI 신호는 로봇, 제조, 모빌리티, 공간 운영이 AI와 연결되는 지점을 보여줘요. 현장과 시뮬레이션의 간극을 봐야 해요."
    if "social_trends" in topic_set:
        return "소셜 트렌드는 빠르게 식을 수 있지만 대중의 언어와 관심사를 빨리 보여줘요. 제품 훅이나 콘텐츠 가설을 만들 때 유용해요."
    return "후보 신호로는 볼 수 있어요. 다만 전략에 반영하려면 더 강한 1차 출처나 반복 패턴을 확인해야 해요."


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
        summary_for_signal = summary[:600]
        text = f"{title} {summary_for_signal}"
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
