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
