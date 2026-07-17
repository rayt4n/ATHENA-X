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
