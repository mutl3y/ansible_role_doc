"""Tests for structured logging in scanner core."""

import logging

from prism.scanner_core.logging_config import (
    LoggerFactory,
    get_logger,
    set_scan_context,
)


class TestStructuredLogging:
    """Test structured logging implementation."""

    def test_scan_context_propagation(self, caplog):
        """Test that scan context is propagated through logging."""
        with caplog.at_level(logging.INFO):
            with set_scan_context(role_name="test_role", scan_id="123"):
                logger = get_logger(__name__)
                logger.info("Test message", extra={"operation": "test"})

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.message == "Test message"
        assert hasattr(record, "role_name")
        assert hasattr(record, "scan_id")
        assert hasattr(record, "operation")

    def test_nested_context(self, caplog):
        """Test nested scan contexts."""
        with caplog.at_level(logging.INFO):
            with set_scan_context(role_name="outer", scan_id="1"):
                logger = get_logger(__name__)
                logger.info("Outer message")
                with set_scan_context(role_name="inner", scan_id="2"):
                    logger.info("Inner message")

        assert len(caplog.records) == 2
        outer_record = caplog.records[0]
        inner_record = caplog.records[1]
        assert outer_record.role_name == "outer"
        assert inner_record.role_name == "inner"


class TestLoggerFactory:
    """Test injected logger factory."""

    def test_logger_factory_creates_structured_logger(self, caplog):
        """Test that LoggerFactory creates loggers with structured fields."""
        factory = LoggerFactory()
        logger = factory.get_logger("test.module")

        with caplog.at_level(logging.INFO):
            with set_scan_context(role_name="test_role", scan_id="456"):
                logger.info("Factory test message", extra={"component": "factory"})

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.message == "Factory test message"
        assert hasattr(record, "role_name")
        assert record.role_name == "test_role"
        assert hasattr(record, "scan_id")
        assert record.scan_id == "456"
        assert hasattr(record, "component")
        assert record.component == "factory"

    def test_logger_factory_injection_in_di(self):
        """Test that logger factory can be injected via DI."""
        from prism.scanner_core.di import DIContainer

        # Create DI container with logger factory
        container = DIContainer(
            role_path="/tmp/test",
            scan_options={},
            wiring_registry={
                "logger_factory": {
                    "factory": lambda: LoggerFactory(),
                    "lifecycle": "singleton",
                    "dependencies": [],
                }
            },
        )

        factory = container._resolve("logger_factory")
        assert isinstance(factory, LoggerFactory)
