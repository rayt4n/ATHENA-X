"""Tests for DI container."""
import pytest
from athena_x_runtime_di import Container, Token


class Logger:
    def __init__(self, name: str = "default"):
        self.name = name


class Database:
    def __init__(self, logger: Logger):
        self.logger = logger


LOGGER_TOKEN = Token[Logger]("logger")
DB_TOKEN = Token[Database]("database")


def test_register_and_resolve_singleton():
    """A registered singleton can be resolved."""
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger("test"))
    logger = c.resolve(LOGGER_TOKEN)
    assert logger.name == "test"


def test_register_and_resolve_factory():
    """A factory creates a new instance each call."""
    c = Container()
    c.register_factory(LOGGER_TOKEN, lambda c: Logger("factory"))
    l1 = c.resolve(LOGGER_TOKEN)
    l2 = c.resolve(LOGGER_TOKEN)
    assert l1 is not l2  # different instances
    assert l1.name == "factory"


def test_factory_can_resolve_other_deps():
    """A factory can resolve other registered dependencies."""
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger("base"))
    c.register_factory(DB_TOKEN, lambda c: Database(c.resolve(LOGGER_TOKEN)))

    db = c.resolve(DB_TOKEN)
    assert db.logger.name == "base"


def test_override_replaces_registration():
    """Override injects a mock for testing."""
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger("real"))
    c.override(LOGGER_TOKEN, Logger("mock"))

    logger = c.resolve(LOGGER_TOKEN)
    assert logger.name == "mock"


def test_clear_overrides_restores_original():
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger("real"))
    c.override(LOGGER_TOKEN, Logger("mock"))
    c.clear_overrides()

    logger = c.resolve(LOGGER_TOKEN)
    assert logger.name == "real"


def test_resolve_unregistered_raises():
    c = Container()
    with pytest.raises(KeyError):
        c.resolve(Token("unknown"))


def test_has_returns_true_for_registered():
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger())
    assert c.has(LOGGER_TOKEN)
    assert not c.has(Token("unknown"))


def test_list_tokens():
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger())
    c.register_factory(DB_TOKEN, lambda c: Database(Logger()))
    tokens = c.list_tokens()
    assert tokens == ["database", "logger"]


async def test_async_factory():
    """Async factories are resolved via resolve_async."""
    c = Container()

    async def make_logger(c: Container) -> Logger:
        return Logger("async")

    c.register_async_factory(LOGGER_TOKEN, make_logger)
    logger = await c.resolve_async(LOGGER_TOKEN)
    assert logger.name == "async"


async def test_resolve_async_falls_back_to_sync():
    """resolve_async can resolve sync registrations too."""
    c = Container()
    c.register_singleton(LOGGER_TOKEN, Logger("sync"))
    logger = await c.resolve_async(LOGGER_TOKEN)
    assert logger.name == "sync"
