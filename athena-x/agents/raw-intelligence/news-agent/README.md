# News Agent

> Layer: **raw-intelligence**

Ingests news from RSS + provider APIs. Runs HuggingFace FinBERT for sentiment + impact.

## Event subscriptions

- (none — source agent)

## Event publications

- `news:headline-received`
- `news:sentiment-scored`
- `news:impact-classified`
- `news:entity-mentioned`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
