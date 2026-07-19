"""Tests for runtime logger."""
import json
import io
import sys
from contextlib import redirect_stdout

import athena_x_runtime_logger
from athena_x_runtime_logger import (
    get_logger,
    configure_logging,
    set_correlation_id,
    get_correlation_id,
    log_context,
    new_correlation_id,
)


def reset_logger():
    """Force re-configuration on next get_logger() call."""
    athena_x_runtime_logger.logger._CONFIGURED = False


def test_logger_emits_json():
    """Logger emits valid JSON to stdout."""
    reset_logger()
    configure_logging(json_output=True, debug=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        log = get_logger("test")
        log.info("hello", key="value")
    output = buf.getvalue().strip()
    parsed = json.loads(output)
    assert parsed["event"] == "hello"
    assert parsed["key"] == "value"
    assert parsed["level"] == "info"
    assert "timestamp" in parsed


def test_correlation_id_propagates():
    """Correlation ID set via context appears in every log line."""
    reset_logger()
    configure_logging(json_output=True, debug=True)
    buf = io.StringIO()
    cid = new_correlation_id()
    with redirect_stdout(buf):
        with log_context(correlation_id=cid, agent_id="ta.rsi"):
            log = get_logger("test")
            log.info("first")
            log.info("second")
    lines = buf.getvalue().strip().split("\n")
    for line in lines:
        parsed = json.loads(line)
        assert parsed["correlation_id"] == cid
        assert parsed["agent_id"] == "ta.rsi"


def test_correlation_id_resets_after_context():
    """Correlation ID is reset to empty after the context exits."""
    reset_logger()
    configure_logging(json_output=True, debug=True)
    cid = new_correlation_id()
    with log_context(correlation_id=cid):
        assert get_correlation_id() == cid
    assert get_correlation_id() == ""


def test_set_correlation_id_directly():
    """set_correlation_id sets the value for the current context."""
    set_correlation_id("test-cid-123")
    assert get_correlation_id() == "test-cid-123"


def test_logger_includes_exception_info():
    """Logger captures exception traceback."""
    reset_logger()
    configure_logging(json_output=True, debug=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        log = get_logger("test")
        try:
            raise ValueError("test error")
        except ValueError:
            log.exception("caught")
    parsed = json.loads(buf.getvalue().strip())
    assert parsed["event"] == "caught"
    assert "exception" in parsed
    assert "ValueError" in str(parsed["exception"])


def test_log_levels_filtered():
    """DEBUG messages are filtered when level is INFO."""
    reset_logger()
    configure_logging(json_output=True, debug=False)
    buf = io.StringIO()
    with redirect_stdout(buf):
        log = get_logger("test")
        log.debug("should be filtered")
        log.info("should appear")
    lines = [l for l in buf.getvalue().strip().split("\n") if l.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event"] == "should appear"
