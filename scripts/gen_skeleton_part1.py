#!/usr/bin/env python3
"""
ATHENA-X Monorepo Skeleton Generator — STEP 3, Part 1
======================================================
Generates: top-level config, packages/, schemas/, database/, runtime/

Run:  python /home/z/my-project/scripts/gen_skeleton_part1.py
"""

from pathlib import Path
import json
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)

FILES_WRITTEN = 0

def w(rel: str, content: str) -> None:
    """Write a file under ROOT."""
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    global FILES_WRITTEN
    FILES_WRITTEN += 1

# ============================================================================
# TOP-LEVEL FILES
# ============================================================================

w("README.md", '''
# ATHENA-X

> Institutional-grade quantitative intelligence terminal.
> Modular · Plugin-based · Event-driven · AI-supervised · Self-learning.

## What this is

ATHENA-X is a Bloomberg-style market intelligence platform built around
a strict layered architecture:

```
Data Collection AI → Data Validation AI → Data → Standardization AI
   → Market Data Database → Raw Intelligence Agents → Decision Intelligence
   → Supervisor AI → Institutional Validation → Report Engine → Dashboard
```

Nothing enters the system without passing through the data pipeline.
The dashboard never calculates — it only displays.

## Repository layout

| Directory | Purpose |
|---|---|
| `apps/` | Deployable applications (Next.js dashboard, Python backend) |
| `packages/` | Shared, framework-agnostic packages |
| `agents/` | All AI agents (Python) — independent, supervised |
| `engines/` | Orchestration frameworks (data, AI runtime, backtest, etc.) |
| `plugins/` | Installable indicator/pattern/options plugins |
| `providers/` | Market data provider adapters |
| `schemas/` | Single source of truth for events, DB, AI models |
| `database/` | Four logical databases (raw, processed, AI, reports) |
| `runtime/` | Bus, queue, scheduler, health, logging, metrics |
| `docs/` | Architecture, ADRs, runbooks |
| `tests/` | Cross-cutting e2e/load tests |
| `scripts/` | Dev/utility scripts |
| `tools/` | Internal scaffolding tooling |
| `configs/` | Environment-specific configs |

## Status

**STEP 3** — folder skeleton. No feature implementation yet.

See `docs/architecture/STEP-2-REVISED.md` for the full architecture specification
and `docs/architecture/implementation-order.md` for the STEP 4 plan.

## Quick start

```bash
# Frontend (Next.js dashboard)
cd apps/nextjs-dashboard && pnpm install && pnpm dev

# Backend (Python FastAPI)
cd apps/python-backend && uv sync && uv run uvicorn main:app --reload

# Or use the workspace scripts
./scripts/setup-dev.sh
```

## License

Proprietary. © 2026 ATHENA-X.
''')

w("package.json", json.dumps({
    "name": "athena-x",
    "version": "0.1.0",
    "private": True,
    "description": "Institutional-grade quantitative intelligence terminal",
    "packageManager": "pnpm@9.14.0",
    "engines": {"node": ">=20.0.0", "pnpm": ">=9.0.0"},
    "scripts": {
        "build": "turbo run build",
        "dev": "turbo run dev",
        "lint": "turbo run lint",
        "typecheck": "turbo run typecheck",
        "test": "turbo run test",
        "clean": "turbo run clean && rm -rf node_modules",
        "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md,yml,yaml}\""
    },
    "devDependencies": {
        "turbo": "^2.3.0",
        "prettier": "^3.3.0",
        "@types/node": "^20.14.0"
    }
}, indent=2) + "\n")

w("pnpm-workspace.yaml", '''
packages:
  - "apps/nextjs-dashboard"
  - "packages/*"
  - "tools/*"
''')

w("turbo.json", json.dumps({
    "$schema": "https://turbo.build/schema.json",
    "globalDependencies": ["**/.env.*"],
    "globalEnv": [
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "NEXT_PUBLIC_PYTHON_BACKEND_URL",
        "PYTHON_BACKEND_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "REDIS_URL",
        "NATS_URL",
        "SENTRY_DSN",
        "OPENAI_API_KEY"
    ],
    "tasks": {
        "build": {
            "dependsOn": ["^build"],
            "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
        },
        "dev": {"cache": False, "persistent": True},
        "lint": {"dependsOn": ["^build"]},
        "typecheck": {"dependsOn": ["^build"]},
        "test": {"dependsOn": ["^build"], "outputs": ["coverage/**"]},
        "clean": {"cache": False}
    }
}, indent=2) + "\n")

w("pyproject.toml", '''
[project]
name = "athena-x"
version = "0.1.0"
description = "Institutional-grade quantitative intelligence terminal"
requires-python = ">=3.11"

[tool.uv.workspace]
members = [
    "apps/python-backend",
    "agents/*/*",
    "engines/*",
    "providers/*",
    "runtime/*",
    "tools/*",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
''')

w(".gitignore", '''
# Dependencies
node_modules/
.pnp
.pnp.js
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.uv/

# Build outputs
dist/
build/
.next/
out/
*.tsbuildinfo
.turbo/

# Testing
coverage/
.coverage
htmlcov/
.pytest_cache/
.playwright/

# Environment
.env
.env.local
.env.*.local
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
npm-debug.log*
pnpm-debug.log*
python-*.log

# Database
*.sqlite
*.db
supabase/.branches
supabase/.temp

# Model artifacts
*.onnx
*.pt
*.pth
*.ckpt
models/cache/

# Secrets
secrets/
*.pem
*.key
''')

w(".editorconfig", '''
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
''')

w(".env.example", '''
# ============================================================================
# ATHENA-X Environment Variables
# ============================================================================

# --- Supabase ---
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# --- Python Backend ---
PYTHON_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_PYTHON_BACKEND_URL=http://localhost:8000

# --- Event Bus ---
REDIS_URL=redis://localhost:6379
NATS_URL=nats://localhost:4222

# --- Market Data Providers (failover chain order) ---
YAHOO_API_KEY=
FINNHUB_API_KEY=
POLYGON_API_KEY=
FLASHALPHA_API_KEY=
FRED_API_KEY=
ALPHA_VANTAGE_API_KEY=

# --- AI / ML ---
GPU_DEVICE=cuda:0
MODEL_REGISTRY_PATH=./models
ONNX_CACHE_PATH=./.cache/onnx

# --- Observability ---
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=

# --- Feature Flags ---
ENABLE_AUTOMATION=false
ENABLE_SELF_CORRECTION=true
''')

# ============================================================================
# PACKAGES/
# ============================================================================

w("packages/event-schema/README.md", '''
# @athena-x/event-schema

Single source of truth for all event bus message schemas.

## Architecture

```
schemas/events/*.yaml  ──►  generate-ts.ts  ──►  types.ts (TypeScript)
                      └──►  generate-py.py  ──►  events.py (Pydantic)
```

Both the TypeScript frontend bus and the Python backend bus import generated
types from this package. Never hand-edit the generated files.

## Mandatory event metadata

Every event MUST contain these 8 fields (Change 11 of STEP 2.1):

- `eventId` (UUID)
- `eventType` (string, e.g., `"market:quote-updated"`)
- `timestamp` (ISO 8601 UTC)
- `provider` (string — source provider/agent)
- `latency` (ms — source to bus publish)
- `confidence` (0..1)
- `dataVersion` (semver of payload schema)
- `retryCount` (0 on first publish)
- `agentId` (emitting agent ID)
- `processingTime` (ms the agent spent producing this)

## Usage

```typescript
import type { BusEvent, MarketQuoteUpdated } from '@athena-x/event-schema';
```

```python
from athena_x_event_schema import BusEvent, MarketQuoteUpdated
```
''')

w("packages/event-schema/package.json", json.dumps({
    "name": "@athena-x/event-schema",
    "version": "0.1.0",
    "private": True,
    "type": "module",
    "main": "./dist/index.js",
    "types": "./dist/index.d.ts",
    "scripts": {
        "build": "tsc",
        "generate": "tsx scripts/generate.ts",
        "lint": "eslint src/",
        "typecheck": "tsc --noEmit",
        "test": "vitest run"
    },
    "devDependencies": {
        "typescript": "^5.6.0",
        "tsx": "^4.19.0",
        "yaml": "^2.6.0",
        "vitest": "^2.1.0",
        "zod": "^3.23.0"
    }
}, indent=2) + "\n")

w("packages/event-schema/src/index.ts", '''
// Auto-generated. Run `pnpm generate` to regenerate.
// Source: schemas/events/*.yaml

export type EventBusVersion = "1.0.0";

export interface BusEventMeta {
  eventId: string;
  eventType: string;
  timestamp: string;
  provider: string;
  latency: number;
  confidence: number;
  dataVersion: string;
  retryCount: number;
  agentId: string;
  processingTime: number;
}

export interface BusEvent<T = unknown> extends BusEventMeta {
  payload: T;
}

export type EventNamespace =
  | "market"
  | "ta"
  | "options"
  | "news"
  | "macro"
  | "cross_market"
  | "decision"
  | "forecast"
  | "probability"
  | "supervisor"
  | "validator"
  | "learning"
  | "report"
  | "ui"
  | "system";

export type EventBusPattern = string;
''')

