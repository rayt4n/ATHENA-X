"""Options Plugin Engine - reuses Stage 7 plugin engine infrastructure."""
from .manager import OptionsPluginManager
from .executor import OptionsPluginExecutor

__all__ = ["OptionsPluginManager", "OptionsPluginExecutor"]
__version__ = "0.1.0"
