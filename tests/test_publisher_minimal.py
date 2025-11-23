"""Minimal test for Publisher basic functionality."""


class TestPublisherMinimal:
    """Test Publisher with minimal registry operations."""

    def test_publisher_init(self, publisher_factory):
        publisher = publisher_factory()

        assert publisher.applications == {}
        assert "cli" in publisher.chan_registry.channels
        assert "http" in publisher.chan_registry.channels

    def test_list_empty_apps(self, publisher_factory):
        publisher = publisher_factory()
        result = publisher.app_manager.list()
        assert result["total"] == 0
        assert result["apps"] == {}

    def test_add_remove_app(self, create_app, publisher_factory):
        publisher = publisher_factory()
        spec = create_app(class_name="MiniApp")

        add_result = publisher.app_manager.add("mini", spec.target)
        assert add_result["status"] == "registered"

        apps = publisher.app_manager.list()
        assert apps["total"] == 1
        assert "mini" in apps["apps"]

        remove_result = publisher.app_manager.remove("mini")
        assert remove_result["status"] == "removed"

        apps = publisher.app_manager.list()
        assert apps["total"] == 0
