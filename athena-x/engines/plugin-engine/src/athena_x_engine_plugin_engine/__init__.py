"""Plugin-based TA Platform engine."""
from .manifest import PluginManifest, PluginCategory, PluginLayer
from .registry import PluginRegistry, RegistryEntry
from .manager import PluginManager
from .dependency import DependencyResolver, DependencyGraph
from .scheduler import PluginScheduler, ScheduleEntry
from .config import PluginConfigService
from .executor import PluginExecutor, ExecutionResult

__all__ = [
    "PluginManifest", "PluginCategory", "PluginLayer",
    "PluginRegistry", "RegistryEntry",
    "PluginManager",
    "DependencyResolver", "DependencyGraph",
    "PluginScheduler", "ScheduleEntry",
    "PluginConfigService",
    "PluginExecutor", "ExecutionResult",
]
__version__ = "0.1.0"