w("packages/event-schema/src/tsconfig.json", json.dumps({
    "extends": "../../configs/shared/tsconfig.base.json",
    "compilerOptions": {
        "outDir": "./dist",
        "rootDir": "./src"
    },
    "include": ["src/**/*"]
}, indent=2) + "\n")

w("packages/ui-kit/README.md", '''
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
''')

w("packages/ui-kit/package.json", json.dumps({
    "name": "@athena-x/ui-kit",
    "version": "0.1.0",
    "private": True,
    "type": "module",
    "main": "./dist/index.js",
    "module": "./dist/index.js",
    "types": "./dist/index.d.ts",
    "exports": {
        ".": {
            "types": "./dist/index.d.ts",
            "import": "./dist/index.js"
        },
        "./styles.css": "./dist/styles.css"
    },
    "scripts": {
        "build": "tsc && tailwindcss -i src/styles.css -o dist/styles.css",
        "lint": "eslint src/",
        "typecheck": "tsc --noEmit",
        "test": "vitest run"
    },
    "peerDependencies": {
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "next": "^16.0.0"
    },
    "dependencies": {
        "@radix-ui/react-dialog": "^1.1.2",
        "@radix-ui/react-dropdown-menu": "^2.1.2",
        "@radix-ui/react-select": "^2.1.2",
        "@radix-ui/react-slider": "^1.2.1",
        "@radix-ui/react-tabs": "^1.1.1",
        "@radix-ui/react-tooltip": "^1.1.3",
        "class-variance-authority": "^0.7.0",
        "clsx": "^2.1.1",
        "cmdk": "^1.0.0",
        "lucide-react": "^0.454.0",
        "recharts": "^2.13.0",
        "sonner": "^1.5.0",
        "tailwind-merge": "^2.5.0",
        "tailwindcss-animate": "^1.0.7"
    }
}, indent=2) + "\n")

w("packages/ui-kit/src/index.ts", '''
export {};  // STEP 4 will export components.
''')

w("packages/eslint-config/README.md", '''
# @athena-x/eslint-config

Shared ESLint configuration enforcing module boundaries, no circular imports,
no dead code, no hardcoded values, and the **no-calc-in-dashboard** rule.

## Key rules

- `import/no-boundaries` — enforces the module dependency graph
- `import/no-cycle` — no circular imports
- `no-unused-vars` — no dead code (error, not warning)
- `no-constant-binary-expression` — catches dead branches
- `@athena-x/no-calc-in-dashboard` — bans arithmetic in `apps/nextjs-dashboard/**`
  except in approved utility files
- `@athena-x/no-hardcoded-values` — requires config extraction for magic numbers

## Usage

```json
// .eslintrc.json
{
  "extends": "@athena-x/eslint-config"
}
```
''')

w("packages/eslint-config/package.json", json.dumps({
    "name": "@athena-x/eslint-config",
    "version": "0.1.0",
    "private": True,
    "main": "./index.js",
    "files": ["index.js", "rules/", "presets/"],
    "dependencies": {
        "@typescript-eslint/eslint-plugin": "^8.10.0",
        "@typescript-eslint/parser": "^8.10.0",
        "eslint-plugin-import": "^2.31.0",
        "eslint-plugin-react": "^7.37.0",
        "eslint-plugin-react-hooks": "^5.0.0",
        "eslint-plugin-jsx-a11y": "^6.10.0"
    }
}, indent=2) + "\n")

w("packages/eslint-config/index.js", '''
/**
 * Base ESLint config — applied to all TypeScript packages.
 */
module.exports = {
  root: false,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2024,
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  plugins: ['@typescript-eslint', 'import', 'react', 'react-hooks', 'jsx-a11y'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/stylistic',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  settings: {
    react: { version: '19.0' },
    'import/resolver': { typescript: { project: ['./tsconfig.json'] } },
  },
  rules: {
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'error',
    'import/no-cycle': ['error', { maxDepth: 10 }],
    'import/no-deprecated': 'error',
    'import/order': ['warn', {
      groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
      'newlines-between': 'always',
    }],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-constant-condition': 'error',
    'no-dead-code': 'error',
    'no-duplicate-imports': 'error',
    'no-unreachable': 'error',
    'no-unused-private-class-members': 'error',
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
  },
};
''')

w("packages/eslint-config/presets/dashboard.js", '''
/**
 * Dashboard preset — adds the no-calc-in-dashboard rule (Change 15).
 * Applied only to apps/nextjs-dashboard.
 */
module.exports = {
  extends: ['../index.js'],
  rules: {
    '@athena-x/no-calc-in-dashboard': 'error',
  },
  overrides: [
    {
      files: ['lib/utils/**', 'lib/format/**'],
      rules: { '@athena-x/no-calc-in-dashboard': 'off' },
    },
  ],
};
''')

w("packages/eslint-config/rules/no-calc-in-dashboard.js", '''
/**
 * Custom ESLint rule: bans arithmetic and Math.* calls in dashboard components.
 * Dashboard MUST only display, never calculate (Change 15).
 */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ban calculations in dashboard components (Change 15)',
      category: 'ATHENA-X Architectural Rules',
    },
    schema: [],
    messages: {
      noArithmetic: 'Dashboard cannot perform arithmetic ({{op}}). Calculations belong in the Python backend.',
      noMathCall: 'Dashboard cannot call Math.{{fn}}. Calculations belong in the Python backend.',
    },
  },
  create(context) {
    const filename = context.getFilename();
    if (!filename.includes('apps/nextjs-dashboard')) return {};
    return {
      BinaryExpression(node) {
        if (['+', '-', '*', '/', '%', '**'].includes(node.operator)) {
          context.report({ node, messageId: 'noArithmetic', data: { op: node.operator } });
        }
      },
      MemberExpression(node) {
        if (node.object?.name === 'Math') {
          context.report({ node, messageId: 'noMathCall', data: { fn: node.property?.name } });
        }
      },
    };
  },
};
''')

w("packages/tsconfig/README.md", '''
# @athena-x/tsconfig

Shared TypeScript compiler configurations.

## Presets

- `tsconfig.base.json` — strict mode, path aliases, common compiler options
- `tsconfig.nextjs.json` — extends base, adds Next.js-specific options
- `tsconfig.library.json` — extends base, for publishable packages
''')

w("packages/tsconfig/package.json", json.dumps({
    "name": "@athena-x/tsconfig",
    "version": "0.1.0",
    "private": True,
    "files": ["*.json"]
}, indent=2) + "\n")

w("packages/tsconfig/tsconfig.base.json", json.dumps({
    "$schema": "https://json.schemastore.org/tsconfig",
    "compilerOptions": {
        "target": "ES2022",
        "lib": ["ES2022", "DOM", "DOM.Iterable"],
        "module": "ESNext",
        "moduleResolution": "Bundler",
        "jsx": "preserve",
        "strict": True,
        "noImplicitAny": True,
        "noImplicitReturns": True,
        "noFallthroughCasesInSwitch": True,
        "noUncheckedIndexedAccess": True,
        "noImplicitOverride": True,
        "exactOptionalPropertyTypes": True,
        "noPropertyAccessFromIndexSignature": False,
        "allowSyntheticDefaultImports": True,
        "esModuleInterop": True,
        "forceConsistentCasingInFileNames": True,
        "isolatedModules": True,
        "resolveJsonModule": True,
        "skipLibCheck": True,
        "incremental": True,
        "declaration": True,
        "declarationMap": True,
        "sourceMap": True
    }
}, indent=2) + "\n")

w("packages/tsconfig/tsconfig.nextjs.json", json.dumps({
    "$schema": "https://json.schemastore.org/tsconfig",
    "extends": "./tsconfig.base.json",
    "compilerOptions": {
        "plugins": [{ "name": "next" }],
        "paths": {
            "@/*": ["./*"],
            "@athena-x/ui-kit": ["../../packages/ui-kit/src"],
            "@athena-x/event-schema": ["../../packages/event-schema/src"]
        }
    }
}, indent=2) + "\n")

w("packages/tsconfig/tsconfig.library.json", json.dumps({
    "$schema": "https://json.schemastore.org/tsconfig",
    "extends": "./tsconfig.base.json",
    "compilerOptions": {
        "composite": True
    }
}, indent=2) + "\n")

