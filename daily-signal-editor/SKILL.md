---
name: daily-signal-editor
description: Curate public or mock business, AI, startup, and investing sources into source-backed daily signal briefs, market insight memos, newsletter drafts, and content angles. Use when a user needs recurring information curation, founder/VC-style trend synthesis, B2B thought-leadership ideation, or a personalized daily digest with links, scoring, guardrails, and reusable output formats.
---

# Daily Signal Editor

## Overview

Use this skill to turn trusted public sources into a concise daily brief for a specific audience and purpose. The skill is designed for founders, B2B content teams, investors, analysts, and expert creators who need fewer but better signals, with source links and a clear path from reading to writing.

Default to public, read-only sources or mock data. Do not bypass logins, paywalls, robots.txt restrictions, rate limits, or source terms.

## When Not to Use

- Do not use for paid article extraction, login-only newsletters, paywall bypassing, CAPTCHA bypassing, or private data scraping.
- Do not use for real-time trading decisions, buy/sell/hold recommendations, or guaranteed return claims.
- Do not use when the user needs full article reproduction instead of source-linked synthesis.
- Do not use when no source link, user-provided excerpt, public report, RSS item, or mock item is available.

## Inputs

Collect or infer these inputs before running the workflow:

- `audience`: founder, B2B marketer, investor, analyst, creator, or a custom persona.
- `purpose`: market research, content ideation, newsletter drafting, investment research, product strategy, or competitive sensing.
- `domains`: business, AI, startups, VC, public markets, consumer trends, Korea business, or a custom niche.
- `source_mix`: global VC, Korea startup, AI research, market data, financial reports, community sources.
- `output_mode`: daily brief, newsletter draft, investment memo, LinkedIn/X post, blog outline, Slack update, meeting agenda, sales talking points, or source map.
- `time_window`: today, last 24 hours, this week, or a fixed date range.
- `lens_team`: optional expert lenses or task categories to emphasize.

If the user only says "make my daily brief", use this default:

```json
{
  "audience": "Korean founder-investor",
  "purpose": "market research and content ideation",
  "domains": ["AI", "business models", "VC thinking", "investable market signals"],
  "source_mix": ["global VC", "Korea startup", "AI research", "market reports"],
  "output_mode": "daily brief plus content angles"
}
```

## Workflow

1. Define the user profile.
   - Clarify audience, purpose, domain, and output mode when missing.
   - Prefer one primary persona over a generic "everyone" brief.
   - Read `references/task-categories.md` when the user's job-to-be-done is broad or ambiguous.
   - Read `references/role-library.md` when expert lenses would improve judgment. Use named anchors only as decision lenses, not as impersonation or endorsement.

2. Choose sources.
   - Read `references/source-catalog.md` when choosing or explaining source strategy.
   - Use `mock-data/source-registry.json` as the default source universe.
   - Run `scripts/plan_sources.py` when the user wants the skill to choose sources automatically for a persona, purpose, or domain.
   - Favor official blogs, RSS feeds, public reports, public APIs, and user-provided links.
   - Include Korean sources when the user cares about Korean business, startups, consumers, policy, or investing.
   - Rotate sources by persona and day instead of reading the same feed list every time. Keep RSS sources for automatic fetch and non-RSS newsletters, reports, and YouTube channels as watchlist sources.

3. Gather candidate items.
   - Use public source summaries, RSS items, official posts, public reports, or mock data.
   - Preserve title, URL, source, date, summary, and topic tags.
   - Do not copy paid or full copyrighted articles. Summarize short snippets and link to the source.

4. Score and select.
   - Read `references/scoring-rubric.md` for scoring criteria.
   - Score candidates on freshness, source quality, audience fit, business impact, novelty, signal durability, and content potential.
   - Remove duplicates and cluster related items.
   - Select the top 3-7 signals.

5. Pattern-match and synthesize.
   - Read `references/editorial-rubric.md` for the editorial lens.
   - Connect the selected signals into one directional market read.
   - Include a contrarian view or counter-signal when evidence is incomplete.
   - Explain whether the pattern is tactical, strategic, or still speculative.

6. Synthesize individual signals.
   - For each signal, explain why it matters, who is affected, what changes if it is true, and what to watch next.
   - Separate evidence from interpretation.

7. Produce the output.
   - Read `references/output-formats.md` for format choices.
   - Always include source links, scores, caveats, and next actions.
   - Include at least one actionable artifact: Slack update, LinkedIn/X hook, meeting agenda, newsletter intro, research question, or sales talking point.
   - For investing topics, frame as research and education, not investment advice.

8. Validate.
   - Read `references/safety-and-copyright.md` before publishing or sharing.
   - Check that every key claim has a source link.
   - Check that the output is useful to the chosen audience, not just a generic news summary.

## Local Demo

Use the bundled mock data when live sources are unavailable or when running a reproducible local demo:

```bash
python3 scripts/build_digest.py \
  --sources mock-data/sample-sources.json \
  --items mock-data/sample-items.json \
  --profile mock-data/sample-user-profile.json \
  --output examples/daily-brief.md
```

Validate the generated brief:

```bash
python3 scripts/validate_digest.py examples/daily-brief.md
```

Plan sources for a persona before fetching:

```bash
python3 scripts/plan_sources.py \
  --registry mock-data/source-registry.json \
  --profile mock-data/profiles/founder.json \
  --output examples/founder-source-plan.json \
  --rss-output /tmp/founder-rss-sources.json
```

## Done When

- The target audience and purpose are explicit.
- The selected signals have source links and scores.
- The brief explains "why it matters", not only "what happened".
- The output includes at least one reusable content angle or next action.
- Copyright, paywall, login, and investment-advice boundaries are respected.

## Response Style

- Keep the answer compact enough to read daily.
- Prefer tables only when comparing signals, sources, or scores.
- State uncertainty when evidence is weak.
- Use "source says" for reported claims and "this suggests" for interpretation.
- End with practical next actions, such as a writing angle, follow-up source, or question to verify.

## Failure Modes

- If sources are unavailable, use mock data or ask the user for public links.
- If the user requests paid or login-only content, ask for a public excerpt or use the source headline/link only.
- If a topic is too broad, narrow by audience, geography, sector, and time window.
- If the output becomes generic, re-score for audience fit and content potential.
- If investing content could be mistaken for advice, add an explicit research-only caveat.
