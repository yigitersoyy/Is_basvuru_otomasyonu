import io
from pathlib import Path

import httpx
from docx import Document
from docx.shared import Inches, Pt
from docxtpl import DocxTemplate
from pypdf import PdfReader

from .domain import digest, fail, normalized


def extract_pdf(data: bytes, ocr: bool = False) -> list[str]:
    if not data.startswith(b"%PDF-"):
        fail("expected a PDF file", 422)
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted or len(reader.pages) > 30:
            fail("CV must be unencrypted and at most 30 pages", 422)
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        from fastapi import HTTPException

        if isinstance(exc, HTTPException):
            raise
        fail("could not parse PDF", 422)
    if ocr and len("".join(pages).strip()) < 50:
        from .ocr import recognize

        pages = recognize(data, len(pages))
    if len("".join(pages).strip()) < 50:
        fail("PDF has insufficient text; enable local OCR or provide a text-based PDF", 422)
    return pages


def make_template(path: Path):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Inches(0.6)
    sec.left_margin = sec.right_margin = Inches(0.65)
    doc.styles["Normal"].font.name = "Liberation Sans"
    doc.styles["Normal"].font.size = Pt(10)
    doc.add_heading("{{ name }}", 0)
    doc.add_paragraph("{{ email }} | {{ location }}")
    doc.add_heading("{{ target_role }}", 1)
    doc.add_paragraph("{%p for section in sections %}")
    doc.add_heading("{{ section.title }}", 2)
    doc.add_paragraph("{%p for item in section['items'] %}")
    doc.add_paragraph("{{ item }}", style="List Bullet")
    doc.add_paragraph("{%p endfor %}")
    doc.add_paragraph("{%p endfor %}")
    doc.save(path)


def render_docx(path: Path, content: dict):
    template = path.parent / "template.docx"
    make_template(template)
    doc = DocxTemplate(template)
    doc.render(content, autoescape=True)
    doc.save(path)
    template.unlink()
    text = " ".join(p.text for p in Document(path).paragraphs)
    if "{{" in text or "{%" in text:
        fail("unresolved template placeholder")
    for section in content["sections"]:
        for item in section["items"]:
            if normalized(item) not in normalized(text):
                fail("document is missing an approved statement")


def render_package(settings, package_id: str, content: dict, convert_pdf=True) -> dict:
    folder = settings.artifact_dir / package_id
    folder.mkdir(parents=True, exist_ok=True)
    docx = folder / "cv.docx"
    render_docx(docx, content)
    manifest = {"docx": {"sha256": digest(docx.read_bytes()), "size": docx.stat().st_size}}
    if convert_pdf:
        try:
            response = httpx.post(
                settings.gotenberg_url + "/forms/libreoffice/convert",
                files={
                    "files": (
                        "cv.docx",
                        docx.read_bytes(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                timeout=60,
            )
            response.raise_for_status()
            if len(response.content) > 2 * 1024 * 1024:
                fail("generated PDF exceeds the 2 MB cap")
            pages = extract_pdf(response.content)
            if len(pages) > 2:
                fail("CV exceeds two pages; reduce approved content before regenerating")
            text = normalized(" ".join(pages))
            for section in content["sections"]:
                for item in section["items"]:
                    if normalized(item) not in text:
                        fail("PDF text does not contain every selected approved statement")
            (folder / "cv.pdf").write_bytes(response.content)
            manifest["pdf"] = {
                "sha256": digest(response.content),
                "size": len(response.content),
                "pages": len(pages),
            }
        except httpx.HTTPError:
            fail("PDF converter unavailable; package was not created", 503)
    return manifest