w("packages/types/README.md", '''
# @athena-x/types

Shared TypeScript domain types used across packages and apps.

These types are NOT generated — they represent stable domain concepts
(Symbol, AssetClass, Timeframe, MarketRegime, etc.) that change rarely.

For event payload types, use `@athena-x/event-schema` (generated from YAML).
''')

w("packages/types/package.json", json.dumps({
    "name": "@athena-x/types",
    "version": "0.1.0",
    "private": True,
    "type": "module",
    "main": "./dist/index.js",
    "types": "./dist/index.d.ts",
    "scripts": {
        "build": "tsc",
        "lint": "eslint src/",
        "typecheck": "tsc --noEmit"
    }
}, indent=2) + "\n")

w("packages/types/src/index.ts", '''
// Domain types — stable, hand-curated.

export type Symbol = string;
export type AssetClass = 'equity' | 'etf' | 'index' | 'future' | 'option' | 'currency' | 'commodity' | 'yield' | 'volatility' | 'crypto';
export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1D' | '1W' | '1M';
export type Direction = 'long' | 'short' | 'neutral';
export type SignalStrength = 'weak' | 'moderate' | 'strong';
export type ProviderName = 'yahoo' | 'finnhub' | 'polygon' | 'flashalpha' | 'fred' | 'alphavantage' | 'simulated';
export type MarketRegime =
  | 'trending'
  | 'ranging'
  | 'breakout'
  | 'mean-reversion'
  | 'high-vol'
  | 'low-vol'
  | 'news-driven'
  | 'option-driven'
  | 'dealer-controlled';

export interface Quote {
  symbol: Symbol;
  last: number;
  bid: number;
  ask: number;
  high: number;
  low: number;
  open: number;
  prevClose: number;
  volume: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

export interface Bar {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AgentId {
  readonly agentId: string;
  readonly layer: 'data-collection' | 'raw-intelligence' | 'decision-intelligence' | 'supervisor' | 'validator' | 'self-correction' | 'automation';
  readonly module: string;
  readonly sub: string;
}

export interface Confidence {
  readonly score: number;  // 0..1
  readonly evidence: number;
  readonly sources: number;
  readonly agreement: number;  // 0..1
}

export const MAIN_INDICATORS = ['ES', 'SPY'] as const;
export type MainIndicator = typeof MAIN_INDICATORS[number];
''')

# ============================================================================
# SCHEMAS/
# ============================================================================

w("schemas/README.md", '''
# schemas/

Single source of truth for all ATHENA-X schemas.

## Layout

```
schemas/
├── events/          # Event bus message schemas (YAML → TS + Pydantic)
├── database/        # SQL schemas for the 4 logical databases
├── ai-models/       # AI model input/output schemas (ONNX contract)
└── plugins/         # Plugin manifest schemas
```

## Generation

- Event schemas: `pnpm --filter @athena-x/event-schema generate`
- DB schemas: applied via Supabase migrations in `database/migrations/`
- AI model schemas: validated at model registration time
- Plugin schemas: validated by `engines/plugin-engine/` at load time

## Principles

- YAML for human-editable schemas
- JSON Schema for validation
- OpenAPI for HTTP API contracts
- Pydantic / Zod generated from these sources
- Never hand-write generated files
''')

w("schemas/events/market.yaml", '''
# Market data events — published by agents/data-collection/.
namespace: market
version: 1.0.0

events:
  - name: quote-updated
    description: Real-time quote for a symbol
    payload:
      type: object
      required: [symbol, last, bid, ask, timestamp]
      properties:
        symbol: { type: string }
        last:   { type: number }
        bid:    { type: number }
        ask:    { type: number }
        high:   { type: number }
        low:    { type: number }
        open:   { type: number }
        prevClose: { type: number }
        volume: { type: number }
        change: { type: number }
        changePercent: { type: number }
        timestamp: { type: integer, format: unix-millis }

  - name: trade-printed
    description: Individual trade print
    payload:
      type: object
      required: [symbol, price, size, side, timestamp]
      properties:
        symbol: { type: string }
        price:  { type: number }
        size:   { type: integer }
        side:   { type: string, enum: [buy, sell, unknown] }
        timestamp: { type: integer, format: unix-millis }

  - name: level2-updated
    description: Order book depth update
    payload:
      type: object
      required: [symbol, bids, asks, timestamp]
      properties:
        symbol: { type: string }
        bids:   { type: array, items: { type: array, items: { type: number }, minItems: 2, maxItems: 2 } }
        asks:   { type: array, items: { type: array, items: { type: number }, minItems: 2, maxItems: 2 } }
        timestamp: { type: integer, format: unix-millis }

  - name: bar-closed
    description: OHLCV bar finalized for a timeframe
    payload:
      type: object
      required: [symbol, timeframe, bar]
      properties:
        symbol:    { type: string }
        timeframe: { type: string, enum: [1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1M] }
        bar:       { $ref: "#/components/Bar" }

  - name: provider-failed-over
    description: Provider failover event
    payload:
      type: object
      required: [from, to, reason, timestamp]
      properties:
        from:      { type: string }
        to:        { type: string }
        reason:    { type: string }
        timestamp: { type: integer, format: unix-millis }

components:
  Bar:
    type: object
    required: [timestamp, open, high, low, close, volume]
    properties:
      timestamp: { type: integer, format: unix-millis }
      open:      { type: number }
      high:      { type: number }
      low:       { type: number }
      close:     { type: number }
      volume:    { type: number }
''')

w("schemas/events/ta.yaml", '''
namespace: ta
version: 1.0.0

events:
  - name: indicator-computed
    description: Output of a TA plugin computation (Raw Intelligence)
    payload:
      type: object
      required: [symbol, timeframe, indicator, value]
      properties:
        symbol:     { type: string }
        timeframe:  { type: string }
        indicator:  { type: string }   # e.g., "ema", "rsi", "macd"
        value:      { type: number }
        context:    { type: object, additionalProperties: true }

  - name: signal-emitted
    description: Directional signal from a TA agent (Raw Intelligence)
    payload:
      type: object
      required: [symbol, agentId, direction, strength, weight]
      properties:
        symbol:    { type: string }
        agentId:   { type: string }
        direction: { type: string, enum: [long, short, neutral] }
        strength:  { type: string, enum: [weak, moderate, strong] }
        weight:    { type: number, minimum: 0, maximum: 1 }
        evidence:  { type: array, items: { type: string } }

  - name: level-identified
    description: Support/resistance level
    payload:
      type: object
      required: [symbol, level, type, strength]
      properties:
        symbol:   { type: string }
        level:    { type: number }
        type:     { type: string, enum: [support, resistance] }
        strength: { type: number, minimum: 0, maximum: 1 }
''')

w("schemas/events/options.yaml", '''
namespace: options
version: 1.0.0

events:
  - name: chain-refreshed
    description: Options chain refreshed for a symbol
    payload:
      type: object
      required: [symbol, expiry, chain]
      properties:
        symbol: { type: string }
        expiry: { type: string, format: date }
        chain:  { type: array, items: { $ref: "#/components/OptionRow" } }

  - name: unusual-activity
    payload:
      type: object
      required: [symbol, strike, expiry, type, size, premium]
      properties:
        symbol:  { type: string }
        strike:  { type: number }
        expiry:  { type: string, format: date }
        type:    { type: string, enum: [call, put] }
        size:    { type: integer }
        premium: { type: number }

  - name: iv-updated
    payload:
      type: object
      required: [symbol, iv]
      properties:
        symbol:    { type: string }
        iv:        { type: number }
        ivSkew:    { type: number }
        ivTerm:    { type: object, additionalProperties: { type: number } }

  - name: greeks-computed
    payload:
      type: object
      required: [symbol, strike, expiry, delta, gamma, theta, vega, rho]
      properties:
        symbol: { type: string }
        strike: { type: number }
        expiry: { type: string, format: date }
        delta:  { type: number }
        gamma:  { type: number }
        theta:  { type: number }
        vega:   { type: number }
        rho:    { type: number }

  - name: gamma-exposure-updated
    payload:
      type: object
      required: [symbol, gex, gammaFlip]
      properties:
        symbol:     { type: string }
        gex:        { type: number }
        gammaFlip:  { type: number }

  - name: max-pain-updated
    payload:
      type: object
      required: [symbol, expiry, maxPain]
      properties:
        symbol:   { type: string }
        expiry:   { type: string, format: date }
        maxPain:  { type: number }

components:
  OptionRow:
    type: object
    properties:
      strike:    { type: number }
      callIv:    { type: number }
      callVol:   { type: integer }
      callOi:    { type: integer }
      callDelta: { type: number }
      putIv:     { type: number }
      putVol:    { type: integer }
      putOi:     { type: integer }
      putDelta:  { type: number }
''')

