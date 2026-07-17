#!/usr/bin/env python3
"""
ATHENA-X Monorepo Skeleton Generator — STEP 3, Part 3
======================================================
Generates: apps/, docs/, tests/, scripts/, tools/, .github/
"""

from pathlib import Path
import json
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)

FILES_WRITTEN = 0

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    global FILES_WRITTEN
    FILES_WRITTEN += 1

# ============================================================================
# APPS/  (nextjs-dashboard + python-backend)
# ============================================================================

w("apps/README.md", '''
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
''')

# === Next.js Dashboard ===
w("apps/nextjs-dashboard/README.md", '''
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
''')

w("apps/nextjs-dashboard/package.json", json.dumps({
    "name": "@athena-x/dashboard",
    "version": "0.1.0",
    "private": True,
    "type": "module",
    "scripts": {
        "dev": "next dev --turbopack",
        "build": "next build --turbopack",
        "start": "next start",
        "lint": "next lint",
        "typecheck": "tsc --noEmit",
        "test": "vitest run",
        "test:e2e": "playwright test",
        "clean": "rm -rf .next .turbo node_modules"
    },
    "dependencies": {
        "@athena-x/event-schema": "workspace:*",
        "@athena-x/types": "workspace:*",
        "@athena-x/ui-kit": "workspace:*",
        "@radix-ui/react-dialog": "^1.1.2",
        "@radix-ui/react-dropdown-menu": "^2.1.2",
        "@radix-ui/react-select": "^2.1.2",
        "@radix-ui/react-slider": "^1.2.1",
        "@radix-ui/react-tabs": "^1.1.1",
        "@radix-ui/react-tooltip": "^1.1.3",
        "@supabase/ssr": "^0.5.2",
        "@supabase/supabase-js": "^2.45.0",
        "@tanstack/react-query": "^5.59.0",
        "class-variance-authority": "^0.7.0",
        "clsx": "^2.1.1",
        "cmdk": "^1.0.0",
        "framer-motion": "^11.11.0",
        "geist": "^1.3.0",
        "lucide-react": "^0.454.0",
        "next": "^16.0.0",
        "next-themes": "^0.3.0",
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "recharts": "^2.13.0",
        "sonner": "^1.5.0",
        "tailwind-merge": "^2.5.0",
        "tailwindcss-animate": "^1.0.7",
        "zod": "^3.23.0",
        "zustand": "^5.0.0",
        "zundo": "^2.1.0"
    },
    "devDependencies": {
        "@playwright/test": "^1.48.0",
        "@testing-library/react": "^16.0.0",
        "@testing-library/jest-dom": "^6.5.0",
        "@types/node": "^20.14.0",
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "@vitejs/plugin-react": "^4.3.0",
        "eslint": "^9.12.0",
        "eslint-config-next": "^16.0.0",
        "jsdom": "^25.0.0",
        "tailwindcss": "^4.0.0",
        "typescript": "^5.6.0",
        "vitest": "^2.1.0"
    }
}, indent=2) + "\n")

w("apps/nextjs-dashboard/tsconfig.json", json.dumps({
    "extends": "../../packages/tsconfig/tsconfig.nextjs.json",
    "compilerOptions": {
        "plugins": [{"name": "next"}],
        "paths": {
            "@/*": ["./src/*"],
            "@athena-x/ui-kit": ["../../packages/ui-kit/src"],
            "@athena-x/event-schema": ["../../packages/event-schema/src"],
            "@athena-x/types": ["../../packages/types/src"]
        },
        "incremental": True,
        "noEmit": True
    },
    "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
    "exclude": ["node_modules"]
}, indent=2) + "\n")

w("apps/nextjs-dashboard/next.config.ts", '''
import type { NextConfig } from 'next';

const config: NextConfig = {
    turbopack: {
        transpilePackages: ['@athena-x/ui-kit', '@athena-x/event-schema', '@athena-x/types'],
    },
    webpack: (cfg) => {
        cfg.externals = cfg.externals || [];
        return cfg;
    },
    experimental: {
        serverActions: { bodySizeLimit: '10mb' },
    },
};

export default config;
''')

w("apps/nextjs-dashboard/tailwind.config.ts", '''
import type { Config } from 'tailwindcss';

const config: Config = {
    darkMode: 'class',  // forced dark — Change 8 of STEP 2.1
    content: [
        './src/**/*.{ts,tsx}',
        '../../packages/ui-kit/src/**/*.{ts,tsx}',
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
                mono: ['var(--font-geist-mono)', 'monospace'],
            },
            colors: {
                background: 'rgb(var(--background) / <alpha-value>)',
                foreground: 'rgb(var(--foreground) / <alpha-value>)',
                card: 'rgb(var(--card) / <alpha-value>)',
                muted: 'rgb(var(--muted) / <alpha-value>)',
                border: 'rgb(var(--border) / <alpha-value>)',
                primary: 'rgb(var(--primary) / <alpha-value>)',
                pos: 'rgb(var(--pos) / <alpha-value>)',
                neg: 'rgb(var(--neg) / <alpha-value>)',
                accent: 'rgb(var(--accent) / <alpha-value>)',
                sidebar: 'rgb(var(--sidebar) / <alpha-value>)',
            },
            animation: {
                'ticker': 'ticker-scroll 40s linear infinite',
                'pulse-dot': 'pulse-dot 1.6s ease-in-out infinite',
            },
        },
    },
    plugins: [require('tailwindcss-animate')],
};

export default config;
''')

