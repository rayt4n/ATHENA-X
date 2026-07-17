# Data Standardization Agent

> Layer: **data-collection**

Maps provider-specific schemas to canonical ATHENA-X schema. Normalizes units. Writes validated, standardized data to processed_market_data schema. ONLY writer to processed_market_data.

## Event subscriptions

- `market:quote-updated`

## Event publications

- (none)

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
