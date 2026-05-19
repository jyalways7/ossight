# NVIDIA Korea Persona Layer

Use this layer when physical-world, Korea market, AI adoption, or product-strategy work would benefit from Korean synthetic persona data and NVIDIA ecosystem signals.

This layer is source-backed but should stay bounded:

- `Nemotron-Personas-Korea` is a synthetic persona dataset. Use it for scenario generation, segmentation hypotheses, and evaluation prompts.
- Do not treat synthetic personas as survey results, transaction data, or proof of demand.
- Pair persona interpretation with observed evidence: map reviews, reservation/waiting, YouTube routes, commerce ranking, public data, or direct user research.

## Core Sources

- NVIDIA Blog Korea: Korean NVIDIA ecosystem, Nemotron, enterprise AI, physical AI, and developer content.
- NVIDIA Nemotron-Personas-Korea on Hugging Face: open Korean synthetic persona dataset.
- NVIDIA Korea Personas article: public explanation and context for the dataset.
- NVIDIA AI Day Seoul: Korean developer, startup, enterprise, and research ecosystem signals.
- NVIDIA Korea AI Infrastructure Newsroom: sovereign AI, AI factories, physical AI, robotics, manufacturing, and cloud infrastructure.

## How to Combine With Physical-World Signals

Use a two-layer read:

1. `Observed scene`: What people actually do.
   - movement, dwell, queue, payment, photo, object, route, video route, copy
2. `Persona interpretation`: Who would care and why.
   - age, region, job, household structure, technical maturity, industry context, risk tolerance, budget authority

Then write the synthesis as:

```text
This scene is not one market. It likely splits into these Korean persona jobs:
1. Persona:
   Why this matters:
   Product or space implication:
   Evidence to verify:
```

## Useful Persona Cuts

Start with these cuts before inventing new ones:

- `Local lifestyle explorer`: finds places through Shorts, vlogs, map reviews, and friends.
- `Workday operator`: cares about time saved, reliable routes, waiting reduction, and nearby errands.
- `Family logistics buyer`: cares about parking, seating, stroller access, safety, scheduling, and predictable quality.
- `Creator-commerce visitor`: treats places as content sets, not only consumption locations.
- `AI builder`: evaluates whether Korean data, model, and infrastructure are usable for product development.
- `Enterprise AI sponsor`: cares about sovereignty, security, deployment path, governance, and vendor credibility.
- `Physical AI operator`: connects robotics, manufacturing, mobility, logistics, simulation, and field operations.

## Output Additions

When this layer is active, add:

- `페르소나 해석`: 2-4 Korean persona jobs for each major signal.
- `기술/인프라 연결`: whether NVIDIA/Nemotron/sovereign AI/physical AI changes the feasibility of the opportunity.
- `검증 질문`: what real data would confirm the persona hypothesis.

## Guardrails

- Do not imply NVIDIA endorses the analysis.
- Do not infer sensitive attributes about real people from individual posts or reviews.
- Do not claim a synthetic persona proves market size or conversion.
- Use this layer to sharpen hypotheses, not to replace fieldwork.
