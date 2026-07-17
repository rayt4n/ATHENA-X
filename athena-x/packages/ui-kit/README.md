# @athena-x/ui-kit

Shared shadcn/ui primitives and custom Bloomberg-style components for the
Next.js dashboard. Used by all frontend modules.

## Principles

- Dark-only (institutional terminal aesthetic — no light theme support).
- All numerics rendered in Geist Mono with `tabular-nums`.
- All colors via OKLCH CSS variables defined in `globals.css`.
- No calculations performed in UI components (Change 15).

## Components

- `PanelShell` / `PanelHeader` / `PanelBody` / `PanelFooter` — Bloomberg-style panel chrome
- `TickerTape` — animated ticker (uses `useTickerStore`)
- `Sidebar` / `SidebarNav` / `SidebarWatchlist`
- `Topbar` / `SymbolSearch` / `MainIndicatorSwitch`
- `CommandPalette` — cmdk-based launcher (Ctrl+K)
- `DataTable` — virtualized, sortable, filterable
- `StatCard` / `KpiTile` / `Gauge` / `Heatmap`
- `Skeleton` / `ErrorState` / `EmptyState`
- `StatusBanner` / `StatusDot`
- Chart wrappers (typed Recharts): `LineChart` / `CandlestickChart` / `BarChart` / `AreaChart`

## Usage

```tsx
import { PanelShell, DataTable, StatCard } from '@athena-x/ui-kit';
```