w("schemas/events/news.yaml", '''
namespace: news
version: 1.0.0

events:
  - name: headline-received
    payload:
      type: object
      required: [id, headline, source, timestamp]
      properties:
        id:       { type: string }
        headline: { type: string }
        source:   { type: string }
        url:      { type: string }
        timestamp: { type: integer, format: unix-millis }
        symbols:  { type: array, items: { type: string } }
        category: { type: string, enum: [earnings, analyst, regulatory, macro, product, mna, geopolitical] }

  - name: sentiment-scored
    payload:
      type: object
      required: [id, sentiment, score, model]
      properties:
        id:        { type: string }
        sentiment: { type: string, enum: [positive, neutral, negative] }
        score:     { type: number, minimum: -1, maximum: 1 }
        model:     { type: string }

  - name: impact-classified
    payload:
      type: object
      required: [id, impact, confidence]
      properties:
        id:         { type: string }
        impact:     { type: integer, minimum: 0, maximum: 100 }
        confidence: { type: number, minimum: 0, maximum: 1 }

  - name: entity-mentioned
    payload:
      type: object
      required: [entity, type, count]
      properties:
        entity: { type: string }
        type:   { type: string }
        count:  { type: integer }
''')

w("schemas/events/macro.yaml", '''
namespace: macro
version: 1.0.0

events:
  - name: indicator-released
    payload:
      type: object
      required: [indicator, region, value, previous, surprise]
      properties:
        indicator: { type: string }
        region:    { type: string, enum: [US, EU, CN, JP, UK, Global] }
        freq:      { type: string, enum: [Daily, Weekly, Monthly, Quarterly] }
        value:     { type: number }
        previous:  { type: number }
        surprise:  { type: number }

  - name: yield-curve-updated
    payload:
      type: object
      required: [points]
      properties:
        points: { type: array, items: { type: object, properties: { tenor: {type: string}, yield: {type: number} } } }

  - name: fx-rate-updated
    payload:
      type: object
      required: [pair, rate, change]
      properties:
        pair:   { type: string }
        rate:   { type: number }
        change: { type: number }

  - name: commodity-updated
    payload:
      type: object
      required: [commodity, price, change]
      properties:
        commodity: { type: string }
        price:     { type: number }
        change:    { type: number }
''')

w("schemas/events/cross-market.yaml", '''
namespace: cross_market
version: 1.0.0

events:
  - name: symbol-state-updated
    description: Per-symbol cross-market state
    payload:
      type: object
      required: [symbol, state]
      properties:
        symbol: { type: string, enum: [SPY, SPX, ES, QQQ, NQ, IWM, DIA, SOXX, VIX, VVIX, MOVE, DXY, TNX, Gold, Oil, Copper, USDJPY, Europe, Asia, Crypto] }
        state:  { type: object, additionalProperties: true }

  - name: spy-intelligence-updated
    description: Aggregated SPY intelligence from all cross-market agents
    payload:
      type: object
      required: [summary, components]
      properties:
        summary:   { type: string }
        components: { type: array, items: { type: object, properties: { source: {type: string}, contribution: {type: number} } } }
''')

w("schemas/events/decision.yaml", '''
namespace: decision
version: 1.0.0

events:
  - name: regime-classified
    description: Market regime classification (prerequisite for all decisions)
    payload:
      type: object
      required: [symbol, regime, confidence, evidence]
      properties:
        symbol:    { type: string }
        regime:    { type: string, enum: [trending, ranging, breakout, mean-reversion, high-vol, low-vol, news-driven, option-driven, dealer-controlled] }
        confidence: { type: number, minimum: 0, maximum: 1 }
        evidence:  { type: array, items: { type: string } }

  - name: timeframe-alignment-updated
    description: Multi-timeframe alignment score
    payload:
      type: object
      required: [symbol, alignmentScore, breakdown]
      properties:
        symbol:         { type: string }
        alignmentScore: { type: number, minimum: 0, maximum: 100 }
        breakdown:      { type: object, additionalProperties: { type: string, enum: [bullish, bearish, neutral] } }

  - name: scenario-updated
    description: Bull/Base/Bear scenario probabilities
    payload:
      type: object
      required: [symbol, bull, base, bear]
      properties:
        symbol: { type: string }
        bull:   { type: number, minimum: 0, maximum: 1 }
        base:   { type: number, minimum: 0, maximum: 1 }
        bear:   { type: number, minimum: 0, maximum: 1 }

  - name: volatility-projected
    payload:
      type: object
      required: [symbol, projectedVol, horizon]
      properties:
        symbol:      { type: string }
        projectedVol: { type: number }
        horizon:     { type: string }

  - name: expected-move-updated
    payload:
      type: object
      required: [symbol, expectedMove, horizon, confidence]
      properties:
        symbol:       { type: string }
        expectedMove: { type: number }
        horizon:      { type: string }
        confidence:   { type: number }

  - name: probability-tree-updated
    payload:
      type: object
      required: [symbol, tree]
      properties:
        symbol: { type: string }
        tree:   { type: object, additionalProperties: true }

  - name: ai-consensus-updated
    description: Aggregate AI consensus across all decision agents
    payload:
      type: object
      required: [symbol, consensus, agreement]
      properties:
        symbol:    { type: string }
        consensus: { type: string, enum: [bullish, bearish, neutral] }
        agreement: { type: number, minimum: 0, maximum: 1 }
        components: { type: array, items: { type: object } }
''')

w("schemas/events/forecast.yaml", '''
namespace: forecast
version: 1.0.0

events:
  - name: trajectory-computed
    description: Price forecast trajectory from an AI model
    payload:
      type: object
      required: [symbol, modelId, horizon, points]
      properties:
        symbol:   { type: string }
        modelId:  { type: string, enum: [lstm, transformer, tabpfn, xgboost, catboost, lightgbm-large, lightgbm-small, random-forest, logistic] }
        runtime:  { type: string, enum: [python-gpu, browser-onnx] }
        horizon:  { type: string }
        points:   { type: array, items: { type: object, properties: { t: {type: integer}, price: {type: number}, confidence: {type: number} } } }
        inferenceTimeMs: { type: number }

  - name: catalyst-detected
    payload:
      type: object
      required: [symbol, catalyst, impact]
      properties:
        symbol:   { type: string }
        catalyst: { type: string }
        impact:   { type: number }

  - name: rerun-requested
    description: UI → backend, request forecast re-run
    payload:
      type: object
      required: [symbol, config]
      properties:
        symbol: { type: string }
        config: { type: object, additionalProperties: true }
''')

w("schemas/events/probability.yaml", '''
namespace: probability
version: 1.0.0

events:
  - name: simulation-run
    payload:
      type: object
      required: [symbol, config, stats]
      properties:
        symbol: { type: string }
        config: { type: object, additionalProperties: true }
        stats:  { type: object, additionalProperties: true }
        paths:  { type: array, items: { type: array, items: { type: number } } }

  - name: profit-scored
    payload:
      type: object
      required: [symbol, strategy, probability, expectedValue]
      properties:
        symbol:       { type: string }
        strategy:     { type: string }
        probability:  { type: number, minimum: 0, maximum: 1 }
        expectedValue: { type: number }

  - name: strategy-matrix-updated
    payload:
      type: object
      required: [symbol, matrix]
      properties:
        symbol: { type: string }
        matrix: { type: array, items: { type: object } }
''')

w("schemas/events/supervisor.yaml", '''
namespace: supervisor
version: 1.0.0

events:
  - name: conflict-detected
    description: Two or more agents disagree
    payload:
      type: object
      required: [symbol, agents, description]
      properties:
        symbol:      { type: string }
        agents:      { type: array, items: { type: string } }
        description: { type: string }
        severity:    { type: string, enum: [low, medium, high] }

  - name: agent-failing
    payload:
      type: object
      required: [agentId, reason, lastSeenAt]
      properties:
        agentId:    { type: string }
        reason:     { type: string }
        lastSeenAt: { type: integer, format: unix-millis }

  - name: retry-requested
    payload:
      type: object
      required: [agentId, retryCount]
      properties:
        agentId:    { type: string }
        retryCount: { type: integer }

  - name: confidence-adjusted
    description: Supervisor adjusted an agent's confidence weighting
    payload:
      type: object
      required: [agentId, oldWeight, newWeight, reason]
      properties:
        agentId:   { type: string }
        oldWeight: { type: number }
        newWeight: { type: number }
        reason:    { type: string }
''')

w("schemas/events/validator.yaml", '''
namespace: validator
version: 1.0.0

events:
  - name: report-approved
    description: Report passed Institutional Validation Layer
    payload:
      type: object
      required: [reportId, score, checks]
      properties:
        reportId: { type: string }
        score:    { type: number }
        checks:   { type: object, additionalProperties: true }

  - name: report-rejected
    payload:
      type: object
      required: [reportId, failedChecks, reason]
      properties:
        reportId:    { type: string }
        failedChecks: { type: array, items: { type: string } }
        reason:      { type: string }

  - name: backtest-run
    payload:
      type: object
      required: [strategyId, config, results]
      properties:
        strategyId: { type: string }
        config:     { type: object, additionalProperties: true }
        results:    { type: object, additionalProperties: true }

  - name: calibration-updated
    payload:
      type: object
      required: [model, buckets]
      properties:
        model:   { type: string }
        buckets: { type: array, items: { type: object } }
''')

