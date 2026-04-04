"""Tests for ExtensionRegistry functionality."""

from prism.scanner_core.extension_registry import ExtensionRegistry, HookPoint


class TestExtensionRegistry:
    """Test ExtensionRegistry registration and calling."""

    def test_registry_initially_empty(self):
        """Registry starts with no processors."""
        registry = ExtensionRegistry()
        assert registry.get_processors(HookPoint.VARIABLE_DISCOVERY_PRE) == []
        assert registry.get_processors(HookPoint.VARIABLE_DISCOVERY_POST) == []

    def test_register_processor(self):
        """Can register a processor for a hook point."""
        registry = ExtensionRegistry()

        def dummy_processor(*args, **kwargs):
            return "result"

        registry.register(HookPoint.VARIABLE_DISCOVERY_PRE, dummy_processor)
        processors = registry.get_processors(HookPoint.VARIABLE_DISCOVERY_PRE)
        assert len(processors) == 1
        assert processors[0] == dummy_processor

    def test_call_processors(self):
        """Can call registered processors and collect results."""
        registry = ExtensionRegistry()
        results = []

        def processor1(*args, **kwargs):
            results.append("proc1")
            return "result1"

        def processor2(*args, **kwargs):
            results.append("proc2")
            return "result2"

        registry.register(HookPoint.VARIABLE_DISCOVERY_PRE, processor1)
        registry.register(HookPoint.VARIABLE_DISCOVERY_PRE, processor2)

        call_results = registry.call_processors(
            HookPoint.VARIABLE_DISCOVERY_PRE, "arg1", kwarg1="value"
        )
        assert call_results == ["result1", "result2"]
        assert results == ["proc1", "proc2"]

    def test_call_processors_no_registered(self):
        """Calling with no registered processors returns empty list."""
        registry = ExtensionRegistry()
        results = registry.call_processors(HookPoint.FEATURE_DETECTION_POST)
        assert results == []

    def test_get_processors_returns_copy(self):
        """get_processors returns a copy, not the internal list."""
        registry = ExtensionRegistry()

        def dummy():
            pass

        registry.register(HookPoint.VARIABLE_DISCOVERY_PRE, dummy)
        processors = registry.get_processors(HookPoint.VARIABLE_DISCOVERY_PRE)
        processors.append(lambda: None)  # Modify the returned list

        # Internal list should not be affected
        assert len(registry.get_processors(HookPoint.VARIABLE_DISCOVERY_PRE)) == 1
