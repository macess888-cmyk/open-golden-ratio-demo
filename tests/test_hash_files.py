from ogr.scenarios import build_demo_system
from ogr.export import export_artifacts


def test_hash_files_are_written(tmp_path):
    system = build_demo_system()
    export_artifacts(system, tmp_path)

    expected_hash_files = [
        "ledger.json.sha256.txt",
        "watch_records.json.sha256.txt",
        "restoration_log.json.sha256.txt",
        "run_summary.txt.sha256.txt",
        "artifact_manifest.json.sha256.txt",
    ]

    for name in expected_hash_files:
        assert (tmp_path / name).exists(), f"Missing hash file: {name}"