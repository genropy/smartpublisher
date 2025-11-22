"""Tests for Publisher coordinator without AppRegistry."""

import json
import pytest

from smartpublisher.publisher import Publisher


class TestPublisher:
    """Test Publisher functionality."""

    def test_init_default(self, publisher_factory):
        pub = publisher_factory()

        assert pub.applications == {}
        assert pub.chan_registry.channels is not None
        assert "cli" in pub.chan_registry.channels
        assert "http" in pub.chan_registry.channels

    def test_get_channel(self, publisher_factory):
        pub = publisher_factory()
        assert pub.get_channel("cli") is pub.chan_registry.channels["cli"]
        assert pub.get_channel("http") is pub.chan_registry.channels["http"]

    def test_get_channel_not_found(self, publisher_factory):
        pub = publisher_factory()
        with pytest.raises(KeyError):
            pub.get_channel("nonexistent")

    def test_add_channel(self, publisher_factory):
        pub = publisher_factory()
        dummy = object()
        pub.add_channel("custom", dummy)
        assert pub.get_channel("custom") is dummy

    def test_add_app_registers_metadata(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app(class_name="SampleApp")

        result = pub.add("sample", spec.target)

        assert result["status"] == "registered"
        assert "sample" in pub.applications
        assert pub.list()["total"] == 1
        assert result["module"] == spec.module
        assert result["class"] == spec.class_name
        assert result["path"] == str(spec.file_path)

    def test_add_app_duplicate_name(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        with pytest.raises(ValueError):
            pub.add("sample", spec.target)

    def test_remove_app(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        result = pub.remove("sample")

        assert result["status"] == "removed"
        assert pub.applications == {}

    def test_remove_missing_app(self, publisher_factory):
        pub = publisher_factory()
        result = pub.remove("ghost")
        assert "error" in result

    def test_unload_app(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        result = pub.unload_app("sample")

        assert result["status"] == "unloaded"
        assert "sample" not in pub.applications

    def test_list_apps(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        listing = pub.list()

        assert listing["total"] == 1
        assert "sample" in listing["apps"]

    def test_getapp_metadata(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        info = pub.getapp("sample")

        assert info["name"] == "sample"
        assert info["module"] == spec.module
        assert info["class"] == spec.class_name

    def test_getapp_missing(self, publisher_factory):
        pub = publisher_factory()
        info = pub.getapp("ghost")
        assert "error" in info

    def test_load_app_returns_instance(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app()
        pub.add("sample", spec.target)

        instance = pub.load_app("sample")

        assert instance is pub.applications["sample"]

    def test_load_app_missing(self, publisher_factory):
        pub = publisher_factory()
        with pytest.raises(ValueError):
            pub.load_app("ghost")

    def test_get_publisher_singleton(self):
        from smartpublisher.publisher import get_publisher

        pub1 = get_publisher()
        pub2 = get_publisher()
        assert pub1 is pub2

    def test_add_app_passes_init_arguments(self, create_app, publisher_factory):
        pub = publisher_factory()
        spec = create_app(class_name="SampleApp")

        pub.add("sample", spec.target, "arg1", option="value")

        instance = pub.applications["sample"]
        assert instance.args == ("arg1",)
        assert instance.kwargs == {"option": "value"}

    def test_savestate_and_loadstate(self, create_app, tmp_path):
        state_file = tmp_path / "state.json"
        pub = Publisher(state_path=state_file, autosave=False)
        spec = create_app()

        pub.add("sample", spec.target, "one", option="x")
        save = pub.savestate()

        assert save["status"] == "saved"
        assert state_file.exists()

        new_pub = Publisher(state_path=state_file, autosave=False)
        load = new_pub.loadstate()

        assert load["status"] == "loaded"
        assert "sample" in new_pub.applications
        instance = new_pub.applications["sample"]
        assert getattr(instance, "args", ()) == ("one",)
        assert getattr(instance, "kwargs", {}) == {"option": "x"}

    def test_loadstate_missing_file(self, publisher_factory):
        pub = publisher_factory()
        result = pub.loadstate()
        assert "error" in result

    def test_loadstate_skip_missing(self, tmp_path):
        state_file = tmp_path / "state.json"
        payload = {
            "apps": [
                {"name": "ghost", "spec": str(tmp_path / "ghost.py"), "args": [], "kwargs": {}}
            ]
        }
        state_file.write_text(json.dumps(payload))

        pub = Publisher(state_path=state_file, autosave=False)
        result = pub.loadstate(skip_missing=True)

        assert result["status"] == "loaded"
        assert result["skipped"] != []
