import json
import hashlib
from pathlib import Path
from dataclasses import asdict


def sha256_of_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def write_hash_file(path: Path, digest: str):
    path.with_name(path.name + ".sha256.txt").write_text(digest, encoding="utf-8")


def export_artifacts(system, base_dir="."):
    base = Path(base_dir)

    ledger_path = base / "ledger.json"
    watch_path = base / "watch_records.json"
    restoration_path = base / "restoration_log.json"
    summary_path = base / "run_summary.txt"
    manifest_path = base / "artifact_manifest.json"

    write_json(ledger_path, system.ledger)
    write_json(watch_path, {k: asdict(v) for k, v in system.watch_records.items()})
    write_json(restoration_path, system.restoration_log)

    summary_text = "\n".join(
        [
            "OGR run summary",
            f"ledger_entries: {len(system.ledger)}",
            f"watch_records: {len(system.watch_records)}",
            f"restoration_reviews: {len(system.restoration_log)}",
        ]
    )
    write_text(summary_path, summary_text)

    files = [ledger_path, watch_path, restoration_path, summary_path]
    manifest = {"artifacts": []}

    for path in files:
        digest = sha256_of_file(path)
        write_hash_file(path, digest)
        manifest["artifacts"].append(
            {
                "file": path.name,
                "sha256": digest,
            }
        )

    write_json(manifest_path, manifest)
    manifest_digest = sha256_of_file(manifest_path)
    write_hash_file(manifest_path, manifest_digest)

    print("\nArtifacts exported:")
    print(str(ledger_path.resolve()))
    print(str(watch_path.resolve()))
    print(str(restoration_path.resolve()))
    print(str(summary_path.resolve()))
    print(str(manifest_path.resolve()))

    print("\nHash files exported:")
    for path in files + [manifest_path]:
        print(str(path.with_name(path.name + ".sha256.txt").resolve()))

    print("\nSHA256 summary:")
    for item in manifest["artifacts"]:
        print(f"{item['file']}: {item['sha256']}")
    print(f"{manifest_path.name}: {manifest_digest}")