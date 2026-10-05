"""Unit tests for AppLogger singleton.

Covers:
- Singleton behaviour
- Console handler setup
- File handler setup (per-run log file)
- No-handler mode (console=False, log_file=False)
- Troubleshooting mode (DEBUG level from JSON config)
- Normal mode (INFO level)
- Log file naming convention (log_YYYYmmDD-HHMMSS.log)
- Fallback when config JSON is missing or invalid
- IAppLogger interface compliance
- Actual message content in file and console output
"""

import json
import logging
import re
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from bda.application.interfaces import IAppLogger
from bda.infrastructure.utils.logger import AppLogger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _patch_config(monkeypatch, config_path: Path) -> None:
    def _load_config_override() -> dict[str, Any]:
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        return raw if isinstance(raw, dict) else {}

    monkeypatch.setattr(AppLogger, "_load_config", staticmethod(_load_config_override))


def _flush(logger_name: str = "BDA") -> None:
    for h in logging.getLogger(logger_name).handlers:
        h.flush()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure every test starts with a fresh singleton."""
    AppLogger._reset()
    yield
    AppLogger._reset()


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "logger_config.json"
    _write_config(path, {"logs_directory": str(tmp_path), "troubleshooting": False})
    return path


@pytest.fixture()
def troubleshooting_config_file(tmp_path: Path) -> Path:
    path = tmp_path / "logger_config.json"
    _write_config(path, {"logs_directory": str(tmp_path), "troubleshooting": True})
    return path


# ===========================================================================
# Singleton behaviour
# ===========================================================================

class TestSingleton:

    def test_returns_same_instance(self):
        a = AppLogger(console=True)
        b = AppLogger()
        assert a is b

    def test_second_call_ignores_flags(self):
        a = AppLogger(console=False, log_file=False)
        b = AppLogger(console=True, log_file=True)
        assert a is b
        assert logging.getLogger("BDA").handlers == []

    def test_reset_allows_reconfiguration(self):
        a = AppLogger(console=False)
        assert logging.getLogger("BDA").handlers == []

        AppLogger._reset()

        b = AppLogger(console=True)
        assert a is not b
        assert len(logging.getLogger("BDA").handlers) == 1


# ===========================================================================
# IAppLogger compliance
# ===========================================================================

class TestInterface:

    def test_implements_iapplogger(self):
        assert isinstance(AppLogger(console=False), IAppLogger)

    def test_has_all_methods(self):
        logger = AppLogger(console=False)
        for method in ("debug", "info", "warning", "error"):
            assert callable(getattr(logger, method))


# ===========================================================================
# Handler configuration
# ===========================================================================

class TestHandlerSetup:

    def test_console_only(self):
        AppLogger(console=True, log_file=False)
        handlers = logging.getLogger("BDA").handlers
        assert len(handlers) == 1
        assert isinstance(handlers[0], logging.StreamHandler)
        assert not isinstance(handlers[0], logging.FileHandler)

    def test_file_only(self, monkeypatch, config_file):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        AppLogger(console=False, log_file=True)
        handlers = logging.getLogger("BDA").handlers
        assert len(handlers) == 1
        assert isinstance(handlers[0], logging.FileHandler)

    def test_console_and_file(self, monkeypatch, config_file):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        AppLogger(console=True, log_file=True)
        handlers = logging.getLogger("BDA").handlers
        assert len(handlers) == 2
        types = {type(h) for h in handlers}
        assert logging.StreamHandler in types
        assert logging.FileHandler in types

    def test_no_handlers(self):
        AppLogger(console=False, log_file=False)
        assert logging.getLogger("BDA").handlers == []

    def test_propagation_disabled(self):
        AppLogger(console=True)
        assert logging.getLogger("BDA").propagate is False


# ===========================================================================
# Log level / troubleshooting
# ===========================================================================

class TestLogLevel:

    def test_normal_mode_sets_info(self, monkeypatch, config_file):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.INFO

    def test_troubleshooting_sets_debug(self, monkeypatch, troubleshooting_config_file):
        _patch_config(monkeypatch, troubleshooting_config_file)
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.DEBUG

    def test_missing_config_defaults_to_info(self, monkeypatch, tmp_path):
        _patch_config(monkeypatch, tmp_path / "nonexistent.json")
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.INFO


# ===========================================================================
# File logging
# ===========================================================================

class TestFileLogging:

    def test_creates_log_file_with_correct_name(self, monkeypatch, config_file, tmp_path):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        logger = AppLogger(console=False, log_file=True)
        logger.info("test entry")
        _flush()

        files = list(tmp_path.glob("log_*.log"))
        assert len(files) == 1
        assert re.match(r"^log_\d{8}-\d{6}\.log$", files[0].name)

    def test_file_contains_logged_messages(self, monkeypatch, config_file, tmp_path):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        logger = AppLogger(console=False, log_file=True)
        logger.info("hello %s", "world")
        logger.warning("watch out")
        logger.error("broken %d", 42)
        _flush()

        content = list(tmp_path.glob("log_*.log"))[0].read_text(encoding="utf-8")
        assert "hello world" in content
        assert "watch out" in content
        assert "broken 42" in content

    def test_debug_not_in_file_when_normal_mode(self, monkeypatch, config_file, tmp_path):
        _patch_config(monkeypatch, config_file)
        AppLogger._reset()

        logger = AppLogger(console=False, log_file=True)
        logger.debug("secret debug")
        logger.info("visible info")
        _flush()

        content = list(tmp_path.glob("log_*.log"))[0].read_text(encoding="utf-8")
        assert "secret debug" not in content
        assert "visible info" in content

    def test_debug_in_file_when_troubleshooting(self, monkeypatch, troubleshooting_config_file, tmp_path):
        _patch_config(monkeypatch, troubleshooting_config_file)
        AppLogger._reset()

        logger = AppLogger(console=False, log_file=True)
        logger.debug("debug visible now")
        _flush()

        content = list(tmp_path.glob("log_*.log"))[0].read_text(encoding="utf-8")
        assert "debug visible now" in content

    def test_fallback_logs_directory(self, monkeypatch, tmp_path):
        config_path = tmp_path / "logger_config.json"
        _write_config(config_path, {"logs_directory": "logs", "troubleshooting": False})
        _patch_config(monkeypatch, config_path)
        AppLogger._reset()

        # Should not raise — falls back gracefully
        logger = AppLogger(console=False, log_file=True)
        logger.info("fallback test")
        _flush()


# ===========================================================================
# Console logging
# ===========================================================================

class TestConsoleLogging:

    def test_console_receives_messages(self):
        logger = AppLogger(console=True, log_file=False)

        buf = StringIO()
        logging.getLogger("BDA").handlers[0].stream = buf

        logger.info("console test %d", 123)
        logger.warning("warn msg")
        _flush()

        output = buf.getvalue()
        assert "console test 123" in output
        assert "warn msg" in output

    def test_console_format_contains_expected_fields(self):
        logger = AppLogger(console=True, log_file=False)

        buf = StringIO()
        logging.getLogger("BDA").handlers[0].stream = buf

        logger.info("format check")
        _flush()

        line = buf.getvalue()
        # expected: "2026-04-20 15:30:43,290 - BDA - INFO - format check"
        assert " - BDA - INFO - format check" in line


# ===========================================================================
# Config edge cases
# ===========================================================================

class TestConfigEdgeCases:

    def test_invalid_json_config(self, monkeypatch, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json!!!", encoding="utf-8")
        _patch_config(monkeypatch, bad)
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.INFO

    def test_empty_json_config(self, monkeypatch, tmp_path):
        empty = tmp_path / "empty.json"
        empty.write_text("{}", encoding="utf-8")
        _patch_config(monkeypatch, empty)
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.INFO

    def test_non_dict_json_config(self, monkeypatch, tmp_path):
        arr = tmp_path / "list.json"
        arr.write_text("[1, 2, 3]", encoding="utf-8")
        _patch_config(monkeypatch, arr)
        AppLogger._reset()

        AppLogger(console=True)
        assert logging.getLogger("BDA").level == logging.INFO