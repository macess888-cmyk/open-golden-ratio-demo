from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_hash_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    return text.split()[0]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: py verify_artifacts.py <artifacts_dir>")
        return 1

    artifacts_dir = Path(sys.argv[1]).resolve()

    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        print(f"ERROR: artifacts directory not found: {artifacts_dir}")
        return 1

    manifest_path = artifacts_dir / "artifact_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if "artifacts" not in manifest:
        print("ERROR: manifest missing 'artifacts' key")
        return 1

    failures = []

    for entry in manifest["artifacts"]:
        filename = entry["file"]
        expected_hash = entry["sha256"]

        artifact_path = artifacts_dir / filename
        hash_file_path = artifacts_dir / f"{filename}.sha256.txt"

        if not artifact_path.exists():
            failures.append(f"MISSING ARTIFACT: {filename}")
            continue

        if not hash_file_path.exists():
            failures.append(f"MISSING HASH FILE: {filename}.sha256.txt")
            continue

        actual_hash = sha256_file(artifact_path)
        hash_file_value = read_hash_file(hash_file_path)

        if actual_hash != expected_hash:
            failures.append(
                f"HASH MISMATCH (manifest): {filename} | expected {expected_hash} | got {actual_hash}"
            )

        if actual_hash != hash_file_value:
            failures.append(
                f"HASH MISMATCH (sha256 file): {filename} | expected {hash_file_value} | got {actual_hash}"
            )

        if not failures or all(filename not in failure for failure in failures):
            print(f"OK  {filename}  {actual_hash}")

    manifest_hash_file = artifacts_dir / "artifact_manifest.json.sha256.txt"
    if manifest_hash_file.exists():
        manifest_actual_hash = sha256_file(manifest_path)
        manifest_hash_value = read_hash_file(manifest_hash_file)
        if manifest_actual_hash != manifest_hash_value:
            failures.append(
                "HASH MISMATCH (sha256 file): artifact_manifest.json "
                f"| expected {manifest_hash_value} | got {manifest_actual_hash}"
            )
        else:
            print(f"OK  artifact_manifest.json  {manifest_actual_hash}")

    if failures:
        print("\nVERIFICATION FAILED")
        for failure in failures:
            print(failure)
        return 1

    print("\nVERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())