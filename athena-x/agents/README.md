# agents/

All AI agents in ATHENA-X. Each agent is an independent, supervised process
that subscribes to bus events and publishes bus events.

## Layered architecture (Changes 1, 2, 3, 4, 12)

```
agents/
├── data-collection/          (Layer 0: Data Collection AI — Change 1)
│   ├── collection-agent/
│   ├── validation-agent/
│   └── standardization-agent/
│
├── raw-intelligence/         (Layer 1: Raw Intelligence — facts only — Change 2)
│   ├── technical-analysis/   (23 TA agents — Change 6)
│   ├── options/              (15 options agents — Change 7)
│   ├── news/
│   ├── macro/
│   └── cross-market/         (20 cross-market agents — Change 8)
│
├── decision-intelligence/    (Layer 2: Decision Intelligence — conclusions only — Change 2)
│   ├── market-regime/        (Change 9)
│   ├── timeframe-sync/       (Change 10)
│   ├── forecast/             (AI forecast — hybrid routing — Change 4 of STEP 2)
│   ├── scenario-analysis/
│   ├── volatility-projection/
│   ├── expected-move/
│   ├── probability-tree/
│   ├── ai-consensus/
│   └── probability-engine/
│
├── supervisor/               (Layer 3: Supervisor AI — Change 3)
├── validator/                (Layer 4: Institutional Validation — Change 4)
├── self-correction/          (Layer 5: Continuous Learning — Change 12)
└── automation/               (Future — Change 16 — reserved)
    ├── execution/
    ├── risk/
    ├── position/
    └── broker/
```

## Agent contract

Every agent implements this contract:

```python
class Agent(Protocol):
    agent_id: str
    layer: str  # data-collection | raw-intelligence | decision-intelligence | supervisor | validator | self-correction | automation

    async def start(self, config: AgentConfig) -> None: ...
    async def stop(self) -> None: ...
    async def on_event(self, event: BusEvent) -> None: ...
```

## Agent file structure

```
agents/<layer>/<agent-name>/
├── README.md
├── pyproject.toml
├── src/<pkg>/
│   ├── __init__.py
│   ├── manifest.py        # agent manifest (id, layer, subscriptions, publications)
│   ├── config.py          # Zod-validated config schema
│   ├── types.py           # agent-specific types
│   └── agent.py           # the agent class
└── tests/
    ├── __init__.py
    └── test_agent.py
```

## Reporting to Supervisor (Change 3)

Every agent emits periodic `system:agent-heartbeat` events with the 10
health metrics (Change 17). The Supervisor subscribes to all heartbeats,
detects failures, triggers retries, and adjusts confidence weights.

## Raw vs Decision Intelligence (Change 2)

- **Raw Intelligence** agents publish facts only (e.g., `ta:indicator-computed`,
  `ta:signal-emitted`, `options:iv-updated`). Never conclusions.
- **Decision Intelligence** agents publish conclusions only (e.g.,
  `decision:regime-classified`, `decision:scenario-updated`, `forecast:trajectory-computed`).
  Never raw facts.

This separation is enforced by ESLint and reviewed in PRs.