w("apps/nextjs-dashboard/src/app/globals.css", '''
@import 'tailwindcss';

@theme {
    --color-background: oklch(1.97% 0 0);
    --color-foreground: oklch(95.36% 0 0);
    --color-card: oklch(5.24% 0 0);
    --color-muted: oklch(9.49% 0 0);
    --color-border: oklch(100% 0 0 / 0.08);
    --color-primary: oklch(69.89% 0 0);
    --color-pos: oklch(69.89% 0 0);     /* institutional green */
    --color-neg: oklch(57.02% 0 0);     /* institutional red */
    --color-accent: oklch(69.89% 0 0);
    --color-sidebar: oklch(1.18% 0 0);
    --font-sans: var(--font-geist-sans), system-ui, sans-serif;
    --font-mono: var(--font-geist-mono), monospace;
}

@layer base {
    html { color-scheme: dark; }
    body {
        @apply bg-background text-foreground antialiased;
        font-feature-settings: 'tnum' on;
    }
}

/* Custom utilities (kept from STEP 1) */
.grid-bg {
    background-image: linear-gradient(oklch(100% 0 0 / 0.03) 1px, transparent 1px),
                      linear-gradient(90deg, oklch(100% 0 0 / 0.03) 1px, transparent 1px);
    background-size: 32px 32px;
}

.scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: oklch(100% 0 0 / 0.15) transparent;
}
.scrollbar-thin::-webkit-scrollbar { width: 6px; height: 6px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: oklch(100% 0 0 / 0.15);
    border-radius: 3px;
}

@keyframes ticker-scroll {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.6; transform: scale(0.85); }
}
''')

w("apps/nextjs-dashboard/src/app/layout.tsx", '''
import type { Metadata } from 'next';
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import './globals.css';

export const metadata: Metadata = {
    title: 'ATHENA-X — Quantitative Intelligence Terminal',
    description: 'Institutional-grade quantitative market intelligence terminal.',
    authors: [{ name: 'ATHENA-X' }],
    keywords: ['ATHENA-X', 'quantitative', 'market intelligence', 'trading terminal'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className={`dark ${GeistSans.variable} ${GeistMono.variable}`} suppressHydrationWarning>
            <body className="font-sans">
                {children}
            </body>
        </html>
    );
}
''')

w("apps/nextjs-dashboard/src/app/page.tsx", '''
import { redirect } from 'next/navigation';

export default function RootPage() {
    redirect('/workspace/default');
}
''')

w("apps/nextjs-dashboard/src/app/workspace/[workspaceId]/layout.tsx", '''
// WorkspaceShell — mounts sidebar, topbar, command palette, toaster.
// Implementation in STEP 4 (Dashboard/UI stage).
export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
}
''')

w("apps/nextjs-dashboard/src/app/workspace/[workspaceId]/page.tsx", '''
// WorkspaceCanvas — renders the panel grid + active module instances.
// Implementation in STEP 4 (Dashboard/UI stage).
export default function WorkspacePage({ params }: { params: Promise<{ workspaceId: string }> }) {
    return <div>Workspace — implementation in STEP 4</div>;
}
''')

w("apps/nextjs-dashboard/src/app/auth/login/page.tsx", '''
// Login page — Supabase Auth.
// Implementation in STEP 4.
export default function LoginPage() {
    return <div>Login — STEP 4</div>;
}
''')

w("apps/nextjs-dashboard/src/app/auth/callback/route.ts", '''
// OAuth callback handler.
// Implementation in STEP 4.
export async function GET(request: Request) {
    return new Response('OK');
}
''')

w("apps/nextjs-dashboard/src/lib/README.md", '''
# Dashboard lib

Shared infrastructure for the Next.js dashboard.

## Subdirectories

| Dir | Purpose |
|---|---|
| `event-bus/` | Frontend bus + WebSocket bridge to backend bus |
| `module-registry/` | Bloomberg-style module catalog + loader |
| `workspace/` | Zustand workspace store (panels, layout, persistence) |
| `module-instance/` | Per-instance Zustand slices |
| `market-data/` | TanStack Query hooks for backend market data API |
| `ai-runtime/` | ONNX Runtime Web loader + router |
| `supabase/` | Supabase browser + server clients |
| `auth/` | AuthProvider, hooks, route guards |
| `di/` | DI container |
| `config/` | Zod-validated env |
| `logger/` | Pino browser logger |
| `keyboard/` | Bloomberg-style shortcuts + cmdk palette |
| `utils/` | Pure helpers (format, time) — these are the ONLY files allowed to do arithmetic |
''')

# Create empty index.ts for lib subdirs to make them valid TS packages
LIB_DIRS = ['event-bus', 'module-registry', 'workspace', 'module-instance',
            'market-data', 'ai-runtime', 'supabase', 'auth', 'di', 'config',
            'logger', 'keyboard', 'utils']

for d in LIB_DIRS:
    w(f"apps/nextjs-dashboard/src/lib/{d}/index.ts", f'''// {d} — implementation in STEP 4
export {{}};
''')

# Stub the module-registry contract so module manifests can type-check
w("apps/nextjs-dashboard/src/lib/module-registry/contract.ts", '''
/**
 * ModuleManifest — the canonical contract every dashboard module implements.
 * Full implementation in STEP 4.
 */
export interface ModuleCapabilities {
    launchable: boolean;
    multiInstance: boolean;
    headless: boolean;
    defaultHotkey: string;
}

export interface ModuleManifest {
    id: string;
    name: string;
    shortcut: string;
    description: string;
    version: string;
    capabilities: ModuleCapabilities;
    configSchema: unknown | null;
    instanceStateSchema: unknown | null;
    subscriptions: string[];
    publications: string[];
    publicAPI: Record<string, unknown>;
    panelComponent: React.ComponentType<unknown> | null;
    agentFactory: (() => unknown) | null;
}
''')

# Stub for module-instance store
w("apps/nextjs-dashboard/src/lib/module-instance/store.ts", '''
/**
 * Per-instance Zustand store. Each module instance (panel) gets its own slice
 * keyed by instanceId. Implementation in STEP 4.
 */
export {};
''')

