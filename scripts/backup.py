"""Quiesce writers, dump both databases and encrypt a checkpoint using installed restic."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(*args):
    return subprocess.run(args, check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--init", action="store_true", help="Initialize a new restic repository")
    args = parser.parse_args()
    if not shutil.which("restic"):
        raise SystemExit("Install the free restic CLI first.")
    os.chdir(Path(__file__).resolve().parents[1])
    base = ["restic", "--repo", args.repository, "--password-file", str(Path(args.password_file).resolve())]
    if args.init:
        run(*base, "init")
    running = run("docker", "compose", "ps", "--services", "--status", "running").decode().split()
    writers = [s for s in ["api", "n8n", "workspace"] if s in running]
    if writers:
        run("docker", "compose", "stop", *writers)
    try:
        with tempfile.TemporaryDirectory(prefix="career-backup-") as directory:
            root = Path(directory)
            for name, role in [("career", "career"), ("n8n", "n8n")]:
                run(
                    "docker",
                    "compose",
                    "exec",
                    "-T",
                    "postgres",
                    "pg_dump",
                    "-U",
                    role,
                    "-Fc",
                    "-f",
                    "/tmp/" + name + ".dump",
                    name,
                )
                run(
                    "docker", "compose", "cp", "postgres:/tmp/" + name + ".dump", str(root / (name + ".dump"))
                )
            run("docker", "compose", "cp", "api:/app/artifacts", str(root / "artifacts"))
            run("docker", "compose", "cp", "n8n:/home/node/.n8n", str(root / "n8n_state"))
            shutil.copyfile(".env", root / "recovery.env")
            manifest = {
                str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*")
                if path.is_file()
            }
            (root / "manifest.json").write_text(json.dumps(manifest, indent=2))
            run(*base, "backup", "--tag", "career-v02", str(root))
        print("Encrypted checkpoint completed. Run restic snapshots and periodically test restore.")
    finally:
        if writers:
            run("docker", "compose", "start", *writers)


if __name__ == "__main__":
    main()
