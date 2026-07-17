# Technical Analysis Module

> Bloomberg shortcut: `TA`
> 23 TA agents + indicator matrix

## Implementation status

- [x] Module scaffold
- [ ] Implementation (STEP 4)

## Module structure (per STEP 2 contract)

```
modules/technical-analysis/
├── README.md
├── manifest.ts          # ModuleManifest
├── config.ts            # Zod schema for instance config
├── types.ts             # Module-specific types
├── api.ts               # Backend API client
├── hooks.ts             # TanStack Query + Zustand selectors
├── components/          # UI components
├── services/            # Business logic (delegated to backend — Change 15)
├── index.ts             # Public façade
└── tests/
```

## Critical rule (Change 15)

This module's components MUST NOT perform calculations. They only display
data fetched from the Python backend via TanStack Query and bus subscriptions.