# Stub for workspace store
w("apps/nextjs-dashboard/src/lib/workspace/store.ts", '''
/**
 * Workspace Zustand store. Single source of truth for the active workspace's
 * panel layout and module instances. Implementation in STEP 4.
 */
export {};
''')

# Modules (10 Bloomberg-style + 2 system)
MODULES = [
    ("dashboard", "DASH", "Dashboard", "Composite workspace view"),
    ("live-market", "MKT", "Live Market Data", "Real-time market data ingestion display"),
    ("technical-analysis", "TA", "Technical Analysis", "23 TA agents + indicator matrix"),
    ("news-intelligence", "NEWS", "News Intelligence", "News feed + sentiment + entity analysis"),
    ("options-intelligence", "OPT", "Options Intelligence", "15 options agents + chain + IV surface"),
    ("macro-intelligence", "MACRO", "Macro Intelligence", "Macro indicators + yield curve + FX + commodities"),
    ("market-intelligence", "MI", "Market Intelligence", "Forecast + Scenario + Regime + Volatility + Expected Move + Prob Tree + Consensus"),
    ("probability-engine", "PROB", "Probability Engine", "Monte Carlo + PoP + strategy matrix"),
    ("report-generator", "RPT", "Report Generator", "Multi-format report generation"),
    ("self-validation", "VAL", "Self Validation", "Real backtesting + model performance audit"),
    ("agent-health", "HEALTH", "Agent Health Dashboard", "Change 17 — live monitoring of all AI agents"),
    ("data-quality", "QUALITY", "Data Quality Dashboard", "Change 18 — per-provider health metrics"),
]

for slug, shortcut, name, desc in MODULES:
    base = f"apps/nextjs-dashboard/src/modules/{slug}"
    # camelCase variable name (e.g., "technical-analysis" -> "technicalAnalysis")
    parts = slug.split('-')
    manifest_var = parts[0] + ''.join(p.title() for p in parts[1:])
    w(f"{base}/README.md", f'''
# {name} Module

> Bloomberg shortcut: `{shortcut}`
> {desc}

## Implementation status

- [x] Module scaffold
- [ ] Implementation (STEP 4)

## Module structure (per STEP 2 contract)

```
modules/{slug}/
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
''')

    w(f"{base}/manifest.ts", f'''
/**
 * {name} Module Manifest
 */
import type {{ ModuleManifest }} from '@/lib/module-registry/contract';

export const {manifest_var}Manifest: ModuleManifest = {{
    id: '{slug}',
    name: '{name}',
    shortcut: '{shortcut}',
    description: '{desc}',
    version: '0.1.0',
    capabilities: {{
        launchable: true,
        multiInstance: false,
        headless: false,
        defaultHotkey: '',
    }},
    configSchema: null,  // STEP 4
    instanceStateSchema: null,  // STEP 4
    subscriptions: [],
    publications: [],
    publicAPI: {{}},  // STEP 4
    panelComponent: null,  // STEP 4
    agentFactory: null,
}};
''')

    w(f"{base}/index.ts", f'''// Public façade for {name} module.
// STEP 4 will export manifest, types, hooks, and the panel component.
export {{ {manifest_var}Manifest }} from './manifest';
''')

    w(f"{base}/components/.gitkeep", '')
    w(f"{base}/services/.gitkeep", '')
    w(f"{base}/tests/.gitkeep", '')

# Vitest config
w("apps/nextjs-dashboard/vitest.config.ts", '''
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
    plugins: [react()],
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./vitest.setup.ts'],
        include: ['src/**/*.test.{ts,tsx}'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html'],
            exclude: ['node_modules/', '.next/'],
        },
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, './src'),
        },
    },
});
''')

w("apps/nextjs-dashboard/vitest.setup.ts", '''
import '@testing-library/jest-dom/vitest';
''')

w("apps/nextjs-dashboard/playwright.config.ts", '''
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    reporter: 'html',
    use: {
        baseURL: 'http://localhost:3000',
        trace: 'on-first-retry',
    },
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
    webServer: {
        command: 'pnpm dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
    },
});
''')

w("apps/nextjs-dashboard/tests/e2e/.gitkeep", '')
w("apps/nextjs-dashboard/next-env.d.ts", '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n')
w("apps/nextjs-dashboard/.eslintrc.json", json.dumps({
    "extends": ["next/core-web-vitals", "@athena-x/eslint-config/presets/dashboard"],
    "rules": {}
}, indent=2) + "\n")

