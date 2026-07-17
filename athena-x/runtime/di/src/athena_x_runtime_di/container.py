"""Lightweight DI container with token-based injection.

Supports:
- Singleton scope (one instance per container)
- Factory scope (new instance each call)
- Async factories
- Override (for testing)

No external dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, TypeVar, get_type_hints
import inspect
import threading

T = TypeVar("T")


class Scope(str, Enum):
    SINGLETON = "singleton"
    FACTORY = "factory"


@dataclass(frozen=True)
class Token(Generic[T]):
    """Injection token. Use as Token[ServiceType]("service_name")."""
    name: str
    type_: type | None = None

    def __repr__(self) -> str:
        return f"Token({self.name!r})"


class Container:
    """DI container.

    Usage:
        container = Container()

        # Register a singleton instance
        container.register_singleton(Token(Logger, "logger"), my_logger)

        # Register a factory
        container.register_factory(Token(BusClient, "bus"),
                                    lambda c: RedisBusClient(c.resolve(Token(Config, "config")).redis.url))

        # Resolve
        logger = container.resolve(Token(Logger, "logger"))

        # Override for testing
        container.override(Token(Logger, "logger"), mock_logger)
    """

    def __init__(self):
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[["Container"], Any]] = {}
        self._async_factories: dict[str, Callable[["Container"], Awaitable[Any]]] = {}
        self._overrides: dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_singleton(self, token: Token[T], instance: T) -> None:
        """Register an already-constructed instance as a singleton."""
        with self._lock:
            self._singletons[token.name] = instance

    def register_factory(self, token: Token[T],
                         factory: Callable[["Container"], T]) -> None:
        """Register a factory. Each resolve() returns a new instance.

        For singleton behavior, cache inside the factory.
        """
        with self._lock:
            self._factories[token.name] = factory

    def register_async_factory(self, token: Token[T],
                                factory: Callable[["Container"], Awaitable[T]]) -> None:
        """Register an async factory. Use resolve_async() to get instance.

        Each call to resolve_async() invokes the factory.
        """
        with self._lock:
            self._async_factories[token.name] = factory

    def register_async_singleton(self, token: Token[T],
                                  factory: Callable[["Container"], Awaitable[T]]) -> None:
        """Register an async singleton. Factory is called once; result cached.

        Use this for async-constructed resources that must be shared (event bus,
        health monitor, scheduler, etc.).
        """
        async def singleton_wrapper(c: "Container") -> T:
            if token.name in c._singletons:
                return c._singletons[token.name]
            instance = await factory(c)
            with c._lock:
                c._singletons[token.name] = instance
            return instance
        with self._lock:
            self._async_factories[token.name] = singleton_wrapper

    def resolve(self, token: Token[T]) -> T:
        """Resolve a dependency synchronously.

        Priority:
        1. Overrides (for testing)
        2. Singletons
        3. Factories
        """
        with self._lock:
            if token.name in self._overrides:
                return self._overrides[token.name]
            if token.name in self._singletons:
                return self._singletons[token.name]
            if token.name in self._factories:
                return self._factories[token.name](self)
        raise KeyError(f"No registration for token: {token.name}")

    async def resolve_async(self, token: Token[T]) -> T:
        """Resolve a dependency that may require async initialization."""
        with self._lock:
            if token.name in self._overrides:
                return self._overrides[token.name]
            if token.name in self._singletons:
                return self._singletons[token.name]
            if token.name in self._async_factories:
                return await self._async_factories[token.name](self)
            if token.name in self._factories:
                return self._factories[token.name](self)
        raise KeyError(f"No registration for token: {token.name}")

    def override(self, token: Token[T], instance: T) -> None:
        """Override a registration. Used in tests to inject mocks."""
        with self._lock:
            self._overrides[token.name] = instance

    def clear_overrides(self) -> None:
        """Remove all overrides."""
        with self._lock:
            self._overrides.clear()

    def has(self, token: Token[T]) -> bool:
        with self._lock:
            return (
                token.name in self._overrides
                or token.name in self._singletons
                or token.name in self._factories
                or token.name in self._async_factories
            )

    def list_tokens(self) -> list[str]:
        with self._lock:
            all_names = set()
            all_names.update(self._singletons.keys())
            all_names.update(self._factories.keys())
            all_names.update(self._async_factories.keys())
            all_names.update(self._overrides.keys())
            return sorted(all_names)

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
            self._async_factories.clear()
            self._overrides.clear()
