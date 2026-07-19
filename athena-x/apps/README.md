# apps/

Deployable applications.

| App | Description |
|---|---|
| `nextjs-dashboard/` | Next.js 16 frontend (display only — Change 15) |
| `python-backend/` | FastAPI backend (all AI, agents, calculations) |

## Critical rule (Change 15)

The Next.js dashboard performs NO calculations. It only:
- Display
- Filter
- Search
- Layout
- User interaction

All market calculations, AI inferences, indicators, and forecasts happen
in the Python backend. The dashboard consumes results via TanStack Query
and bus event subscriptions.