w("schemas/events/learning.yaml", '''
namespace: learning
version: 1.0.0

events:
  - name: prediction-scored
    description: A prediction was compared to actual outcome and scored
    payload:
      type: object
      required: [modelId, predictionId, predicted, actual, error]
      properties:
        modelId:       { type: string }
        predictionId:  { type: string }
        predicted:     { type: number }
        actual:        { type: number }
        error:         { type: number }
        absoluteError: { type: number }

  - name: weight-adjusted
    description: Self-correction engine adjusted a model's weight
    payload:
      type: object
      required: [modelId, oldWeight, newWeight, reason]
      properties:
        modelId:   { type: string }
        oldWeight: { type: number }
        newWeight: { type: number }
        reason:    { type: string }
        evidence:  { type: array, items: { type: string } }
''')

w("schemas/events/report.yaml", '''
namespace: report
version: 1.0.0

events:
  - name: generation-started
    payload:
      type: object
      required: [reportId, config]
      properties:
        reportId: { type: string }
        config:   { type: object, additionalProperties: true }

  - name: generation-completed
    payload:
      type: object
      required: [reportId, markdown, jsonContent, pdfPath]
      properties:
        reportId:    { type: string }
        markdown:    { type: string }
        jsonContent: { type: object }
        pdfPath:     { type: string }

  - name: exported
    payload:
      type: object
      required: [reportId, format, url]
      properties:
        reportId: { type: string }
        format:   { type: string, enum: [markdown, json, pdf] }
        url:      { type: string }

  - name: stored
    payload:
      type: object
      required: [reportId, storagePath]
      properties:
        reportId:    { type: string }
        storagePath: { type: string }
''')

w("schemas/events/ui.yaml", '''
namespace: ui
version: 1.0.0

events:
  - name: symbol-selected
    payload:
      type: object
      required: [symbol, source]
      properties:
        symbol: { type: string }
        source: { type: string, enum: [sidebar, palette, chart, watchlist, ticker] }

  - name: module-launched
    payload:
      type: object
      required: [moduleId, instanceId, config]
      properties:
        moduleId:    { type: string }
        instanceId:  { type: string }
        config:      { type: object, additionalProperties: true }

  - name: module-closed
    payload:
      type: object
      required: [instanceId]
      properties:
        instanceId: { type: string }

  - name: main-indicator-switched
    description: ES ⇄ SPY switch (Change 2.2)
    payload:
      type: object
      required: [indicator]
      properties:
        indicator: { type: string, enum: [ES, SPY] }

  - name: layout-updated
    payload:
      type: object
      required: [workspaceId, layout]
      properties:
        workspaceId: { type: string }
        layout:      { type: object, additionalProperties: true }
''')

w("schemas/events/system.yaml", '''
namespace: system
version: 1.0.0

events:
  - name: agent-started
    payload:
      type: object
      required: [agentId, moduleId, version]
      properties:
        agentId:  { type: string }
        moduleId: { type: string }
        version:  { type: string }

  - name: agent-stopped
    payload:
      type: object
      required: [agentId]
      properties:
        agentId: { type: string }
        reason:  { type: string }

  - name: agent-heartbeat
    description: Periodic health heartbeat from an agent
    payload:
      type: object
      required: [agentId, timestamp, metrics]
      properties:
        agentId:   { type: string }
        timestamp: { type: integer, format: unix-millis }
        metrics:
          type: object
          required: [running, cpu, memory, queueLength, errorCount, restartCount, confidence]
          properties:
            running:       { type: boolean }
            lastUpdate:    { type: integer, format: unix-millis }
            cpu:           { type: number }
            memory:        { type: number }
            apiLatency:    { type: number }
            queueLength:   { type: integer }
            errorCount:    { type: integer }
            restartCount:  { type: integer }
            confidence:    { type: number }
            version:       { type: string }

  - name: bus-connected
    payload:
      type: object
      required: [transport]
      properties:
        transport: { type: string, enum: [websocket, redis, nats] }

  - name: bus-disconnected
    payload:
      type: object
      required: [reason]
      properties:
        reason: { type: string }

  - name: provider-health-updated
    description: Provider health for Data Quality Dashboard (Change 18)
    payload:
      type: object
      required: [provider, status]
      properties:
        provider:        { type: string }
        status:          { type: string, enum: [connected, disconnected, degraded] }
        delay:           { type: number }
        missingBars:     { type: integer }
        missingTicks:    { type: integer }
        apiErrors:       { type: integer }
        failoverCount:   { type: integer }
        freshness:       { type: number }
        reliabilityScore: { type: number, minimum: 0, maximum: 1 }
''')

# AI model schemas
w("schemas/ai-models/README.md", '''
# AI Model Schemas

Input/output contracts for every AI model in the registry.

Used by:
- `engines/ai-runtime/` — to validate inference requests/responses
- `engines/onnx-runtime/` — to validate browser-runnable models
- `engines/learning-engine/` — to score predictions against outcomes

## Routing table (non-overridable)

| Model ID | Runtime | Location |
|---|---|---|
| `lstm` | python-gpu | Python backend (PyTorch) |
| `transformer` | python-gpu | Python backend (PyTorch) |
| `tabpfn` | python-gpu | Python backend |
| `xgboost` | python-gpu | Python backend |
| `catboost` | python-gpu | Python backend |
| `lightgbm-large` | python-gpu | Python backend |
| `lightgbm-small` | browser-onnx | Frontend (onnxruntime-web) |
| `random-forest` | browser-onnx | Frontend (onnxruntime-web) |
| `logistic` | browser-onnx | Frontend (onnxruntime-web) |

**LSTM and Transformer NEVER run in the browser.**
''')

# Plugin manifest schema
w("schemas/plugins/manifest.schema.json", json.dumps({
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ATHENA-X Plugin Manifest",
    "type": "object",
    "required": ["id", "name", "version", "type", "runtime"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z]+\\.[a-z-]+$"},
        "name": {"type": "string"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "type": {"type": "string", "enum": ["indicator", "options", "pattern", "dark-pool"]},
        "runtime": {"type": "string", "enum": ["python", "typescript", "wasm"]},
        "description": {"type": "string"},
        "author": {"type": "string"},
        "license": {"type": "string"},
        "inputs": {"type": "array", "items": {"type": "string"}},
        "params": {"type": "object"},
        "outputs": {"type": "array", "items": {"type": "string"}},
        "dependencies": {"type": "array", "items": {"type": "string"}}
    }
}, indent=2) + "\n")

# ============================================================================
# DATABASE/
# ============================================================================

w("database/README.md", '''
# database/

Four logical databases (Change 14). Implemented as four Postgres schemas
in a single Supabase instance for dev/staging, optionally separate clusters
in production.

## Layout

```
database/
├── raw-market-data/         # Schema: raw_market_data — untouched provider output
├── processed-market-data/   # Schema: processed_market_data — normalized + validated
├── ai-intelligence/         # Schema: ai_intelligence — agent outputs, predictions, weights
├── historical-reports/      # Schema: historical_reports — reports + backtests
├── migrations/              # Supabase migrations (timestamped)
├── seeds/                   # Dev seed data
└── policies/                # Row-level security policies
```

## Writer access (enforced by RLS)

| Schema | Writer |
|---|---|
| `raw_market_data` | `collection-agent` only (service role) |
| `processed_market_data` | `standardization-agent` only (service role) |
| `ai_intelligence` | Each agent writes only to its own tables |
| `historical_reports` | `report-engine` + `validator-engine` |

Reader access is open to all authenticated users (subject to user RLS).
''')

w("database/raw-market-data/schema.sql", '''
-- ============================================================================
-- Database 1: raw_market_data
-- Untouched provider output. Writer: collection-agent only.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS raw_market_data;

-- Provider quotes as received
CREATE TABLE IF NOT EXISTS raw_market_data.quotes (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingest_id       UUID NOT NULL
);
CREATE INDEX idx_raw_quotes_symbol_time ON raw_market_data.quotes (symbol, received_at DESC);
CREATE INDEX idx_raw_quotes_provider   ON raw_market_data.quotes (provider, received_at DESC);

-- Raw bars
CREATE TABLE IF NOT EXISTS raw_market_data.bars (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    provider        TEXT NOT NULL,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_raw_bars_lookup ON raw_market_data.bars (symbol, timeframe, received_at DESC);

-- Raw trades
CREATE TABLE IF NOT EXISTS raw_market_data.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    payload         JSONB,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw news (before NLP processing)
CREATE TABLE IF NOT EXISTS raw_market_data.news (
    id              UUID PRIMARY KEY,
    symbol          TEXT,
    provider        TEXT NOT NULL,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload         JSONB
);

-- Raw provider call log (for data quality dashboard)
CREATE TABLE IF NOT EXISTS raw_market_data.provider_calls (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    status_code     INTEGER,
    latency_ms      INTEGER,
    error           TEXT,
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_provider_calls_time ON raw_market_data.provider_calls (provider, called_at DESC);
''')

