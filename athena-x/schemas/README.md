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
