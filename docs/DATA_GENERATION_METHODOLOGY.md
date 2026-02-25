# Data Generation Methodology

## Purpose
This project uses synthetic data to exercise a Responsible Gaming analytics pipeline, not to replicate operator production data.

## Scope
- Jurisdictions in scope: MA, NJ, PA.
- Output artifacts include player profiles, betting activity, risk inputs, and derived case queues.
- Data is generated for reproducible testing and demo workflows.

## Method Summary
- Generate player-level baseline attributes.
- Simulate bet-level activity over a rolling historical window.
- Derive risk components used by queue/case workflows.
- Load generated artifacts into DuckDB for API and dbt consumption.

## Correlation and Behavioral Modeling
- Correlated latent factors are seeded during generation.
- Downstream state-machine behavior can attenuate targeted correlations.
- Correlation targets are therefore treated as directional, not exact guarantees.

## Validation Performed
- Distribution checks for risk cohorts and state allocation.
- Sanity checks for edge-case players (very low/high volume, missing fields, outliers).
- Reproducibility checks by deterministic seeding.

## What This Data Is Good For
- Validating ETL/model wiring.
- Exercising analyst workflows and audit logs.
- Demonstrating static/live mode behavior.

## What This Data Is Not Good For
- Estimating real player prevalence or business impact.
- Claiming production intervention efficacy.
- Making policy decisions without real operational datasets.

## Risks and Bias Considerations
- Synthetic assumptions can over- or under-represent behavior patterns.
- Generated cohorts can influence analyst narratives in non-realistic ways.
- Any model or analyst output should be interpreted within those limits.
