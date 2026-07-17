# plugins/

Installable indicator, options, and pattern recognition plugins (Change 13).

Every indicator is an independent plugin with a standardized manifest.
Plugins are loaded by `engines/plugin-engine/` at startup.

## Layout

```
plugins/
├── indicators/    # TA computation plugins
├── options/       # options computation plugins
├── patterns/      # pattern recognition plugins
└── dark-pool/     # alternative data plugins (future)
```

## Plugin manifest

Every plugin ships a `manifest.py` (or `manifest.ts` for browser plugins):

```python
@dataclass(frozen=True)
class PluginManifest:
    id: str           # e.g., "indicators.ema"
    name: str         # e.g., "EMA"
    version: str      # semver
    type: str         # indicator | options | pattern | dark-pool
    runtime: str      # python | typescript | wasm
    inputs: list[str]      # e.g., ["closes"]
    params: dict           # e.g., {"period": 20}
    outputs: list[str]     # e.g., ["value", "signal"]
    dependencies: list[str]  # other plugin ids
```

## Adding a new plugin

```bash
python tools/plugin-scaffolder/scaffold.py indicators my_indicator
```

This generates boilerplate under `plugins/indicators/my_indicator/`.
