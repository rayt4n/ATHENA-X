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