w("database/processed-market-data/schema.sql", '''
-- ============================================================================
-- Database 2: processed_market_data
-- Normalized, deduplicated, validated. Writer: standardization-agent only.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS processed_market_data;

-- Canonical quotes (post-validation, post-dedup)
CREATE TABLE IF NOT EXISTS processed_market_data.quotes (
    symbol          TEXT NOT NULL,
    last            NUMERIC NOT NULL,
    bid             NUMERIC,
    ask             NUMERIC,
    high            NUMERIC,
    low             NUMERIC,
    open            NUMERIC,
    prev_close      NUMERIC,
    volume          BIGINT,
    change          NUMERIC,
    change_percent  NUMERIC,
    quality_score   NUMERIC NOT NULL,  -- 0..1 from validation-agent
    source_count    INTEGER NOT NULL,  -- how many providers contributed
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol)
);

-- Canonical OHLCV bars
CREATE TABLE IF NOT EXISTS processed_market_data.bars (
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    timestamp       BIGINT NOT NULL,  -- unix-millis
    open            NUMERIC NOT NULL,
    high            NUMERIC NOT NULL,
    low             NUMERIC NOT NULL,
    close           NUMERIC NOT NULL,
    volume          BIGINT NOT NULL,
    quality_score   NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, timeframe, timestamp)
);

-- Canonical trades
CREATE TABLE IF NOT EXISTS processed_market_data.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    timestamp       BIGINT NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trades_symbol_time ON processed_market_data.trades (symbol, timestamp DESC);

-- Canonical options chains
CREATE TABLE IF NOT EXISTS processed_market_data.option_chains (
    symbol          TEXT NOT NULL,
    expiry          DATE NOT NULL,
    chain           JSONB NOT NULL,
    quality_score   NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, expiry)
);

-- Canonical news (post-NLP)
CREATE TABLE IF NOT EXISTS processed_market_data.news (
    id              UUID PRIMARY KEY,
    symbol          TEXT,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    source          TEXT NOT NULL,
    category        TEXT,
    sentiment       TEXT,
    sentiment_score NUMERIC,
    impact          INTEGER,
    published_at    TIMESTAMPTZ,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_symbol_time ON processed_market_data.news (symbol, published_at DESC);

-- Data quality log
CREATE TABLE IF NOT EXISTS processed_market_data.data_quality (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    quality_score   NUMERIC NOT NULL,
    issues          JSONB,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_quality_lookup ON processed_market_data.data_quality (symbol, checked_at DESC);
''')

w("database/ai-intelligence/schema.sql", '''
-- ============================================================================
-- Database 3: ai_intelligence
-- Agent outputs, predictions, signals, weights. Each agent owns its tables.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_intelligence;

-- Technical Analysis signals (one row per agent×symbol×timeframe)
CREATE TABLE IF NOT EXISTS ai_intelligence.ta_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,    -- e.g., 'ta.rsi', 'ta.macd'
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    direction       TEXT NOT NULL,    -- long|short|neutral
    strength        TEXT NOT NULL,    -- weak|moderate|strong
    weight          NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ta_signals_lookup ON ai_intelligence.ta_signals (agent_id, symbol, emitted_at DESC);

-- Options Intelligence signals
CREATE TABLE IF NOT EXISTS ai_intelligence.options_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,    -- greeks|iv|skew|gamma|max-pain|...
    value           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_options_signals_lookup ON ai_intelligence.options_signals (agent_id, symbol, emitted_at DESC);

-- News signals
CREATE TABLE IF NOT EXISTS ai_intelligence.news_signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    sentiment       TEXT NOT NULL,
    impact          INTEGER NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Macro signals
CREATE TABLE IF NOT EXISTS ai_intelligence.macro_signals (
    id              BIGSERIAL PRIMARY KEY,
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    trend           TEXT,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cross-market signals (per instrument)
CREATE TABLE IF NOT EXISTS ai_intelligence.cross_market_signals (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Market regime classifications
CREATE TABLE IF NOT EXISTS ai_intelligence.regimes (
    symbol          TEXT NOT NULL,
    regime          TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    classified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, classified_at)
);
CREATE INDEX idx_regimes_lookup ON ai_intelligence.regimes (symbol, classified_at DESC);

-- Forecasts (per model run)
CREATE TABLE IF NOT EXISTS ai_intelligence.forecasts (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    runtime         TEXT NOT NULL,    -- python-gpu|browser-onnx
    horizon         TEXT NOT NULL,
    trajectory      JSONB NOT NULL,   -- array of {t, price, confidence}
    inference_ms    INTEGER NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_forecasts_lookup ON ai_intelligence.forecasts (symbol, model_id, created_at DESC);

-- Probability simulations
CREATE TABLE IF NOT EXISTS ai_intelligence.simulations (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    stats           JSONB NOT NULL,
    paths           JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model weight table (managed by self-correction-engine)
CREATE TABLE IF NOT EXISTS ai_intelligence.model_weights (
    model_id        TEXT PRIMARY KEY,
    weight          NUMERIC NOT NULL,
    accuracy_7d     NUMERIC,
    accuracy_30d    NUMERIC,
    sample_count    INTEGER NOT NULL DEFAULT 0,
    last_adjusted_at TIMESTAMPTZ,
    last_adjustment_reason TEXT
);

-- Agent health history (for Agent Health Dashboard, Change 17)
CREATE TABLE IF NOT EXISTS ai_intelligence.agent_health (
    agent_id        TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    running         BOOLEAN NOT NULL,
    cpu             NUMERIC,
    memory          NUMERIC,
    api_latency     NUMERIC,
    queue_length    INTEGER,
    error_count     INTEGER,
    restart_count   INTEGER,
    confidence      NUMERIC,
    version         TEXT,
    PRIMARY KEY (agent_id, timestamp)
);

-- Prediction scoring (self-correction)
CREATE TABLE IF NOT EXISTS ai_intelligence.prediction_scores (
    id              BIGSERIAL PRIMARY KEY,
    model_id        TEXT NOT NULL,
    prediction_id   UUID NOT NULL,
    symbol          TEXT NOT NULL,
    predicted       NUMERIC NOT NULL,
    actual          NUMERIC NOT NULL,
    error           NUMERIC NOT NULL,
    absolute_error  NUMERIC NOT NULL,
    scored_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_prediction_scores_model ON ai_intelligence.prediction_scores (model_id, scored_at DESC);

-- Supervisor decisions log
CREATE TABLE IF NOT EXISTS ai_intelligence.supervisor_decisions (
    id              BIGSERIAL PRIMARY KEY,
    decision_type   TEXT NOT NULL,    -- conflict-detected|agent-failing|retry-requested|confidence-adjusted
    agent_id        TEXT,
    symbol          TEXT,
    payload         JSONB NOT NULL,
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
''')

w("database/historical-reports/schema.sql", '''
-- ============================================================================
-- Database 4: historical_reports
-- Generated reports + backtests. Writers: report-engine, validator-engine.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS historical_reports;

-- Generated reports (4 artifacts: markdown + json + pdf + storage path)
CREATE TABLE IF NOT EXISTS historical_reports.reports (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    title           TEXT NOT NULL,
    audience        TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    sections        JSONB NOT NULL,
    markdown        TEXT NOT NULL,                  -- canonical format
    json_content    JSONB NOT NULL,                 -- structured
    pdf_path        TEXT NOT NULL,                  -- Supabase Storage path
    status          TEXT NOT NULL DEFAULT 'generating',  -- generating|completed|approved|rejected
    validation_score NUMERIC,
    validation_checks JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_reports_user_time ON historical_reports.reports (user_id, created_at DESC);
CREATE INDEX idx_reports_symbol    ON historical_reports.reports (symbol, created_at DESC);

-- Backtests (real vectorbt results)
CREATE TABLE IF NOT EXISTS historical_reports.backtests (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    strategy_id     TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    equity_curve    JSONB NOT NULL,
    trade_history   JSONB NOT NULL,
    metrics         JSONB NOT NULL,    -- { returns, sharpe, sortino, max_dd, calmar, win_rate, ... }
    calibration     JSONB,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running'
);
CREATE INDEX idx_backtests_user_time ON historical_reports.backtests (user_id, started_at DESC);

-- User workspaces (per-user, workspace-aware — Change 7 of original STEP 2)
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    main_indicator  TEXT NOT NULL DEFAULT 'SPY' CHECK (main_indicator IN ('ES', 'SPY')),
    panel_layout    JSONB NOT NULL DEFAULT '[]'::jsonb,
    background_services JSONB NOT NULL DEFAULT '[]'::jsonb,
    settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.watchlists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    asset_class     TEXT NOT NULL,
    position        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app.module_instances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    module_id       TEXT NOT NULL,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    state           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model registry (AI model artifacts, browser-onnx + python-gpu)
CREATE TABLE IF NOT EXISTS ai_intelligence.model_artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        TEXT NOT NULL,
    version         TEXT NOT NULL,
    runtime         TEXT NOT NULL,    -- python-gpu|browser-onnx
    storage_path    TEXT NOT NULL,
    input_schema    JSONB NOT NULL,
    output_schema   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_id, version)
);
''')

