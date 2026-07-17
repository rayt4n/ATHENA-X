# {PACKAGE_NAME}

> {ONE_LINE_DESCRIPTION}

## Purpose

{DETAILED_DESCRIPTION}

## Public API

```python
from {PACKAGE_NAME} import {PUBLIC_EXPORT_1}, {PUBLIC_EXPORT_2}
```

### {EXPORT_1}

```python
{USAGE_EXAMPLE}
```

## Event Contracts

{EVENT_TYPES_PUBLISHED_OR_CONSUMED}

## Dependencies

- {DEPENDENCY_1}
- {DEPENDENCY_2}

## Health Check

```python
{HEALTH_CHECK_METHOD}
```

## Tests

```bash
cd {PACKAGE_DIR} && pytest tests/
```

## Stage-Gate Compliance

- [x] Functional - works correctly
- [x] Tested - unit + integration tests pass
- [x] Modular - no circular deps, public interface only
- [x] Documented - README + API docs complete
- [x] Verifiable - inputs, outputs, logs, health checks inspectable
- [x] Production-ready - linting, type checks, builds pass
