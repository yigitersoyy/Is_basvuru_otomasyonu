"""Run inside the API container. Uses synthetic candidate/company data and local Mailpit only."""

import io
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
from career_app.settings import Settings
from docx import Document

s = Settings()
key = s.api_key.get_secret_value()
client = httpx.Client(base_url="http://127.0.0.1:8000", headers={"X-API-Key": key}, timeout=90)


def call(path, data=None):
    r = client.post(path, json=data)
    r.raise_for_status()
    return r.json()


# A real DOCX -> Gotenberg -> PDF -> upload -> approved facts -> tailored PDF cycle.
doc = Document()
source_text = "Alex Example developed Python RAG workflows during a part-time traineeship."
doc.add_paragraph(source_text)
doc.add_paragraph("English C1. Bachelor of Computer Engineering.")
buffer = io.BytesIO()
doc.save(buffer)
r = httpx.post(
    s.gotenberg_url + "/forms/libreoffice/convert",
    files={"files": ("source.docx", buffer.getvalue())},
    timeout=60,
)
r.raise_for_status()
source = client.post("/v1/sources", files={"file": ("synthetic-cv.pdf", r.content, "application/pdf")})
source.raise_for_status()
profile = call(
    "/v1/profiles",
    {
        "name": "Alex Example",
        "email": "alex@example.org",
        "location": "Istanbul",
        "source_id": source.json()["id"],
    },
)
fact = call(
    f"/v1/profiles/{profile['id']}/facts",
    {
        "section": "experience",
        "text": source_text,
        "source_page": 1,
        "source_quote": source_text,
        "tags": ["python", "rag"],
    },
)
call(f"/v1/facts/{fact['id']}/approve")
company = call(
    "/v1/companies",
    {
        "name": "Synthetic Example",
        "domain": uuid.uuid4().hex + ".example.org",
        "country": "NL",
        "source_url": "https://example.org",
    },
)
job = call(
    "/v1/opportunities",
    {
        "company_id": company["id"],
        "external_key": "speculative:ai",
        "title": "Junior AI Engineer",
        "kind": "speculative",
        "role": "applied_ai",
        "description": "Interest in future Python AI integration opportunities",
        "source_url": "https://example.org",
    },
)
contact = call(
    "/v1/contacts",
    {
        "company_id": company["id"],
        "name": "Example Recruiting",
        "email": "careers@example.org",
        "title": "Recruiting",
        "evidence_type": "published_functional",
        "source_url": "https://example.org/careers",
        "source_quote": "Contact careers@example.org",
    },
)
call(f"/v1/contacts/{contact['id']}/confirm")
package = call(
    "/v1/packages", {"profile_id": profile["id"], "opportunity_id": job["id"], "contact_id": contact["id"]}
)
assert package["manifest"]["pdf"]["pages"] <= 2
call(f"/v1/packages/{package['id']}/approve", {"package_hash": package["package_hash"]})
entry = call(f"/v1/packages/{package['id']}/queue")
again = call(f"/v1/packages/{package['id']}/queue")
assert entry["id"] == again["id"]
with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(lambda _: call("/v1/outbox/dispatch-test"), range(2)))
assert sum(x["status"] == "delivered_to_test" for x in results) == 1, results
assert call("/v1/outbox/dispatch-test")["status"] == "idle"
# Verify the accepted message really exists in Mailpit, with the correct Message-ID and attachment.
messages = httpx.get("http://mailpit:8025/api/v1/messages").json()["messages"]
matching = []
for m in messages:
    detail = httpx.get("http://mailpit:8025/api/v1/message/" + m["ID"]).json()
    if detail.get("MessageID", "").strip("<>") == entry["message_id"].strip("<>"):
        matching.append(detail)
assert len(matching) == 1, "Mailpit must contain exactly one copy of the logical message"
assert len(matching[0]["Attachments"]) == 1
print(
    "PASS: PostgreSQL migrations, real PDF roundtrip, review, idempotent queue, concurrent dispatch and Mailpit receipt."
)
print("No external email was sent. Synthetic test package ID:", package["id"])
