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

For broad trend work, enforce category diversity instead of letting AI dominate. Use `source_category_mix` in the profile. Recommended mix:

- `business`: general company, strategy, retail, platform, and market-model shifts.
- `consumer`: consumer behavior, lifestyle, shopping, brand, and survey reports.
- `persona_data`: synthetic persona datasets and public explanations used for hypothesis generation and scenario testing.
- `nvidia_ecosystem`: NVIDIA Korea ecosystem, developer, startup, AI Day, enterprise AI, and infrastructure signals.
- `sovereign_ai`: Korean sovereign AI, local model, language, public-private AI, and national AI infrastructure signals.
- `physical_ai`: robotics, digital twins, manufacturing AI, mobility, simulation, AI factories, and field-operation signals.
- `physical_world`: material-world behavior such as movement, dwell, payment, photos, routes, and offline experiences.
- `spatial_reviews`: map reviews, public place pages, review counts, photo patterns, complaints, and repeat-visit language.
- `reservation`: public reservation, waiting, queue, and availability surfaces.
- `retail_offline`: commerce curation, brand ranking, store/pop-up activation, merchandising, and lifestyle objects.
- `real_estate`: commercial-area data, business density, foot traffic, vacancy, lease, and rent narratives.
- `content_ip`: creator economy, YouTube, games, entertainment, fandom, and IP extensions.
- `social_trends`: X, Threads, YouTube trending, Google Trends, Reddit, and community weak signals.
- `app_rankings`: app store charts, mobile rankings, traffic/ranking reports.
- `investing`: wealth, macro, public markets, and funding narratives.
- `korea`: local market, policy, startup, and community context.
- `ai`: keep as one category, not the whole brief.

Planner outputs are separated by collection method:

- `rss_sources`: fetch automatically with `scripts/fetch_rss.py`.
- `app_ranking_sources`: fetch with `scripts/fetch_app_rankings.py` when an `api_url` exists.
- `manual_signal_sources`: inspect manually or use user-provided public links/excerpts. This includes X, Threads, and YouTube trending.

For physical-world work, most sources are watchlist or manual sources. Do not scrape map reviews, bypass platform controls, automate bookings, or collect private account content. Record only short public observations and link to the public surface.

For NVIDIA Korea persona work, treat Nemotron-Personas-Korea as a scenario and evaluation layer. It can sharpen Korean persona hypotheses, but it does not replace user interviews, survey data, transaction data, or observed behavior.

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
- YouTube Trending Korea for fast public-interest signals. Treat titles and visible metrics as weak signals, not proof.
- YouTube Korea vlogs and place Shorts for physical-world work. Track route order, repeated locations, entrance shots, waiting language, comments asking for location, and creator-made courses. Verify with map reviews, reservation surfaces, or public spatial data.

### Social, Search, and App Ranking Signals

Use these as early indicators of attention, language, and product demand:

- X Explore and Threads Search: public posts only, no login bypass, no scraping protected content.
- Google Trends Korea: search interest and rising queries.
- Apple App Store rankings: app category movement and product idea discovery.
- Similarweb, Sensor Tower, Mobile Index: public ranking reports and app/web traffic narratives.

When these sources produce a signal, ask:

- Which segment is paying attention?
- Is the interest rising, recurring, or just a one-day spike?
- Does the signal imply a product idea, content hook, distribution channel, or IP extension?
- What stronger source would confirm it?

### Physical World, Space, and Retail Signals

Use these to observe where online attention becomes embodied behavior:

- Map/place reviews: Naver Map, Kakao Map, Google Maps where public. Look for recent review language, photo repetition, complaints, revisit words, and route context.
- Reservation and waiting: CatchTable, Tabling, public booking availability, visible waitlist language, and regional/category clustering.
- Public spatial data: Seoul Open Data, commercial-area data, transport and foot-traffic datasets, small-business density, vacancy, and local facility data.
- Retail and lifestyle curation: 29CM, Musinsa, Todayhouse, department-store pop-ups, flagship stores, and public brand campaigns.
- Public visual signals: Instagram public geotags, YouTube vlogs, Shorts/Reels titles, and creator routes. Treat as weak signals, but include them intentionally because they reveal movement order and scene design better than text-only sources.

When these sources produce a signal, ask:

- What scene is repeated: movement, dwell, queue, payment, photo, object, route, or copy?
- What hidden desire is being materialized?
- Is this attention, a habit, or a market?
- Which stronger source confirms it: reservation data, map reviews, public spatial data, commerce ranking, or repeated brand replication?
- Can the format survive outside the original neighborhood?

### NVIDIA Korea Persona and Ecosystem Signals

Use these to connect Korean physical-world and consumer observations with AI adoption capability:

- NVIDIA Blog Korea and NVIDIA AI Day Seoul: developer, startup, enterprise, sovereign AI, and physical AI ecosystem cues.
- Nemotron-Personas-Korea: synthetic Korean personas for scenario generation and evaluation prompts.
- NVIDIA Korea AI infrastructure announcements: AI factories, sovereign cloud, manufacturing, robotics, and physical AI capability.
- Hugging Face dataset metadata: license, release context, dataset scale, tags, and intended use.

When these sources produce a signal, ask:

- Which Korean persona jobs does this help separate?
- Does the signal change product feasibility, distribution, or evaluation?
- Is this a real deployment path or only ecosystem narrative?
- Which observed behavior would validate the persona hypothesis?
- Which human research or operational data is still missing?

### Tier 3: Community and Social Signals

Use these as weak signals only. Verify with Tier 1 or Tier 2 before making strong claims.

- Reddit, X, LinkedIn, YouTube descriptions, community newsletters, comments.
- Treat these as narrative evidence, not factual proof.
- Mark social/app ranking items as weak signals unless supported by primary sources, app store data, or repeated observations.

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
