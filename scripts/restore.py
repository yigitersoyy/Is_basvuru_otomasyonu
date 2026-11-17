"""Restore an encrypted checkpoint to an empty private directory and test an isolated database.

Never replaces the active installation or starts a sender. Use the restore runbook after validation.
"""

import argparse
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path


def run(*args, data=None):
    return subprocess.run(args, input=data, check=True, capture_output=True).stdout


def validate_files(root):
    manifests = list(root.rglob("manifest.json"))
    if len(manifests) != 1:
        raise ValueError("Expected exactly one checkpoint manifest")
    base = manifests[0].parent
    manifest = json.loads(manifests[0].read_text())
    for relative, digest in manifest.items():
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()) or not path.is_file():
            raise ValueError("Missing file or invalid checkpoint path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Checkpoint checksum mismatch")
    for name in ["career.dump", "n8n.dump", "recovery.env"]:
        if name not in manifest:
            raise ValueError("Incomplete checkpoint")
    return base


def validate_databases(base):
    compose = ["docker", "compose", "exec", "-T", "postgres"]
    for source in ["career", "n8n"]:
        name = "restore_check_" + uuid.uuid4().hex
        run(*compose, "createdb", "-U", "postgres", name)
        try:
            run(
                *compose,
                "pg_restore",
                "-U",
                "postgres",
                "--exit-on-error",
                "-d",
                name,
                data=(base / (source + ".dump")).read_bytes(),
            )
            if source == "career":
                rows = run(
                    *compose,
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    name,
                    "-Atc",
                    "SELECT json_build_object('id',id,'manifest',manifest)::text FROM packages",
                )
                for line in rows.decode().splitlines():
                    package = json.loads(line)
                    for extension, metadata in package["manifest"].items():
                        path = base / "artifacts" / package["id"] / ("cv." + extension)
                        if extension not in {"pdf", "docx"} or not path.is_file():
                            raise ValueError("Restored package artifact missing")
                        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
                            raise ValueError("Restored package artifact hash mismatch")
        finally:
            run(*compose, "dropdb", "-U", "postgres", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    target = args.target.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit("Target must be empty; existing files are preserved")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chdir(Path(__file__).resolve().parents[1])
    base = ["restic", "--repo", args.repository, "--password-file", str(Path(args.password_file).resolve())]
    run(*base, "check")
    nodes = run(*base, "ls", "--json", args.snapshot).decode().splitlines()
    manifests = [
        json.loads(line)["path"]
        for line in nodes
        if json.loads(line).get("struct_type") == "node" and json.loads(line).get("name") == "manifest.json"
    ]
    if len(manifests) != 1:
        raise SystemExit("Expected one checkpoint root; specify the exact checkpoint snapshot")
    # Restore only the checkpoint subtree, avoiding unrelated ancestor ownership/permissions.
    subtree = str(Path(manifests[0]).parent).replace("\\", "/")
    run(*base, "restore", args.snapshot + ":" + subtree, "--target", str(target), "--verify")
    checkpoint = validate_files(target)
    validate_databases(checkpoint)
    print(
        "PASS: encrypted repository, checkpoint hashes, isolated PostgreSQL restores and package artifact hashes."
    )
    print(
        "Active databases and sending state were not replaced. Restored files contain private recovery keys; protect the target."
    )


if __name__ == "__main__":
    main()