# === Python Backend ===
w("apps/python-backend/README.md", '''
# ATHENA-X Python Backend (FastAPI)

> All AI, agents, calculations, and data processing live here.

## Architecture

```
FastAPI app
├── api/                # HTTP routers
├── ws/                 # WebSocket bridge (frontend bus ↔ backend bus)
├── services/           # Business logic — uses agents/engines
└── main.py             # App entry + lifespan
```

## Endpoints

### Data
- `GET  /market/quote/{symbol}`
- `GET  /market/bars/{symbol}?timeframe=1m&count=100`
- `GET  /market/level2/{symbol}`
- `GET  /market/providers` — provider chain + health (Change 18)

### TA
- `GET  /ta/indicators/{symbol}?timeframe=5m`
- `GET  /ta/signals/{symbol}`
- `GET  /ta/levels/{symbol}`

### Options
- `GET  /options/chain/{symbol}?expiry=2026-01-15`
- `GET  /options/iv/{symbol}`
- `GET  /options/unusual-activity`
- `GET  /options/gamma-exposure/{symbol}`

### News
- `GET  /news/feed?symbol=NVDA&category=earnings`
- `GET  /news/sentiment/{symbol}`

### Macro
- `GET  /macro/indicators?region=US`
- `GET  /macro/yield-curve`

### Cross-Market (Change 8)
- `GET  /cross-market/spy-intelligence`

### Decision Intelligence
- `GET  /decision/regime/{symbol}`
- `GET  /decision/timeframe-alignment/{symbol}`
- `GET  /decision/scenarios/{symbol}`
- `GET  /decision/ai-consensus/{symbol}`

### AI Forecast
- `POST /forecast/run` — body: `{symbol, models: [...], horizon}`
- `GET  /forecast/{symbol}`

### Probability
- `POST /probability/simulate` — body: `{symbol, dte, simulations, threshold}`

### Reports
- `POST /report/generate`
- `GET  /report/{id}`
- `GET  /report` — list

### Self Validation
- `POST /validator/backtest`
- `GET  /validator/result/{id}`
- `GET  /validator/strategies`

### Health (Changes 17, 18)
- `GET  /health/agents` — agent health dashboard data
- `GET  /health/providers` — provider health dashboard data
- `GET  /health/ready`
- `GET  /health/live`

### WebSocket
- `WS   /ws/events` — bus bridge (frontend subscribes to backend events)

## Implementation status

- [x] Project scaffold
- [ ] Routers (STEP 4)
- [ ] WebSocket bridge (STEP 4)
- [ ] Agent supervisors (STEP 4)
''')