w("database/migrations/20260101000000_init_schemas.sql", '''
-- ATHENA-X initial migration — creates all four schemas + app schema.
-- Run order: this file first, then the four schema files in dependency order:
--   1. raw-market-data/schema.sql
--   2. processed-market-data/schema.sql
--   3. ai-intelligence/schema.sql
--   4. historical-reports/schema.sql

CREATE SCHEMA IF NOT EXISTS raw_market_data;
CREATE SCHEMA IF NOT EXISTS processed_market_data;
CREATE SCHEMA IF NOT EXISTS ai_intelligence;
CREATE SCHEMA IF NOT EXISTS historical_reports;
CREATE SCHEMA IF NOT EXISTS app;

COMMENT ON SCHEMA raw_market_data IS 'Untouched provider output. Writer: collection-agent only.';
COMMENT ON SCHEMA processed_market_data IS 'Normalized + validated market data. Writer: standardization-agent only.';
COMMENT ON SCHEMA ai_intelligence IS 'Agent outputs, predictions, signals, weights. Each agent owns its tables.';
COMMENT ON SCHEMA historical_reports IS 'Generated reports + backtests. Writers: report-engine, validator-engine.';
COMMENT ON SCHEMA app IS 'User-facing app data: workspaces, watchlists, module instances.';
''')

w("database/policies/rls.sql", '''
-- ============================================================================
-- Row-Level Security policies
-- ============================================================================

-- User-owned tables (workspaces, watchlists, module_instances, reports, backtests)
ALTER TABLE app.workspaces        ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.watchlists        ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.module_instances  ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_reports.reports  ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_reports.backtests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own workspaces" ON app.workspaces
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "users own watchlists" ON app.watchlists
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));

CREATE POLICY "users own module_instances" ON app.module_instances
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));

CREATE POLICY "users own reports" ON historical_reports.reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "users own backtests" ON historical_reports.backtests
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Read-only access to market data and AI intelligence for authenticated users
CREATE POLICY "authenticated read raw_market_data" ON raw_market_data.quotes
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read processed_market_data" ON processed_market_data.quotes
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read ai_intelligence" ON ai_intelligence.ta_signals
    FOR SELECT TO authenticated USING (true);

-- Service role bypasses RLS (for backend agents)
-- (Supabase service role automatically bypasses RLS by default.)
''')

w("database/seeds/dev_symbols.sql", '''
-- Dev seed data: default watchlist symbols
INSERT INTO app.workspaces (user_id, name, main_indicator)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default', 'SPY')
ON CONFLICT DO NOTHING;

INSERT INTO app.watchlists (workspace_id, symbol, asset_class, position) VALUES
    ('00000000-0000-0000-0000-000000000000', 'NVDA', 'equity', 1),
    ('00000000-0000-0000-0000-000000000000', 'AAPL', 'equity', 2),
    ('00000000-0000-0000-0000-000000000000', 'MSFT', 'equity', 3),
    ('00000000-0000-0000-0000-000000000000', 'TSLA', 'equity', 4),
    ('00000000-0000-0000-0000-000000000000', 'SPY',  'etf',    5),
    ('00000000-0000-0000-0000-000000000000', 'QQQ',  'etf',    6)
ON CONFLICT DO NOTHING;
''')

# ============================================================================
# RUNTIME/
# ============================================================================

w("runtime/README.md", '''
# runtime/

Cross-cutting infrastructure shared by all agents and engines.

## Modules

| Module | Purpose |
|---|---|
| `event-bus/` | Typed pub/sub bus (Python + TypeScript mirrors) |
| `message-queue/` | Job queue (Redis Streams or NATS JetStream) |
| `scheduler/` | Cron + on-demand task scheduling |
| `health-monitor/` | Agent + provider health aggregation (Changes 17, 18) |
| `logger/` | Structured logger (Pino TS + Pio Py) |
| `metrics/` | Prometheus metrics exporter |
| `tracing/` | OpenTelemetry instrumentation |
| `di/` | Dependency injection container |

All modules are Python packages (used by the backend) with TypeScript
mirrors where needed (event-bus, logger — used by the frontend).
''')

w("runtime/event-bus/README.md", '''
# runtime/event-bus

Central nervous system of ATHENA-X. Every cross-agent and cross-module
communication flows through this bus.

## Topology

```
Frontend bus (TS, in-process)
       ↕ WebSocket bridge
Backend bus (Python, Redis Pub/Sub + NATS)
```

## Event metadata (mandatory — Change 11)

Every event MUST contain: eventId, eventType, timestamp, provider,
latency, confidence, dataVersion, retryCount, agentId, processingTime.

Events missing any field are rejected at the bus boundary.

## Usage (Python)

```python
from runtime.event_bus import BusClient, BusEvent

bus = BusClient(redis_url=..., nats_url=...)

await bus.publish(BusEvent(
    event_id=uuid4(),
    event_type="market:quote-updated",
    timestamp=datetime.utcnow().isoformat(),
    provider="yahoo",
    latency=12,
    confidence=0.98,
    data_version="1.0.0",
    retry_count=0,
    agent_id="data-collection.collection",
    processing_time=8,
    payload={"symbol": "NVDA", "last": 128.45, ...},
))

async def handler(event: BusEvent):
    ...

await bus.subscribe("market:quote-updated", handler)
```

## Usage (TypeScript — frontend mirror)

```typescript
import { useBusSubscription, publish } from '@athena-x/event-bus-browser';

useBusSubscription('market:quote-updated', (event) => {
  // update Zustand store
});
```
''')

w("runtime/event-bus/pyproject.toml", '''
[project]
name = "athena-x-runtime-event-bus"
version = "0.1.0"
description = "Central typed pub/sub bus for ATHENA-X"
requires-python = ">=3.11"
dependencies = [
    "redis>=5.0.0",
    "nats-py>=2.7.0",
    "pydantic>=2.9.0",
    "structlog>=24.4.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_event_bus"]
''')

w("runtime/event-bus/src/athena_x_runtime_event_bus/__init__.py", '''
"""ATHENA-X runtime event bus."""
__version__ = "0.1.0"
''')

w("runtime/event-bus/src/athena_x_runtime_event_bus/types.py", '''
"""Bus event types. Mirrors @athena-x/event-schema TypeScript types."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class BusEvent(BaseModel):
    """Canonical bus event. All 10 metadata fields are required (Change 11)."""
    event_id: UUID = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    timestamp: datetime
    provider: str
    latency: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    data_version: str = Field(alias="dataVersion")
    retry_count: int = Field(ge=0, alias="retryCount")
    agent_id: str = Field(alias="agentId")
    processing_time: int = Field(ge=0, alias="processingTime")
    payload: Any

    model_config = {"populate_by_name": True}


class BusClient:
    """Abstract bus client. Implementations: RedisBusClient, NATSBusClient."""

    async def publish(self, event: BusEvent) -> None:
        raise NotImplementedError

    async def subscribe(self, pattern: str, handler) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError
''')

w("runtime/event-bus/src/athena_x_runtime_event_bus/redis_client.py", '''
"""Redis Pub/Sub implementation of BusClient."""
from __future__ import annotations
import json
from typing import Awaitable, Callable
import redis.asyncio as redis
from .types import BusEvent, BusClient


class RedisBusClient(BusClient):
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._pubsub: redis.Redis | None = None
        self._handlers: dict[str, list[Callable[[BusEvent], Awaitable[None]]]] = {}

    async def connect(self) -> None:
        self._pubsub = redis.from_url(self._redis_url)

    async def publish(self, event: BusEvent) -> None:
        if self._pubsub is None:
            raise RuntimeError("Bus not connected")
        channel = event.event_type
        await self._pubsub.publish(channel, event.model_dump_json())

    async def subscribe(self, pattern: str, handler) -> None:
        if self._pubsub is None:
            raise RuntimeError("Bus not connected")
        self._handlers.setdefault(pattern, []).append(handler)
        await self._pubsub.psubscribe(pattern)

    async def close(self) -> None:
        if self._pubsub is not None:
            await self._pubsub.close()
            self._pubsub = None
''')

