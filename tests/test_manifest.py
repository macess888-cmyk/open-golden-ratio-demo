import json

from ogr.scenarios import build_demo_system
from ogr.export import export_artifacts


def test_artifact_manifest_contains_expected_entries(tmp_path):
    system = build_demo_system()
    export_artifacts(system, tmp_path)

    manifest_path = tmp_path / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    expected_files = {
        "ledger.json",
        "watch_records.json",
        "restoration_log.json",
        "run_summary.txt",
    }

    assert "artifacts" in manifest

    artifact_entries = manifest["artifacts"]
    artifact_files = {item["file"] for item in artifact_entries}

    assert expected_files.issubset(artifact_files)

    for item in artifact_entries:
        assert "file" in item
        assert "sha256" in item
        assert isinstance(item["file"], str)
        assert isinstance(item["sha256"], str)
        assert len(item["sha256"]) == 64