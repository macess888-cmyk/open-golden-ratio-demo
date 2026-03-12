from ogr.core import OGRSystem
from ogr.scenarios import build_demo_system
from ogr.export import export_artifacts


def test_core_import():
    system = OGRSystem()
    assert system is not None


def test_scenario_builder():
    system = build_demo_system()
    assert system is not None


def test_export_import():
    assert callable(export_artifacts)