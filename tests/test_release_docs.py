from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v080_release_docs_and_assets_are_in_sync() -> None:
    readme = (ROOT / "README.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text()
    release_notes = (ROOT / "docs/releases/v0.8.0.md").read_text()

    assert "18 tabs" in readme
    assert "Hermes Teal" in readme
    assert "Plugin Hub" in readme
    assert "Gateway Managed Tools" in readme
    assert "Model Analytics" in readme

    assert "## [0.8.0] — 2026-05-05" in changelog
    for phrase in [
        "Dashboard executive summary",
        "Plugin Hub",
        "Gateway managed-tool visibility",
        "Model analytics upgrade",
        "Official Hermes Teal theme",
        "Gateway update action hardening",
        "Responsive top navigation",
    ]:
        assert phrase in changelog

    for asset in [
        "dashboard-executive.png",
        "gateway-tools.png",
        "model-analytics.png",
        "plugin-hub.png",
        "responsive-tabs.png",
    ]:
        assert (ROOT / "assets" / asset).exists()
        assert asset in readme or asset in release_notes
