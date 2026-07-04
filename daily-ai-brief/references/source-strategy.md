# Source Strategy

Use source quality over search volume. Prefer primary evidence for announcements and independent reporting for claims about impact, controversy, markets, policy, or competition.

## Source Tiers

Tier 0: primary sources for exact announcements.

- Company and lab newsrooms: OpenAI, Anthropic, Google DeepMind, Google AI, Meta AI, Microsoft AI, Nvidia, xAI, Hugging Face, Mistral, Cohere, AI2.
- Research sources: arXiv, OpenReview, Nature, Science, conference pages, lab pages, and author pages.
- Direct posts or interviews from the named person, only for what that person directly said.

Tier 1: independent hard-news confirmation.

- Reuters, AP, Bloomberg, Financial Times, Wall Street Journal, New York Times, The Information, CNBC.
- Use these for funding, chips, partnerships, litigation, policy, executive moves, market impact, safety disputes, and competitive claims.

Tier 2: AI and tech-specialist discovery.

- Axios, The Verge, TechCrunch, MIT Technology Review, IEEE Spectrum, Wired, Ars Technica, VentureBeat, Semafor, Platformer, Stratechery.
- Use these for product detail, interviews, developer tooling, and agentic-engineering context. Confirm major claims with Tier 0 or Tier 1 when possible.

Tier 3: fallback and color only.

- Business Insider, Fortune, Forbes, Barron's, hardware blogs, syndicated stories, podcasts, newsletters, and social posts.
- Do not use these as the only source for consequential financial, policy, safety, or competitive claims unless the item is directly attributed and low-risk.

## Search Loop

Run at most three passes:

1. Broad scan: search current-month AI agent/model/coding/safety/infrastructure news across Tier 1 and Tier 2 sources.
2. Primary-source scan: check official pages for the strongest candidate companies or labs.
3. Targeted fill: search by person name plus company/topic only when a candidate needs confirmation, freshness, or a better link.

Stop searching once there are 10 distinct high-signal stories with credible current sources. Spend the final pass on source quality and dedupe instead of widening search.

## Candidate Scoring

Prefer candidates that score strongly on:

1. Source quality: primary or independent reporting beats reposts and commentary.
2. Freshness: today/yesterday beats current week; current week beats older background.
3. Topic fit: agents, coding agents, model releases, safety/governance, infrastructure, open source, or major AI business/product moves.
4. Person fit: the named person is directly involved, quoted, responsible, or unusually influential for the story.
5. Novelty: not already covered in the last two run-log entries unless the story materially advanced.

## Replacement Rule

Do not force a familiar roster. If a usual AI figure has no current high-signal story, replace them with another influential founder, researcher, executive, builder, safety/policy expert, or open-source leader who does.
