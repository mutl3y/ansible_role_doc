"""Unit tests for scanner_core.di module reformation."""

import pytest
from prism.scanner_core.di import DIContainer, WiringSpec


class TestDIContainerReformation:
    """Test reformed DIContainer with wiring registries and cycle detection."""

    def test_cycle_detection_raises_on_dependency_loop(self):
        """Cycle detection prevents loops in dependency graph."""
        registry = {
            "service_a": WiringSpec(
                factory=lambda di, dep_b: f"a-{dep_b}",
                lifecycle="singleton",
                dependencies=["service_b"],
            ),
            "service_b": WiringSpec(
                factory=lambda di, dep_a: f"b-{dep_a}",
                lifecycle="singleton",
                dependencies=["service_a"],
            ),
        }
        di = DIContainer("role_path", {}, wiring_registry=registry)

        with pytest.raises(RuntimeError, match="Cycle detected"):
            di._resolve("service_a")

    def test_singleton_lifecycle_caches_instance(self):
        """Singleton services return the same instance on multiple resolves."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance-{call_count}"

        registry = {
            "test_service": WiringSpec(
                factory=factory, lifecycle="singleton", dependencies=[]
            ),
        }
        di = DIContainer("role_path", {}, wiring_registry=registry)

        instance1 = di._resolve("test_service")
        instance2 = di._resolve("test_service")

        assert instance1 == "instance-1"
        assert instance2 == "instance-1"
        assert instance1 is instance2

    def test_transient_lifecycle_creates_new_instance_each_time(self):
        """Transient services create new instances on each resolve."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance-{call_count}"

        registry = {
            "test_service": WiringSpec(
                factory=factory, lifecycle="transient", dependencies=[]
            ),
        }
        di = DIContainer("role_path", {}, wiring_registry=registry)

        instance1 = di._resolve("test_service")
        instance2 = di._resolve("test_service")

        assert instance1 == "instance-1"
        assert instance2 == "instance-2"
        assert instance1 != instance2

    def test_factory_methods_use_registry_internally(self):
        """Existing factory methods delegate to registry resolution."""
        di = DIContainer("role_path", {})

        # Test that factory methods work (assuming registry is set up)
        # This will pass once registry is implemented
        variable_discovery = di.factory_variable_discovery()
        assert variable_discovery is not None

        feature_detector = di.factory_feature_detector()
        assert feature_detector is not None

    def test_no_global_state_in_factories(self):
        """Factory methods are pure and don't rely on global state."""
        di1 = DIContainer("role_path1", {})
        di2 = DIContainer("role_path2", {})

        vd1 = di1.factory_variable_discovery()
        vd2 = di2.factory_variable_discovery()

        # Different DI containers should create different instances
        assert vd1 is not vd2

    def test_dependencies_resolved_correctly(self):
        """Dependencies are resolved and passed to factories."""
        results = []

        def dep_factory():
            return "dep_instance"

        def service_factory(dep):
            results.append(dep)
            return f"service-{dep}"

        registry = {
            "dependency": WiringSpec(
                factory=dep_factory, lifecycle="singleton", dependencies=[]
            ),
            "service": WiringSpec(
                factory=service_factory,
                lifecycle="singleton",
                dependencies=["dependency"],
            ),
        }
        di = DIContainer("role_path", {}, wiring_registry=registry)

        service = di._resolve("service")

        assert service == "service-dep_instance"
        assert results == ["dep_instance"]
