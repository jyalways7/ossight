# Source Catalog

Use this catalog to choose source mixes for daily briefs. Prefer public, official, and read-only sources. Use mock data for reproducible demos and offline validation.

The machine-readable source universe lives in `mock-data/source-registry.json`. Use `scripts/plan_sources.py` to choose a rotating source plan for the user's audience, purpose, domains, and output mode.

## Active Source Rotation

Do not read the same fixed source list every day. Build a source plan first:

1. Match the user's persona and purpose against source `domains`, `personas`, and `geography`.
2. Prefer Tier 1 official sources for factual claims.
3. Mix source types: official blogs, VC/operator writing, newsletters, Korea sources, reports, community sources, and YouTube.
4. Use RSS sources for automatic fetch.
5. Keep non-RSS newsletters, public reports, and YouTube channels as watchlist sources.
6. Rotate among similar sources by day or seed so the brief does not become repetitive.

For a Daily 50 workflow, plan 20-30 sources, fetch 5-10 items from each RSS source, then rank the combined pool. The 50-item queue is a discovery surface, not the final brief: promote only the top A-tier items into synthesis or content drafts.

Example:

```bash
python3 scripts/plan_sources.py \
  --registry mock-data/source-registry.json \
  --profile mock-data/profiles/founder.json \
  --output examples/founder-source-plan.json \
  --rss-output /tmp/founder-rss-sources.json \
  --max-sources 24 \
  --max-per-type 8
```

## Source Tiers

### Tier 1: Official and Primary

Use these when accuracy matters.

- Company blogs: OpenAI, Anthropic, Google DeepMind, Microsoft, NVIDIA, Stripe, Shopify, Coupang, Naver, Kakao.
- VC firm blogs: Y Combinator, a16z, Sequoia, Bessemer, NFX, First Round Review, Lightspeed.
- Public filings and regulators: DART, SEC, FSS, Korea Exchange, Bank of Korea, KOSIS.
- Official research PDFs: financial institutions, government agencies, public research groups.

### Tier 2: Curated Industry Sources

Use these to find narratives and emerging topics.

- Global: Hacker News, The Information headlines, TechCrunch, Stratechery excerpts when public, Lenny's Newsletter public posts, Latent Space.
- Korea: GeekNews, Startup Alliance, Platum, Venturesquare, THE VC public pages, Hankyung startup coverage.
- Investing and wealth: KB, Hana, Shinhan, Woori, Mirae Asset, Samsung Securities, Daishin research pages when publicly accessible.

### Newsletters and Podcasts

Use these for narrative discovery and content angles. Verify important claims with primary sources:

- AI and developer: Latent Space, Import AI, The Batch, Ben's Bites, TLDR AI.
- Product and startup operations: Lenny's Newsletter, First Round Review.
- Strategy and markets: Stratechery public posts, Not Boring public posts.

### YouTube and Video

Use video sources as watchlist items unless transcripts are available:

- Y Combinator YouTube for founder education.
- a16z YouTube for market narrative and interviews.
- Gartner YouTube for enterprise technology framing.

### Tier 3: Community and Social Signals

Use these as weak signals only. Verify with Tier 1 or Tier 2 before making strong claims.

- Reddit, X, LinkedIn, YouTube descriptions, community newsletters, comments.
- Treat these as narrative evidence, not factual proof.

## Suggested Source Mixes

### AI Founder Brief

- OpenAI, Anthropic, Google DeepMind, NVIDIA.
- YC, a16z, Sequoia.
- GeekNews, Hacker News.
- Korea AI/startup news for localization.

### B2B Content Brief

- First Round Review, Lenny's public posts, a16z, OpenView-style SaaS writing when available.
- Customer case studies from Stripe, HubSpot, Salesforce, Atlassian.
- Korean B2B market articles and reports.

### Investor Research Brief

- Public company blogs and filings.
- Public securities reports.
- VC market maps and official data sources.
- Startup funding databases with public pages.

## Source Rules

- Keep the URL for every item.
- Record access type: RSS, public web, public API, user-provided, mock.
- Do not scrape login-only content.
- Do not reproduce full copyrighted text.
- If a source is a secondary report, say so and avoid overclaiming.
- If a source is Korean and the output is English, preserve Korean names and translate cautiously.
