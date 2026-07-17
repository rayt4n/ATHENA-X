"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForecastManifest:
    """Manifest for the AI Forecast Engine."""
    agent_id: str = "decision-intelligence.forecast"
    name: str = "AI Forecast Engine"
    layer: str = "decision-intelligence"
    description: str = "Hybrid AI forecast ensemble (Change 4 of STEP 2). LSTM/Transformer/TabPFN/XGBoost/CatBoost/LightGBM-large → Python GPU; LightGBM-small/RF/Logistic → Browser ONNX. LSTM NEVER runs in browser."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
        "decision:regime-classified",
        "learning:weight-adjusted",
    )
    publishes: tuple = (
        "forecast:trajectory-computed",
        "forecast:catalyst-detected",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ForecastManifest()
