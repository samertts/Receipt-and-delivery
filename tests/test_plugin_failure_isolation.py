from __future__ import annotations

from lab_system.app.services.plugin_service import PluginLoader, PluginRegistry


def test_plugin_load_failure_disables_only_failed_plugin(tmp_path):
    plugin_path = tmp_path / "broken_plugin.py"
    plugin_path.write_text("raise RuntimeError('plugin crash')\n", encoding="utf-8")

    registry = PluginRegistry()
    assert registry.register("broken", {"version": "1.0", "status": "active"})
    loader = PluginLoader(registry)

    result = loader.load_plugin("broken", str(plugin_path))

    assert result["success"] is False
    plugin = registry.get_plugin("broken")
    assert plugin["status"] == "disabled"
    assert plugin["failure_count"] == 1
    assert plugin["last_error"] == "plugin crash"
