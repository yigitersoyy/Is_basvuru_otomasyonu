"""Bounded local OCR; extracted wording remains unapproved until source review."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from .domain import fail


def recognize(data: bytes, count: int) -> list[str]:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        fail(
            "OCR requires local poppler-utils and tesseract-ocr; install them or upload a text-based PDF", 503
        )
    if not 1 <= count <= 30:
        fail("OCR supports 1–30 pages", 422)
    try:
        with tempfile.TemporaryDirectory(prefix="career-ocr-") as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(data)
            pages = []
            for page in range(1, count + 1):
                image = root / "page"
                subprocess.run(
                    [
                        "pdftoppm",
                        "-f",
                        str(page),
                        "-l",
                        str(page),
                        "-singlefile",
                        "-scale-to",
                        "2400",
                        "-png",
                        str(source),
                        str(image),
                    ],
                    check=True,
                    timeout=30,
                    capture_output=True,
                )
                result = subprocess.run(
                    ["tesseract", str(image.with_suffix(".png")), "stdout", "-l", "eng"],
                    check=True,
                    timeout=30,
                    capture_output=True,
                )
                pages.append(result.stdout.decode("utf-8", errors="replace"))
            return pages
    except (subprocess.SubprocessError, OSError):
        fail("Local OCR failed or timed out; provide a corrected PDF", 422)
