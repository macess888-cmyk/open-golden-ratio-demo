# OGR Demo

This project contains a modular OpenGoldenRatio demo.

Project structure:

ogr/core.py
ogr/scenarios.py
ogr/export.py
run_ogr_demo.py
tests/
artifacts/

Run the demo:

py run_ogr_demo.py

Run tests:

py -m pytest tests -q

Artifacts produced:

artifacts/ledger.json
artifacts/watch_records.json
artifacts/restoration_log.json
artifacts/run_summary.txt
artifacts/artifact_manifest.json

Each artifact also has a matching SHA256 file.

Latest validated run:

ledger_entries: 42
watch_records: 4
restoration_reviews: 3