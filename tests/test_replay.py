from pathlib import Path
from ogr.scenarios import build_demo_system
from ogr.export import export_artifacts


def test_replay_consistency(tmp_path):
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    run1.mkdir()
    run2.mkdir()

    system1 = build_demo_system()
    export_artifacts(system1, run1)

    system2 = build_demo_system()
    export_artifacts(system2, run2)

    ledger1 = (run1 / "ledger.json").read_text()
    ledger2 = (run2 / "ledger.json").read_text()

    watch1 = (run1 / "watch_records.json").read_text()
    watch2 = (run2 / "watch_records.json").read_text()

    assert ledger1 == ledger2
    assert watch1 == watch2