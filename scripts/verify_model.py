"""Inspect a locally pulled Ollama artifact and record a private reproducibility report.

Uses only Python's standard library; no Python package installation is needed on Windows.
"""

import argparse
import json
import re
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--url", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    opener = build_opener(ProxyHandler({}))

    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = Request(args.url.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=240) as response:
            return json.load(response)

    details = request("/api/show", {"model": args.model})
    if args.model == "qwen3.5:9b":
        info = details.get("model_info", {})
        family = str(info.get("general.architecture", details.get("details", {}).get("family", ""))).lower()
        size = str(details.get("details", {}).get("parameter_size", ""))
        match = re.fullmatch(r"([0-9.]+)B", size, re.I)
        if "qwen35" not in family.replace(".", "") or not match or not 8 <= float(match[1]) <= 11:
            raise SystemExit("Artifact metadata does not establish the requested Qwen3.5 9B family/size.")
    matches = [m for m in request("/api/tags")["models"] if m["name"] == args.model]
    if len(matches) != 1 or not matches[0].get("digest"):
        raise SystemExit("Exact model tag/digest not found; no fallback permitted.")
    start = time.monotonic()
    response = request(
        "/api/chat",
        {
            "model": args.model,
            "stream": False,
            "think": False,
            "messages": [{"role": "user", "content": 'Return exactly {"ready": true} as JSON.'}],
            "format": {"type": "object", "properties": {"ready": {"type": "boolean"}}, "required": ["ready"]},
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 128},
        },
    )
    if json.loads(response["message"]["content"]) != {"ready": True}:
        raise SystemExit("Structured inference check failed.")
    report = {
        "model": args.model,
        "digest": matches[0]["digest"],
        "details": details.get("details"),
        "model_info": details.get("model_info"),
        "seconds": round(time.monotonic() - start, 2),
        "structured_inference": "passed",
    }
    target = Path("private/model-verification.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2))
    print("Verified exact local artifact and inference; report:", target)


if __name__ == "__main__":
    main()
