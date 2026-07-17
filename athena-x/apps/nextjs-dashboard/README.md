# ATHENA-X Dashboard (Next.js 16)

> Institutional-grade quantitative intelligence terminal UI.

## Critical constraint (Change 15)

The dashboard NEVER calculates. It only displays, filters, searches, layouts,
and handles user interaction. All calculations happen in the Python backend.

## Stack

- Next.js 16 (app-router, Turbopack, RSC)
- React 19
- Tailwind CSS v4 (dark-only, OKLCH)
- shadcn/ui primitives (from `@athena-x/ui-kit`)
- Zustand (workspace state)
- TanStack Query (server state)
- Recharts (charts)
- Framer Motion (animations)
- cmdk (command palette)
- lucide-react (icons)
- sonner (toasts)

## Modules (10 — Bloomberg-style)

| # | Module | Shortcut | Multi-Instance |
|---|---|---|---|
| 01 | Dashboard | `DASH` | no |
| 02 | Live Market Data | `MKT` | yes |
| 03 | Technical Analysis | `TA` | yes |
| 04 | News Intelligence | `NEWS` | no |
| 05 | Options Intelligence | `OPT` | yes |
| 06 | Macro Intelligence | `MACRO` | no |
| 07 | Market Intelligence | `MI` | yes |
| 08 | Probability Engine | `PROB` | yes |
| 09 | Report Generator | `RPT` | no |
| 10 | Self Validation | `VAL` | yes |

Additional system modules:
- `Agent Health Dashboard` (Change 17)
- `Data Quality Dashboard` (Change 18)

## Implementation status

- [x] Project scaffold
- [ ] Module implementations (STEP 4)
