# Data Governance & Metric Transparency

This document describes how the system distinguishes **exact** vs
**estimated** metrics and how that is communicated in APIs and the UI.

## Metric provenance

Where possible, metrics are computed directly from structured CSV data
with no inference. In a few areas, the system may need to fall back to
simpler approximations:

- **Independent Wave (district-level)**  
  - Primary method: vote-based share using `votes_received` and
    `is_independent`.  
  - Fallback: candidate-based share (independent candidates /
    total candidates) when vote data is missing.  
  - API field: `method` = `"votes"` or `"candidates"` clarifies which
    approach was used, and the frontend reflects this in labels.

- **Competition Pressure**  
  - Uses `votes_received` when available.  
  - If vote counts are missing, assumes equal weight per candidate in
    a race, which is clearly less precise but still signals crowded vs
    safe contests.

- **Party Saturation vs Reach**  
  - Uses `is_winner` when available; otherwise `seats_won` may be null.
  - Win rate is only computed when contested seats and winners are
    both present.

## Sensitive attributes and estimation

For sensitive attributes such as **gender**, **age**, and **education**:

- The system prefers **explicit CSV columns** (`gender`, `age`,
  `education_level`) sourced from authoritative data.
- Any future inference (e.g., gender inference from names) must:
  - Be implemented in a clearly separated enrichment step.
  - Store a flag (e.g., `is_estimated`) or confidence score.
  - Be labeled in API responses and surfaced in the UI as
    **estimated**, not exact.

Currently, no automatic inference of gender, education, or birthplace
is performed; metrics that depend on these attributes will simply be
absent or null when data is missing.

## UI responsibilities

Frontend components consuming these metrics should:

- Read the `method` or similar flags from API responses and adjust
  chart subtitles and tooltips accordingly (e.g., “vote share” vs
  “candidate share”).
- Clearly indicate when a chart or metric:
  - is based on partial data (e.g., limited winner flags), or
  - excludes districts/parties where required fields are missing.
- Avoid over-claiming insights for metrics derived from approximations;
  visual emphasis (badges, labels) should align with high-quality data
  segments (e.g., “Independent Surge Zone” only where vote-based
  shares exist).

## Logging & diagnostics

Backend code logs when:

- Elections fail to load.
- Optional columns needed for a given metric are missing.

This allows operators to track where data gaps prevent certain insights
from being computed and to prioritize enrichment work accordingly.

