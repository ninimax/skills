# Source Strategy

Prefer source quality over search volume. Use primary evidence for announcements and independent reporting for impact, controversy, markets, policy, or competition.

## Source Tiers

Tier 0, primary:

- Company and lab newsrooms, government publications, research papers, conference pages, lab pages, and author pages
- Direct posts or interviews only for what the named person directly said

Tier 1, independent:

- Reuters, AP, Bloomberg, Financial Times, Wall Street Journal, New York Times, The Information, and CNBC
- Use for funding, chips, partnerships, litigation, policy, executive moves, safety disputes, and competitive claims

Tier 2, specialist:

- Axios, The Verge, TechCrunch, MIT Technology Review, IEEE Spectrum, Wired, Ars Technica, VentureBeat, Semafor, Platformer, and Stratechery
- Use for discovery, product detail, interviews, developer tooling, and agentic-engineering context; confirm consequential claims with Tier 0 or Tier 1

Tier 3, fallback:

- Trade blogs, syndicated stories, podcasts, newsletters, and social posts
- Do not use as the sole source for consequential claims unless directly attributed and low-risk

## Discovery Graph

Run one parallel broad pass:

1. Primary branch: current company, lab, government, research, and incident-disclosure sources
2. Independent branch: current hard-news reporting
3. Specialist branch: current AI, developer-tooling, and agentic-engineering coverage

Join and normalize the branches before verification. Build at least 14 candidate person-story pairs. Stop broad discovery after the join.

Use at most two targeted-fill rounds, eight targeted searches total, and one confirmation search per candidate. Keep the full research graph within 600 seconds. Target only missing confirmation, weak citations, unclear freshness, or a material gap at the quality gate.

## Normalization and Dedupe

For each source URL, require HTTPS, lowercase the host, remove credentials and fragments, remove common campaign parameters, and strip a non-root trailing slash. Preserve meaningful query parameters.

Assign a stable story fingerprint from the material event, decision, or release. Treat these as duplicates unless a source adds a materially different development:

- The same launch attributed to multiple executives
- The same policy dispute attributed to a company and regulator
- The same funding, chip, data-center, or partnership event attached to several people
- Follow-up commentary with no new fact or decision

Keep the person most directly responsible or most newsworthy, then reject or replace the others.

Never repeat a canonical URL or normalized theme from the two-run history. A person may recur only for a materially new development with `history_overlap_reason: MATERIAL_NEW_DEVELOPMENT` and a novelty score of at least 4. Store rejection and overlap decisions as bounded reason codes, not prose or private reasoning.

## Candidate Score

Score impact, source quality, freshness, influence, and novelty as integers from 0 to 5. Compute:

```text
total = 6*impact + 5*source_quality + 4*freshness + 3*influence + 2*novelty
```

The result ranges from 0 to 100. Prefer a stronger source over a hotter weakly sourced claim. If a familiar person has no high-signal current story, replace them.

## Quality Gate

Select up to 10 candidates with verified current sources and unique people, normalized themes, story fingerprints, and canonical URLs. Prefer stories from the prior two weeks. If fewer than 10 qualify after targeted budgets are exhausted, keep the strongest set and state the exact shortfall. Never pad with weak, duplicate, or invented material.
