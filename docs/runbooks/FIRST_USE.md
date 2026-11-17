The local interface at `http://localhost:8080` implements these actions with forms and review screens. The API paths below are also available for diagnostics and n8n. For live outreach, finish [Gmail setup](GMAIL.md) first; live sending remains disabled until configured.

# First use — v0.2

Start the stack as described in the root README. Open `http://localhost:8000/docs`, authorize with your private `API_KEY`, and use the following API operations in order. Every ID in these steps comes from an actual preceding response.

1. **Upload the CV:** `POST /v1/sources` accepts a text-based PDF up to 10 MB and 30 pages. It returns `id`, `sha256`, and extracted `pages`. Read the extracted text before proceeding. Enable the local OCR checkbox for scanned PDFs. Poppler and Tesseract run locally with page/time limits; review OCR wording against the original.
2. **Create a profile:** `POST /v1/profiles` with your name, email, location and the source ID. Your work history and private contact details are not preloaded in the repository.
3. **Propose facts:** either use `POST /v1/profiles/{id}/propose-facts` with local Ollama running, or enter individual records through `/facts`. AI extraction is optional. For a manual fact, supply a section, self-contained truthful text, exact source quote, 1-based page number and lowercase tags.
4. **Review facts:** list `/v1/profiles/{id}/facts` and compare wording against the cited page. Approve each accepted statement using `/v1/facts/{id}/approve`. Source-quote matching verifies evidence location; it does not certify the meaning of a paraphrase. You must review dates, part-time labels, numbers and disclosure rights.
5. **Create a company:** use `/v1/companies` with an official domain, country code and source URL. Allowed countries: `TR DE AT CH NL DK SE NO GB BE`.
6. **Create an opportunity:** use `/v1/opportunities` with `kind=vacancy` or `speculative`. An `external_key` identifies repeat imports; for a speculative item use a stable label such as `speculative:rag_llm`. Choose a role from `/v1/roles`. Keep `eligibility=unknown` unless your work rights are actually known. Employer public Greenhouse/Ashby boards can also be imported through `/v1/boards/import` after finding the correct board name on the official careers page.
7. **Inspect the assessment:** `/v1/opportunities/{id}/assessment/{profile_id}` explains approved fact coverage and missing tags. The role score is a tag heuristic, supplemented by literal requirement-to-approved-fact mapping with source excerpts and gaps. It does not implement the architecture’s full semantic weighted ranking or measure probability of hire. Missing languages and unknown eligibility remain visible.
8. **Add a contact:** use `/v1/contacts` with source URL, source quote and an appropriate evidence type. Published-contact quotes must include the address. Inspect the source yourself, then call `/confirm`. Published email candidate discovery is available under Company research. It does not invent identities/roles or confirm candidates. No DNS lookup is presented as mailbox validation.
9. **Generate a package:** `/v1/packages` takes profile, opportunity and contact IDs. Only approved CV statements are included, unchanged. It produces JSON content, DOCX, PDF, an email draft and hashes. Missing converter, PDF overflow or missing text blocks package creation.
10. **Review the exact output:** fetch `/v1/packages/{id}`, download both artifacts, read the email, and inspect the opportunity. The initial email template uses up to two experience/project statements and distinguishes speculative interest from a found vacancy. Use `PATCH /v1/packages/{id}` to improve the subject/body. New wording requires your fact check; the API cannot prove it is truthful.
11. **Approve:** send the latest `package_hash` to `/approve`. Stale hashes, changed profiles, revoked facts, changed artifacts, stale contact evidence and suppressions block approval/queueing. Unknown work rights can remain in a manually reviewed introductory inquiry; do not submit mandatory eligibility answers without knowing them. Live sending additionally requires an enabled Gmail account and all live dispatch gates.
12. **Queue and test:** `/queue` creates one logical outbox entry. `/v1/outbox/dispatch-test` sends at most one item to local Mailpit. The message appears at `http://localhost:8025`; its status is `delivered_to_test`, never a claim of real inbox delivery.

## Useful examples

Fact payload (replace the wording with material actually present in your CV):

```json
{
  "section": "experience",
  "text": "AI Agent Trainee (Part-time), Oct 2025 – Jul 2026. Built local reporting workflows.",
  "source_page": 1,
  "source_quote": "AI Agent Trainee (Part-time)",
  "tags": ["ollama", "reporting", "automation"]
}
```

The quote itself must appear on the cited page. The rest of the fact needs your explicit review before approval.

Speculative opportunity payload:

```json
{
  "company_id": "ID_FROM_COMPANY_RESPONSE",
  "external_key": "speculative:rag_llm",
  "title": "Future RAG integration opportunities",
  "kind": "speculative",
  "role": "rag_llm",
  "description": "Interest in future AI integration work; no vacancy has been established.",
  "source_url": "https://example.org",
  "eligibility": "unknown",
  "required_languages": []
}
```

## Changes and pauses

- Approving or revoking profile facts increments the profile revision and invalidates existing packages for that profile. Finish fact review before generating packages.
- Editing the email clears package approval and cancels pending work. Approve the new hash before queueing again.
- An attempted/uncertain package is immutable; prepare a new version only after resolving the previous outcome.
- `/v1/outbox/pause` persists a global dispatch pause and cancels pending entries. `/resume-test` clears the global pause; Gmail still requires its separately enabled live setting. In-flight attempts cannot be recalled.
- Suppress a contact or company using `/v1/suppressions`. This cancels affected pending items and blocks future queueing.
- Interrupted attempts older than five minutes become `send_unknown` through `/v1/outbox/recover`. They are never automatically retried. Use Gmail synchronization to reconcile an uncertain live attempt; never force a resend.

No automatic facts are imported from public profile sites, no work rights are assumed, and no original CV is committed to Git.