w("apps/python-backend/pyproject.toml", '''
[project]
name = "athena-x-backend"
version = "0.1.0"
description = "ATHENA-X Python backend — FastAPI"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.31.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "httpx>=0.27.0",
    "redis>=5.0.0",
    "nats-py>=2.7.0",
    "websockets>=13.0",
    "supabase>=2.7.0",
    "structlog>=24.4.0",
    "prometheus-client>=0.21.0",
    "opentelemetry-api>=1.27.0",
    "opentelemetry-sdk>=1.27.0",
    "athena-x-runtime-event-bus",
    "athena-x-runtime-logger",
    "athena-x-runtime-health-monitor",
    "athena-x-runtime-scheduler",
    "athena-x-runtime-message-queue",
    "athena-x-runtime-metrics",
    "athena-x-runtime-tracing",
    "athena-x-runtime-di",
    "athena-x-engine-data-engine",
    "athena-x-engine-ai-runtime",
    "athena-x-engine-onnx-runtime",
    "athena-x-engine-backtest-engine",
    "athena-x-engine-report-engine",
    "athena-x-engine-plugin-engine",
    "athena-x-engine-learning-engine",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_backend"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("apps/python-backend/src/athena_x_backend/__init__.py", '''"""ATHENA-X FastAPI backend."""\n__version__ = "0.1.0"\n''')

w("apps/python-backend/src/athena_x_backend/main.py", '''
"""FastAPI app entry point."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown lifecycle.

    STEP 4 will:
    - Connect to event bus
    - Start all agents (data-collection → raw-intelligence → decision-intelligence → supervisor)
    - Start health monitor
    - Start scheduler
    """
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ATHENA-X Backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready():
        return {"status": "ready"}

    return app


app = create_app()
''')

w("apps/python-backend/src/athena_x_backend/api/__init__.py", '"""HTTP routers."""\n')
w("apps/python-backend/src/athena_x_backend/api/market.py", '"""GET /market/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/ta.py", '"""GET /ta/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/options.py", '"""GET /options/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/news.py", '"""GET /news/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/macro.py", '"""GET /macro/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/cross_market.py", '"""GET /cross-market/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/decision.py", '"""GET /decision/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/forecast.py", '"""POST /forecast/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/probability.py", '"""POST /probability/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/report.py", '"""POST /report/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/validator.py", '"""POST /validator/* routers. STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/api/health.py", '"""GET /health/* routers (Changes 17, 18). STEP 4."""\n')
w("apps/python-backend/src/athena_x_backend/ws/__init__.py", '"""WebSocket bus bridge."""\n')
w("apps/python-backend/src/athena_x_backend/ws/events.py", '"""WS /ws/events — bridges frontend bus to backend bus. STEP 4."""\n')
w("apps/python-backend/tests/__init__.py", "")
w("apps/python-backend/tests/test_health.py", '''
"""Tests for /health/* endpoints."""
from fastapi.testclient import TestClient
from athena_x_backend.main import app


def test_live_endpoint():
    client = TestClient(app)
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


def test_ready_endpoint():
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
''')

w("apps/python-backend/Dockerfile", '''
FROM python:3.11-slim AS base
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential curl ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace + project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "athena_x_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
''')

# ============================================================================
# DOCS/
# ============================================================================

w("docs/README.md", '''
# docs/

All ATHENA-X documentation.

## Layout

```
docs/
├── architecture/       # STEP 1, 2, 2.1 analyses + diagrams
├── modules/            # per-module deep dives (built in STEP 4)
├── agents/             # per-agent specs
├── plugins/            # per-plugin specs
├── runbooks/           # operational guides
├── api/                # HTTP API reference (auto-generated from OpenAPI)
└── decisions/          # Architecture Decision Records (ADRs)
```
''')

# Copy STEP 1 and STEP 2 docs
import shutil
Path(ROOT / "docs/architecture").mkdir(parents=True, exist_ok=True)
shutil.copy("/home/z/my-project/analysis/STEP-1-ANALYSIS.md",
            ROOT / "docs/architecture/STEP-1-ANALYSIS.md")
shutil.copy("/home/z/my-project/analysis/STEP-2-ARCHITECTURE.md",
            ROOT / "docs/architecture/STEP-2-ARCHITECTURE.md")
shutil.copy("/home/z/my-project/analysis/STEP-2-REVISED.md",
            ROOT / "docs/architecture/STEP-2-REVISED.md")
FILES_WRITTEN += 3

w("docs/architecture/README.md", '''
# Architecture documentation

| Document | Purpose |
|---|---|
| `STEP-1-ANALYSIS.md` | Reverse-engineering of the original Space site |
| `STEP-2-ARCHITECTURE.md` | Initial modular redesign (pre-revisions) |
| `STEP-2-REVISED.md` | The 20 user-approved revisions — authoritative |
| `implementation-order.md` | STEP 4 implementation sequence |
''')

w("docs/architecture/implementation-order.md", '''
# STEP 4 — Implementation Order

The 18-stage sequence (Change 20 of STEP 2.1). Each stage ships with
`tsc --noEmit` + `next lint` + `pytest` + `next build` passing.
Zero errors before proceeding to the next stage.

| # | Stage | Key deliverables |
|---|---|---|
| 1 | Foundation / Core Runtime | event-bus, logger, health-monitor, di, config |
| 2 | Data Collection AI | collection-agent, validation-agent, standardization-agent |
| 3 | Data Validation AI | (covered in stage 2 — listed separately per user spec) |
| 4 | Database Layer | 4 schemas, RLS, migrations, seeds |
| 5 | Event Bus | full bus impl + WebSocket bridge |
| 6 | Technical Analysis Engine | 23 TA agents + 14 indicator plugins |
| 7 | Options Intelligence | 15 options agents + 6 options plugins |
| 8 | Market Intelligence | macro-agent + news-agent + cross-market (20 agents) |
| 9 | Cross-Market Intelligence | spy-intelligence-aggregator |
| 10 | AI Forecast Engine | hybrid AI router (LSTM/Transformer/etc.) |
| 11 | Probability Engine | Monte Carlo |
| 12 | Supervisor AI | conflict detection, retries, confidence weighting |
| 13 | Validation AI | Institutional Validation Layer |
| 14 | Report Engine | markdown → json → pdf → storage |
| 15 | Dashboard / UI | Next.js modules, panels, palette |
| 16 | Self-Correction & Learning | prediction scoring, weight adjustment |
| 17 | Backtesting & Strategy Validation | vectorbt strategies |
| 18 | Performance Optimization | caching, batching, profiling |

## Per-stage quality gates

```bash
# TypeScript
pnpm --filter @athena-x/dashboard typecheck
pnpm --filter @athena-x/dashboard lint
pnpm --filter @athena-x/dashboard test
pnpm --filter @athena-x/dashboard build

# Python
uv run ruff check .
uv run mypy .
uv run pytest
```

All four must pass (zero errors) before the next stage begins.
''')

w("docs/decisions/README.md", '''
# Architecture Decision Records (ADRs)

Format: `NNNN-short-title.md` with the following structure:

```
# ADR-NNNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
Why this decision was needed.

## Decision
What was decided.

## Consequences
What are the implications.
```
''')

w("docs/decisions/0001-modular-bloomberg-style-architecture.md", '''
# ADR-0001: Modular Bloomberg-Style Architecture

## Status
Accepted

## Context
The original Space site was a monolithic tab-switched SPA with no real
backend, no agents, and no persistence. To rebuild as an institutional-grade
terminal, we needed a paradigm shift — from pages to modules.

## Decision
Adopt a Bloomberg-style modular architecture where each module is an
independently launchable, multi-instance, headless-capable unit. Modules
communicate only through a typed event bus. No direct cross-module calls.

## Consequences
- Pros: extreme modularity, plugin extensibility, parallel development
- Cons: more upfront infrastructure, learning curve for new contributors
- Mitigation: comprehensive docs + scaffolding tools
''')

w("docs/decisions/0002-hybrid-ai-runtime.md", '''
# ADR-0002: Hybrid AI Runtime (Browser ONNX + Python GPU)

## Status
Accepted

## Context
Some AI models (LSTM, Transformer) require GPU and cannot run in browser.
Others (small tree ensembles, logistic regression) are trivial and should
run client-side for low latency.

## Decision
Implement a non-overridable routing table:
- LSTM, Transformer, TabPFN, XGBoost, CatBoost, LightGBM-large → Python GPU
- LightGBM-small, Random Forest, Logistic → Browser ONNX (onnxruntime-web)

LSTM and Transformer NEVER run in the browser. This is enforced by code,
not convention.

## Consequences
- Pros: optimal use of compute, predictable performance
- Cons: requires GPU instance for backend, model versioning complexity
- Mitigation: model registry + automated deployment
''')

w("docs/decisions/0003-four-logical-databases.md", '''
# ADR-0003: Four Logical Databases

## Status
Accepted

## Context
The system processes data at different stages: raw provider output,
validated/standardized data, AI intelligence, and historical reports.
Mixing these creates query complexity and risks data contamination.

## Decision
Implement four logical databases (Postgres schemas in Supabase):
- `raw_market_data` — writer: collection-agent only
- `processed_market_data` — writer: standardization-agent only
- `ai_intelligence` — each agent writes only to its own tables
- `historical_reports` — writers: report-engine, validator-engine

Reader access is open to authenticated users (subject to user RLS).

## Consequences
- Pros: clear data lineage, no contamination, audit trail
- Cons: more tables, cross-schema joins needed for some queries
- Mitigation: dedicated views for cross-schema reads
''')

w("docs/decisions/0004-dashboard-never-calculates.md", '''
# ADR-0004: Dashboard Never Calculates

## Status
Accepted

## Context
The original Space site computed everything client-side. This caused
inconsistencies between modules, made the dashboard heavy, and prevented
server-side auditing of calculations.

## Decision
The Next.js dashboard performs ZERO calculations. It only:
- Display, Filter, Search, Layout, User interaction

All calculations happen in the Python backend. The dashboard consumes
results via TanStack Query (for request-response) and bus subscriptions
(for real-time updates).

Enforced by a custom ESLint rule (`@athena-x/no-calc-in-dashboard`) that
bans arithmetic operators and Math.* calls in dashboard components.

## Consequences
- Pros: single source of truth for calculations, auditable, dashboard stays light
- Cons: more network round-trips
- Mitigation: TanStack Query caching + bus subscriptions for real-time
''')

w("docs/decisions/0005-supervisor-governed-agents.md", '''
# ADR-0005: Supervisor-Governed Agents

## Status
Accepted

## Context
With 77+ AI agents running concurrently, conflicts are inevitable
(e.g., TA bullish + News bearish). Without coordination, the system
would produce contradictory outputs.

## Decision
Every agent reports to a Supervisor AI. The Supervisor:
- Detects conflicting signals
- Checks stale data
- Detects failing agents (no heartbeat)
- Triggers retries (max 3, exponential backoff)
- Performs confidence weighting (dynamically adjusted based on accuracy)
- Delegates report generation
- Runs self-learning (adjusts weights from outcomes)
- Tracks performance statistics

## Consequences
- Pros: coherent system behavior, graceful degradation, continuous improvement
- Cons: Supervisor is a single point of failure (mitigated by health monitoring)
- Mitigation: Supervisor itself is supervised by health-monitor + restart policy
''')

w("docs/runbooks/README.md", '''
# Runbooks

Operational guides for common tasks.

| Runbook | When to use |
|---|---|
| `local-dev-setup.md` | Setting up a dev environment |
| `add-new-plugin.md` | Adding a new indicator/options/pattern plugin |
| `add-new-agent.md` | Adding a new AI agent |
| `deploy-backend.md` | Deploying the Python backend |
| `deploy-dashboard.md` | Deploying the Next.js dashboard |
| `run-backtest.md` | Running a strategy backtest |
| `generate-report.md` | Generating an institutional report |
| `troubleshoot-bus.md` | Debugging event bus issues |
''')

w("docs/runbooks/local-dev-setup.md", '''
# Local Dev Setup

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.11+
- uv (Python package manager)
- Docker (for Redis + NATS + Postgres)
- Supabase CLI

## Steps

```bash
# 1. Clone the repo
git clone <repo-url> athena-x
cd athena-x

# 2. Install workspace deps
pnpm install
uv sync

# 3. Start infrastructure (Postgres + Redis + NATS)
docker compose -f infrastructure/docker-compose.yml up -d

# 4. Apply database migrations
supabase db push

# 5. Seed dev data
psql $DATABASE_URL -f database/seeds/dev_symbols.sql

# 6. Copy env file and fill in API keys
cp .env.example .env
# Edit .env with your provider API keys

# 7. Start the backend
cd apps/python-backend
uv run uvicorn athena_x_backend.main:app --reload --port 8000

# 8. In a new terminal, start the dashboard
cd apps/nextjs-dashboard
pnpm dev
```

Dashboard: http://localhost:3000
Backend: http://localhost:8000/docs (Swagger)
''')

w("docs/runbooks/add-new-plugin.md", '''
# Add a New Plugin

```bash
# Scaffold a new indicator plugin
python tools/plugin-scaffolder/scaffold.py indicators my_indicator

# Or an options plugin
python tools/plugin-scaffolder/scaffold.py options my_options_plugin

# Or a pattern plugin
python tools/plugin-scaffolder/scaffold.py patterns my_pattern
```

This generates boilerplate under `plugins/{type}/{slug}/` with:
- README.md
- pyproject.toml
- src/<pkg>/manifest.py
- src/<pkg>/plugin.py
- tests/

Edit `plugin.py` to implement `compute(inputs, params) -> dict`.
The plugin-engine will discover and load it automatically on next restart.
''')

w("docs/runbooks/add-new-agent.md", '''
# Add a New AI Agent

```bash
# Scaffold a new raw-intelligence agent
python tools/agent-scaffolder/scaffold.py raw-intelligence my_agent

# Or a decision-intelligence agent
python tools/agent-scaffolder/scaffold.py decision-intelligence my_agent
```

Then:
1. Edit `manifest.py` to declare subscriptions + publications
2. Edit `agent.py` to implement the agent class
3. Edit `config.py` to add instance config fields
4. Add tests under `tests/`
5. Register the agent in `apps/python-backend/src/athena_x_backend/agent_registry.py` (STEP 4)

The Supervisor will automatically detect and supervise the new agent.
''')

# ============================================================================
# TESTS/
# ============================================================================

w("tests/README.md", '''
# tests/

Cross-cutting tests that span multiple packages/modules.

| Dir | Purpose |
|---|---|
| `e2e/` | End-to-end tests across the full stack |
| `integration/` | Cross-package integration tests |
| `load/` | Performance and load tests |

Per-module and per-package tests live alongside their source code.
''')

w("tests/e2e/.gitkeep", "")
w("tests/integration/.gitkeep", "")
w("tests/load/.gitkeep", "")
w("tests/conftest.py", '"""Shared pytest fixtures for cross-cutting tests."""\n')

# ============================================================================
# SCRIPTS/
# ============================================================================

w("scripts/README.md", '''
# scripts/

Dev/utility scripts. Not part of the deployed application.

| Script | Purpose |
|---|---|
| `setup-dev.sh` | One-shot dev environment setup |
| `generate-schemas.ts` | Regenerate TS + Python event types from YAML |
| `seed-db.py` | Seed dev data into Supabase |
| `run-backtest.py` | CLI to trigger a backtest |
| `deploy.sh` | Deploy frontend + backend |
''')

w("scripts/setup-dev.sh", '''
#!/usr/bin/env bash
set -euo pipefail

echo "=== ATHENA-X Dev Setup ==="

# 1. Check prerequisites
command -v node >/dev/null || { echo "Node.js required"; exit 1; }
command -v pnpm >/dev/null || { echo "pnpm required"; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.11+ required"; exit 1; }
command -v uv >/dev/null || { echo "uv required (pip install uv)"; exit 1; }
command -v docker >/dev/null || { echo "Docker required"; exit 1; }

# 2. Install workspace deps
echo "[1/5] Installing pnpm workspace..."
pnpm install

echo "[2/5] Installing Python workspace..."
uv sync

# 3. Start infrastructure
echo "[3/5] Starting Docker infrastructure..."
docker compose -f infrastructure/docker-compose.yml up -d

# 4. Apply migrations + seeds
echo "[4/5] Applying database migrations..."
supabase db push || echo "Supabase not configured — skipping migrations"

# 5. Copy env
echo "[5/5] Setting up .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit with your API keys"
fi

echo ""
echo "✅ Setup complete. Run:"
echo "  cd apps/python-backend && uv run uvicorn athena_x_backend.main:app --reload"
echo "  cd apps/nextjs-dashboard && pnpm dev"
''')

w("scripts/generate-schemas.ts", '''
#!/usr/bin/env tsx
/**
 * Regenerate TypeScript + Python event types from schemas/events/*.yaml.
 * Run: pnpm --filter @athena-x/event-schema generate
 */
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';

const SCHEMA_DIR = 'schemas/events';
const TS_OUT = 'packages/event-schema/src/generated.ts';
const PY_OUT = 'runtime/event-bus/src/athena_x_runtime_event_bus/generated.py';

function main() {
    const files = readdirSync(SCHEMA_DIR).filter(f => f.endsWith('.yaml'));
    const namespaces: Record<string, any> = {};

    for (const f of files) {
        const content = readFileSync(join(SCHEMA_DIR, f), 'utf8');
        const parsed = parse(content);
        namespaces[parsed.namespace] = parsed;
    }

    // Generate TypeScript
    const ts = generateTypeScript(namespaces);
    writeFileSync(TS_OUT, ts);
    console.log(`✓ Wrote ${TS_OUT}`);

    // Generate Python
    const py = generatePython(namespaces);
    writeFileSync(PY_OUT, py);
    console.log(`✓ Wrote ${PY_OUT}`);
}

function generateTypeScript(ns: Record<string, any>): string {
    return `// AUTO-GENERATED — do not edit. Run: pnpm --filter @athena-x/event-schema generate\n\n` +
        `export const EVENT_NAMESPACES = ${JSON.stringify(Object.keys(ns), null, 2)} as const;\n`;
}

function generatePython(ns: Record<string, any>): string {
    return `# AUTO-GENERATED — do not edit.\n\nEVENT_NAMESPACES = ${JSON.stringify(list(ns.keys()))}\n`;
}

main();
''')

w("scripts/seed-db.py", '''
#!/usr/bin/env python3
"""Seed the development Supabase instance with default data."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "database" / "seeds" / "dev_symbols.sql"

if not SEED_FILE.exists():
    print(f"Seed file not found: {SEED_FILE}")
    sys.exit(1)

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set")
    sys.exit(1)

subprocess.run(["psql", db_url, "-f", str(SEED_FILE)], check=True)
print("✓ Seed data applied")
''')

w("scripts/run-backtest.py", '''
#!/usr/bin/env python3
"""CLI to trigger a backtest via the Python backend."""
import argparse
import httpx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--strategy", default="athena-ensemble")
    p.add_argument("--backend", default="http://localhost:8000")
    args = p.parse_args()

    r = httpx.post(
        f"{args.backend}/validator/backtest",
        json={"symbol": args.symbol, "strategy_id": args.strategy},
        timeout=300,
    )
    r.raise_for_status()
    print(r.json())


if __name__ == "__main__":
    main()
''')

w("scripts/deploy.sh", '''
#!/usr/bin/env bash
set -euo pipefail

echo "=== ATHENA-X Deploy ==="

# 1. Typecheck + lint + test
echo "[1/4] Typecheck + lint + test..."
pnpm typecheck
pnpm lint
pnpm test

# 2. Build frontend
echo "[2/4] Building frontend..."
pnpm --filter @athena-x/dashboard build

# 3. Build backend image
echo "[3/4] Building backend image..."
docker build -t athena-x-backend:latest apps/python-backend/

# 4. Push to registry (skipped in dev)
echo "[4/4] Deploy step — configure your registry in CI"
''')

# Make scripts executable
import os
import stat
for script in ["setup-dev.sh", "deploy.sh"]:
    p = ROOT / "scripts" / script
    if p.exists():
        st = p.stat()
        p.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ============================================================================
# TOOLS/
# ============================================================================

w("tools/README.md", '''
# tools/

Internal tooling. Each tool is a runnable CLI.

| Tool | Purpose |
|---|---|
| `plugin-scaffolder/` | Generates boilerplate for a new plugin |
| `agent-scaffolder/` | Generates boilerplate for a new agent |
| `event-inspector/` | Bus event debugger (subscribes + prints events) |
''')

w("tools/plugin-scaffolder/pyproject.toml", '''
[project]
name = "athena-x-plugin-scaffolder"
version = "0.1.0"
description = "CLI to scaffold new ATHENA-X plugins"
requires-python = ">=3.11"
dependencies = ["click>=8.1.0", "jinja2>=3.1.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_scaffolder"]

[project.scripts]
athena-plugin-scaffold = "athena_x_plugin_scaffolder.cli:main"
''')

w("tools/plugin-scaffolder/src/athena_x_plugin_scaffolder/__init__.py", '"""Plugin scaffolder CLI."""\n')
w("tools/plugin-scaffolder/src/athena_x_plugin_scaffolder/cli.py", '''
"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.argument('plugin_type', type=click.Choice(['indicators', 'options', 'patterns', 'dark-pool']))
@click.argument('slug')
def main(plugin_type: str, slug: str):
    """Scaffold a new plugin."""
    click.echo(f"Scaffolding {plugin_type}/{slug} — implementation in STEP 4")


if __name__ == '__main__':
    main()
''')

w("tools/agent-scaffolder/pyproject.toml", '''
[project]
name = "athena-x-agent-scaffolder"
version = "0.1.0"
description = "CLI to scaffold new ATHENA-X agents"
requires-python = ">=3.11"
dependencies = ["click>=8.1.0", "jinja2>=3.1.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_agent_scaffolder"]

[project.scripts]
athena-agent-scaffold = "athena_x_agent_scaffolder.cli:main"
''')

w("tools/agent-scaffolder/src/athena_x_agent_scaffolder/__init__.py", '"""Agent scaffolder CLI."""\n')
w("tools/agent-scaffolder/src/athena_x_agent_scaffolder/cli.py", '''
"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.argument('layer', type=click.Choice(['data-collection', 'raw-intelligence', 'decision-intelligence', 'supervisor', 'validator', 'self-correction', 'automation']))
@click.argument('slug')
def main(layer: str, slug: str):
    """Scaffold a new agent."""
    click.echo(f"Scaffolding {layer}/{slug} — implementation in STEP 4")


if __name__ == '__main__':
    main()
''')

w("tools/event-inspector/pyproject.toml", '''
[project]
name = "athena-x-event-inspector"
version = "0.1.0"
description = "Bus event debugger — subscribes and prints events"
requires-python = ">=3.11"
dependencies = ["click>=8.1.0", "rich>=13.8.0", "athena-x-runtime-event-bus"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_event_inspector"]

[project.scripts]
athena-bus-inspect = "athena_x_event_inspector.cli:main"
''')

w("tools/event-inspector/src/athena_x_event_inspector/__init__.py", '"""Event inspector CLI."""\n')
w("tools/event-inspector/src/athena_x_event_inspector/cli.py", '''
"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.option('--pattern', default='*', help='Event pattern to subscribe to')
@click.option('--redis-url', default='redis://localhost:6379')
def main(pattern: str, redis_url: str):
    """Inspect bus events."""
    click.echo(f"Subscribing to {pattern} on {redis_url} — implementation in STEP 4")


if __name__ == '__main__':
    main()
''')

# ============================================================================
# .github/workflows/
# ============================================================================

w(".github/workflows/ci-frontend.yml", '''
name: CI Frontend

on:
  push:
    paths: ['apps/nextjs-dashboard/**', 'packages/**']
  pull_request:
    paths: ['apps/nextjs-dashboard/**', 'packages/**']

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter @athena-x/dashboard typecheck
      - run: pnpm --filter @athena-x/dashboard lint
      - run: pnpm --filter @athena-x/dashboard test
      - run: pnpm --filter @athena-x/dashboard build
''')

w(".github/workflows/ci-backend.yml", '''
name: CI Backend

on:
  push:
    paths: ['apps/python-backend/**', 'agents/**', 'engines/**', 'providers/**', 'runtime/**', 'plugins/**']
  pull_request:
    paths: ['apps/python-backend/**', 'agents/**', 'engines/**', 'providers/**', 'runtime/**', 'plugins/**']

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest
''')

w(".github/workflows/ci-plugins.yml", '''
name: CI Plugins

on:
  push:
    paths: ['plugins/**']
  pull_request:
    paths: ['plugins/**']

jobs:
  plugins:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        plugin: [indicators, options, patterns]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run pytest plugins/${{ matrix.plugin }}/
''')

w(".github/workflows/ci-agents.yml", '''
name: CI Agents

on:
  push:
    paths: ['agents/**']
  pull_request:
    paths: ['agents/**']

jobs:
  agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check agents/
      - run: uv run pytest agents/
''')

w(".github/workflows/deploy.yml", '''
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter @athena-x/dashboard build
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}
          NEXT_PUBLIC_PYTHON_BACKEND_URL: ${{ secrets.NEXT_PUBLIC_PYTHON_BACKEND_URL }}
      # Add Vercel deploy step here

  deploy-backend:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v6
        with:
          context: apps/python-backend
          push: false
          tags: athena-x-backend:${{ github.sha }}
''')

# ============================================================================
# Infrastructure (docker-compose)
# ============================================================================

w("infrastructure/README.md", '''
# infrastructure/

Local development infrastructure. Production uses managed services (Supabase Cloud,
Redis Cloud, NATS Cloud, Vercel, GPU instance).

## Services

| Service | Port | Purpose |
|---|---|---|
| Postgres | 5432 | Supabase local dev (4 schemas) |
| Redis | 6379 | Event bus + cache |
| NATS | 4222 | Message queue (alternative transport) |
| Kibana | 5601 | Log viewer (optional) |
''')

w("infrastructure/docker-compose.yml", '''
services:
  postgres:
    image: supabase/postgres:15.6.1
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../database/raw-market-data/schema.sql:/docker-entrypoint-initdb.d/01-raw.sql:ro
      - ../database/processed-market-data/schema.sql:/docker-entrypoint-initdb.d/02-processed.sql:ro
      - ../database/ai-intelligence/schema.sql:/docker-entrypoint-initdb.d/03-ai.sql:ro
      - ../database/historical-reports/schema.sql:/docker-entrypoint-initdb.d/04-reports.sql:ro

  redis:
    image: redis:7.4-alpine
    ports: ["6379:6379"]
    volumes:
      - redis_data:/data

  nats:
    image: nats:2.10-alpine
    ports: ["4222:4222", "8222:8222"]
    command: ["--jetstream"]

volumes:
  postgres_data:
  redis_data:
''')

print(f"\n✅ Part 3 complete: {FILES_WRITTEN} files written under {ROOT}")