w("runtime/event-bus/tests/__init__.py", '')
w("runtime/event-bus/tests/test_types.py", '''
"""Tests for event-bus type validation."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from athena_x_runtime_event_bus.types import BusEvent


def test_bus_event_validates_all_required_fields():
    """An event missing any of the 10 metadata fields MUST be rejected."""
    event = BusEvent(
        eventId=uuid4(),
        eventType="market:quote-updated",
        timestamp=datetime.now(timezone.utc),
        provider="yahoo",
        latency=10,
        confidence=0.95,
        dataVersion="1.0.0",
        retryCount=0,
        agentId="data-collection.collection",
        processingTime=5,
        payload={"symbol": "NVDA", "last": 128.45},
    )
    assert event.event_type == "market:quote-updated"


def test_bus_event_rejects_missing_metadata():
    with pytest.raises(Exception):
        BusEvent(
            eventId=uuid4(),
            eventType="market:quote-updated",
            timestamp=datetime.now(timezone.utc),
            provider="yahoo",
            # missing: latency, confidence, dataVersion, retryCount, agentId, processingTime
            payload={},
        )
''')

# Logger
w("runtime/logger/pyproject.toml", '''
[project]
name = "athena-x-runtime-logger"
version = "0.1.0"
description = "Structured logger for ATHENA-X"
requires-python = ">=3.11"
dependencies = ["structlog>=24.4.0", "python-json-logger>=2.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_logger"]
''')

w("runtime/logger/src/athena_x_runtime_logger/__init__.py", '''
"""Structured logger."""
from __future__ import annotations
import structlog


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger bound to the given name (usually agent_id)."""
    return structlog.get_logger(name)


__all__ = ["get_logger"]
''')

# Health monitor
w("runtime/health-monitor/pyproject.toml", '''
[project]
name = "athena-x-runtime-health-monitor"
version = "0.1.0"
description = "Agent and provider health monitoring (Changes 17, 18)"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.9.0", "redis>=5.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_health_monitor"]
''')

w("runtime/health-monitor/src/athena_x_runtime_health_monitor/__init__.py", '''
"""Agent health monitoring (Change 17) and provider data quality (Change 18)."""
__version__ = "0.1.0"
''')

w("runtime/health-monitor/src/athena_x_runtime_health_monitor/types.py", '''
"""Health metrics types."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class AgentHealth(BaseModel):
    """Change 17 — every AI agent exposes these 10 metrics."""
    agent_id: str = Field(alias="agentId")
    running: bool
    last_update: datetime | None = Field(default=None, alias="lastUpdate")
    cpu: float = Field(ge=0.0, le=100.0)
    memory: float = Field(ge=0.0)  # MB
    api_latency: float = Field(ge=0.0, alias="apiLatency")  # ms
    queue_length: int = Field(ge=0, alias="queueLength")
    error_count: int = Field(ge=0, alias="errorCount")
    restart_count: int = Field(ge=0, alias="restartCount")
    confidence: float = Field(ge=0.0, le=1.0)
    version: str

    model_config = {"populate_by_name": True}


class ProviderHealth(BaseModel):
    """Change 18 — every provider exposes these 8 metrics."""
    provider: str
    connection: str  # connected|disconnected|degraded
    delay: float = Field(ge=0.0)  # ms
    missing_bars: int = Field(ge=0, alias="missingBars")
    missing_ticks: int = Field(ge=0, alias="missingTicks")
    api_errors: int = Field(ge=0, alias="apiErrors")
    failover_count: int = Field(ge=0, alias="failoverCount")
    freshness: float = Field(ge=0.0)  # ms
    reliability_score: float = Field(ge=0.0, le=1.0, alias="reliabilityScore")

    model_config = {"populate_by_name": True}
''')

# Scheduler
w("runtime/scheduler/pyproject.toml", '''
[project]
name = "athena-x-runtime-scheduler"
version = "0.1.0"
description = "Cron + on-demand task scheduling"
requires-python = ">=3.11"
dependencies = ["apscheduler>=3.10.0", "redis>=5.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_scheduler"]
''')

w("runtime/scheduler/src/athena_x_runtime_scheduler/__init__.py", '''"""Task scheduler."""''')

# Message queue
w("runtime/message-queue/pyproject.toml", '''
[project]
name = "athena-x-runtime-message-queue"
version = "0.1.0"
description = "Job queue (Redis Streams or NATS JetStream)"
requires-python = ">=3.11"
dependencies = ["redis>=5.0.0", "nats-py>=2.7.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_message_queue"]
''')

w("runtime/message-queue/src/athena_x_runtime_message_queue/__init__.py", '''"""Message queue."""''')

# Metrics
w("runtime/metrics/pyproject.toml", '''
[project]
name = "athena-x-runtime-metrics"
version = "0.1.0"
description = "Prometheus metrics exporter"
requires-python = ">=3.11"
dependencies = ["prometheus-client>=0.21.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_metrics"]
''')

w("runtime/metrics/src/athena_x_runtime_metrics/__init__.py", '''"""Prometheus metrics."""''')

# Tracing
w("runtime/tracing/pyproject.toml", '''
[project]
name = "athena-x-runtime-tracing"
version = "0.1.0"
description = "OpenTelemetry instrumentation"
requires-python = ">=3.11"
dependencies = ["opentelemetry-api>=1.27.0", "opentelemetry-sdk>=1.27.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_tracing"]
''')

w("runtime/tracing/src/athena_x_runtime_tracing/__init__.py", '''"""OpenTelemetry tracing."""''')

# DI container
w("runtime/di/pyproject.toml", '''
[project]
name = "athena-x-runtime-di"
version = "0.1.0"
description = "Dependency injection container"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_di"]
''')

w("runtime/di/src/athena_x_runtime_di/__init__.py", '''"""Dependency injection."""''')

# ============================================================================
# CONFIGS/
# ============================================================================

w("configs/shared/tsconfig.base.json", json.dumps({
    "$schema": "https://json.schemastore.org/tsconfig",
    "extends": "../../packages/tsconfig/tsconfig.base.json"
}, indent=2) + "\n")

w("configs/development/env.yaml", '''
# Development environment configuration
environment: development
debug: true

supabase:
  url: http://localhost:54321
  anon_key: dev-anon-key
  service_role_key: dev-service-role-key

redis:
  url: redis://localhost:6379

nats:
  url: nats://localhost:4222

python_backend:
  url: http://localhost:8000

providers:
  failover_chain: [yahoo, finnhub, polygon, flashalpha, fred, alphavantage]
  cache_ttl_seconds: 5

ai_runtime:
  gpu_device: cpu  # use CPU in dev
  onnx_cache_path: ./.cache/onnx

feature_flags:
  enable_automation: false
  enable_self_correction: true
  enable_backtesting: true
''')

w("configs/production/env.yaml", '''
# Production environment configuration
environment: production
debug: false

supabase:
  url: ${SUPABASE_URL}
  anon_key: ${SUPABASE_ANON_KEY}
  service_role_key: ${SUPABASE_SERVICE_ROLE_KEY}

redis:
  url: ${REDIS_URL}

nats:
  url: ${NATS_URL}

python_backend:
  url: ${PYTHON_BACKEND_URL}

providers:
  failover_chain: [yahoo, finnhub, polygon, flashalpha, fred, alphavantage]
  cache_ttl_seconds: 1

ai_runtime:
  gpu_device: ${GPU_DEVICE}
  onnx_cache_path: /var/cache/athena-x/onnx

feature_flags:
  enable_automation: false  # disabled until Change 16 is implemented
  enable_self_correction: true
  enable_backtesting: true
''')

w("configs/staging/env.yaml", '''
# Staging environment configuration
environment: staging
debug: false

supabase:
  url: ${SUPABASE_URL}
  anon_key: ${SUPABASE_ANON_KEY}
  service_role_key: ${SUPABASE_SERVICE_ROLE_KEY}

redis:
  url: ${REDIS_URL}

nats:
  url: ${NATS_URL}

python_backend:
  url: ${PYTHON_BACKEND_URL}

providers:
  failover_chain: [yahoo, finnhub, polygon, flashalpha, fred, alphavantage]
  cache_ttl_seconds: 2

ai_runtime:
  gpu_device: ${GPU_DEVICE}
  onnx_cache_path: /var/cache/athena-x/onnx

feature_flags:
  enable_automation: false
  enable_self_correction: true
  enable_backtesting: true
''')

print(f"\n✅ Part 1 complete: {FILES_WRITTEN} files written under {ROOT}")
