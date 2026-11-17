"""Existing Streamlit widgets provide the local UI; secrets stay on the server."""

import os

import httpx
import streamlit as st

st.set_page_config(page_title="Career Workspace", page_icon="📄", layout="wide")
api = httpx.Client(
    base_url=os.getenv("API_URL", "http://api:8000"),
    headers={"X-API-Key": os.environ["API_KEY"]},
    timeout=300,
)


def call(method, path, **kwargs):
    try:
        response = api.request(method, path, **kwargs)
        if response.is_error:
            st.error(response.json().get("detail", "Request failed"))
            st.stop()
        return response.json()
    except httpx.HTTPError:
        st.error("Workspace API unavailable. Check that the API and database are running.")
        st.stop()


def choose(label, rows, key):
    if not rows:
        st.info("Create the preceding records first.")
        st.stop()
    return st.selectbox(
        label,
        rows,
        format_func=lambda r: r.get("name") or r.get("title") or r.get("subject") or r["id"],
        key=key,
    )


st.title("Career Workspace")
st.caption("Prepare factual applications, review each package and manage your outreach.")
page = st.sidebar.radio(
    "Workspace",
    [
        "Overview",
        "AI settings",
        "Campaigns & applications",
        "CV & facts",
        "Companies & research",
        "Opportunities",
        "Contacts",
        "Review & outbox",
        "Gmail & conversations",
    ],
)
if st.sidebar.button("Pause all sending"):
    call("POST", "/v1/outbox/pause")
    st.sidebar.success("Sending paused; pending messages cancelled.")
if page == "Overview":
    data = call("GET", "/v1/overview")
    if st.button("Check setup readiness"):
        st.json(call("GET", "/v1/operations/readiness"))
    st.json(data["counts"])
    st.dataframe(data["outbox"], use_container_width=True)
    st.info(
        "Gmail requires your own OAuth connection and explicit live configuration. Local test messages remain in Mailpit."
    )
elif page == "Campaigns & applications":
    st.subheader("Campaign policy")
    profiles = call("GET", "/v1/profiles")
    if profiles:
        with st.form("campaign"):
            profile = choose("Candidate profile", profiles, "campaign_profile")
            name = st.text_input("Campaign name")
            mode = st.selectbox("Mode", ["draft_only", "review_each", "policy_auto"])
            countries = st.multiselect(
                "Countries", ["TR", "DE", "AT", "CH", "NL", "DK", "SE", "NO", "GB", "BE"], default=["TR"]
            )
            roles = st.multiselect(
                "Role families",
                list(call("GET", "/v1/roles")),
                default=["applied_ai", "rag_llm", "automation"],
            )
            coverage = st.slider("Minimum approved fact role coverage", 0, 100, 60)
            enabled = st.checkbox(
                "Enable this policy (policy_auto may approve and queue unchanged approved content)"
            )
            if st.form_submit_button("Create campaign"):
                st.json(
                    call(
                        "POST",
                        "/v1/campaigns",
                        json={
                            "name": name,
                            "profile_id": profile["id"],
                            "mode": mode,
                            "countries": countries,
                            "roles": roles,
                            "minimum_coverage": coverage,
                            "enabled": enabled,
                        },
                    )
                )
    campaigns = call("GET", "/v1/campaigns")
    if campaigns:
        selected = choose("Saved campaign", campaigns, "selected_campaign")
        if st.button("Run bounded preparation"):
            st.json(call("POST", f"/v1/campaigns/{selected['id']}/run"))
        if st.button("Pause this campaign and cancel queued packages"):
            st.json(call("POST", f"/v1/campaigns/{selected['id']}/pause"))
    st.subheader("Employer portal handoff")
    packages = call("GET", "/v1/packages")
    if packages:
        package = choose("Package", packages, "portal_package")
        st.json(call("GET", f"/v1/packages/{package['id']}/portal-handoff"))
        st.caption(
            "Download the reviewed files under Review & outbox. Complete unsupported portals manually."
        )
        with st.form("portal_confirmation"):
            reference = st.text_input("Actual submission confirmation/reference")
            timestamp = st.text_input(
                "Submission time (ISO 8601 with timezone)", placeholder="2026-11-17T14:00:00+03:00"
            )
            if st.form_submit_button("Record my completed portal submission"):
                st.json(
                    call(
                        "POST",
                        f"/v1/packages/{package['id']}/portal-submission",
                        json={"reference": reference, "submitted_at": timestamp},
                    )
                )
elif page == "AI settings":
    current = call("GET", "/v1/ai/settings")
    st.info(
        "Local inference is the default. API mode sends CV text to your selected provider and may incur charges. No automatic fallback is used."
    )
    with st.form("ai_selection"):
        provider = st.selectbox(
            "Provider",
            ["ollama", "openai_compatible"],
            index=["ollama", "openai_compatible"].index(current["provider"]),
        )
        model = st.text_input("Ollama model", current["ollama_model"])
        endpoint = st.text_input("API base URL (must match local AI_API_URL)", current["api_url"])
        api_model = st.text_input("API model", current["api_model"])
        enabled = st.checkbox(
            "I explicitly allow API requests and any provider charges", value=current["api_enabled"]
        )
        st.caption(
            "Set AI_API_KEY and AI_API_URL in your private .env, then recreate the API. Keys are never displayed or accepted here."
        )
        st.write("API key configured:", current["api_key_configured"])
        if st.form_submit_button("Save AI selection"):
            call(
                "PUT",
                "/v1/ai/settings",
                json={
                    "provider": provider,
                    "ollama_model": model,
                    "api_enabled": enabled,
                    "api_url": endpoint,
                    "api_model": api_model,
                },
            )
            st.success("Selection saved; no inference request was made.")
elif page == "CV & facts":
    ocr = st.checkbox("Use local OCR if the PDF has no selectable text (review every extracted fact)")
    uploaded = st.file_uploader("Upload your text-based CV", type=["pdf"])
    if uploaded and st.button("Import PDF"):
        st.session_state["source"] = call(
            "POST",
            "/v1/sources",
            params={"ocr": ocr},
            files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
        )
    source = st.session_state.get("source")
    if source:
        st.json(source)
        with st.form("profile"):
            name = st.text_input("Full name")
            email = st.text_input("Email")
            location = st.text_input("Location")
            if st.form_submit_button("Create profile"):
                call(
                    "POST",
                    "/v1/profiles",
                    json={"name": name, "email": email, "location": location, "source_id": source["id"]},
                )
                st.success("Profile created")
    profile = choose("Profile", call("GET", "/v1/profiles"), "profile")
    if st.button("Propose facts with local Ollama"):
        with st.spinner("Reading locally; proposals will need review..."):
            call("POST", f"/v1/profiles/{profile['id']}/propose-facts")
            st.rerun()
    source = call("GET", f"/v1/sources/{profile['source_id']}")
    with st.expander("Read original CV pages"):
        st.json(source["pages"])
    with st.form("fact"):
        section = st.selectbox(
            "Section", ["experience", "skills", "projects", "education", "languages", "summary"]
        )
        text = st.text_area("Truthful self-contained statement")
        quote = st.text_area("Exact source quote")
        number = st.number_input("Source page", min_value=1, step=1)
        tags = st.text_input("Tags, comma separated")
        if st.form_submit_button("Add for review"):
            call(
                "POST",
                f"/v1/profiles/{profile['id']}/facts",
                json={
                    "section": section,
                    "text": text,
                    "source_quote": quote,
                    "source_page": number,
                    "tags": [x.strip().lower() for x in tags.split(",") if x.strip()],
                },
            )
            st.rerun()
    for fact in call("GET", f"/v1/profiles/{profile['id']}/facts"):
        with st.expander(("Approved: " if fact["approved"] else "Review: ") + fact["text"][:100]):
            st.write(fact["text"])
            st.caption(f"Page {fact['source_page']}: {fact['source_quote']}")
            action = "revoke" if fact["approved"] else "approve"
            if st.button(action.title(), key=fact["id"]):
                call("POST", f"/v1/facts/{fact['id']}/{action}")
                st.rerun()
elif page == "Companies & research":
    query = st.text_input("Discover companies or vacancies", value="junior RAG AI engineer Netherlands")
    if st.button("Search public sources"):
        st.json(call("GET", "/v1/discovery/search", params={"query": query}))

    with st.form("company"):
        name = st.text_input("Company name")
        domain = st.text_input("Official domain (example.com)")
        country = st.selectbox("Country", ["TR", "DE", "AT", "CH", "NL", "DK", "SE", "NO", "GB", "BE"])
        url = st.text_input("Official company/source HTTPS URL")
        if st.form_submit_button("Add company"):
            call(
                "POST",
                "/v1/companies",
                json={"name": name, "domain": domain, "country": country, "source_url": url},
            )
            st.rerun()
    company = choose("Company", call("GET", "/v1/companies"), "research_company")
    if st.button("Research official source"):
        with st.spinner("Reading bounded public source..."):
            st.json(call("POST", f"/v1/companies/{company['id']}/research"))
    if st.button("Discover published contact candidates"):
        st.json(call("POST", f"/v1/companies/{company['id']}/discover-contacts"))
    st.caption(
        "Published emails still need source review and contact confirmation. Research never guesses addresses."
    )
elif page == "Opportunities":
    company = choose("Company", call("GET", "/v1/companies"), "job_company")
    roles = call("GET", "/v1/roles")
    with st.form("opportunity"):
        title = st.text_input("Role/title")
        kind = st.selectbox("Type", ["speculative", "vacancy"])
        role = st.selectbox("Role family", list(roles))
        external = st.text_input("Stable reference", value="speculative:ai")
        description = st.text_area("Job description or sourced company-fit notes")
        url = st.text_input("Source URL")
        eligibility = st.selectbox("Work eligibility", ["unknown", "eligible", "ineligible"])
        languages = st.text_input("Mandatory languages, comma separated")
        if st.form_submit_button("Save opportunity"):
            call(
                "POST",
                "/v1/opportunities",
                json={
                    "company_id": company["id"],
                    "title": title,
                    "kind": kind,
                    "role": role,
                    "external_key": external,
                    "description": description,
                    "source_url": url,
                    "eligibility": eligibility,
                    "required_languages": [x.strip() for x in languages.split(",") if x.strip()],
                },
            )
            st.rerun()
    with st.form("board"):
        provider = st.selectbox("Public ATS", ["greenhouse", "ashby"])
        board = st.text_input("Official board identifier")
        family = st.selectbox("Role family for imported board", list(roles))
        if st.form_submit_button("Import listed jobs"):
            st.json(
                call(
                    "POST",
                    "/v1/boards/import",
                    json={"company_id": company["id"], "provider": provider, "board": board, "role": family},
                )
            )
    st.dataframe(call("GET", "/v1/opportunities"), use_container_width=True)
elif page == "Contacts":
    company = choose("Company", call("GET", "/v1/companies"), "contact_company")
    with st.form("contact"):
        name = st.text_input("Person or recruiting team")
        email = st.text_input("Published professional email")
        title = st.text_input("Professional role")
        url = st.text_input("Evidence URL")
        quote = st.text_area("Evidence quote including address")
        evidence = st.selectbox(
            "Evidence type",
            ["published_named", "published_functional", "user_confirmed", "inferred_or_unconfirmed"],
        )
        if st.form_submit_button("Add contact"):
            call(
                "POST",
                "/v1/contacts",
                json={
                    "company_id": company["id"],
                    "name": name,
                    "email": email,
                    "title": title,
                    "source_url": url,
                    "source_quote": quote,
                    "evidence_type": evidence,
                },
            )
            st.rerun()
    for c in call("GET", "/v1/contacts"):
        with st.expander(c["name"] + " — " + c["email"]):
            st.write(c["source_url"])
            st.write(c["source_quote"])
            if st.button("Confirm reviewed evidence", key="confirm" + c["id"]):
                call("POST", f"/v1/contacts/{c['id']}/confirm")
                st.success("Confirmed")
            if st.button("Do not contact", key="suppress" + c["id"]):
                call(
                    "POST",
                    "/v1/suppressions",
                    json={"scope": "email", "value": c["email"], "reason": "User requested suppression"},
                )
                st.success("Suppressed")
elif page == "Review & outbox":
    profile = choose("Profile", call("GET", "/v1/profiles"), "prep_profile")
    job = choose("Opportunity", call("GET", "/v1/opportunities"), "prep_job")
    contacts = [c for c in call("GET", "/v1/contacts") if c["company_id"] == job["company_id"]]
    contact = choose("Relevant contact", contacts, "prep_contact")
    st.json(call("GET", f"/v1/opportunities/{job['id']}/assessment/{profile['id']}"))
    if st.button("Generate CV and email"):
        with st.spinner("Rendering and checking documents..."):
            call(
                "POST",
                "/v1/packages",
                json={"profile_id": profile["id"], "opportunity_id": job["id"], "contact_id": contact["id"]},
            )
            st.rerun()
    packages = call("GET", "/v1/packages")
    if packages:
        p = choose("Package", packages, "review_package")
        st.write("Recipient:", p["recipient"])
        st.write("Status:", p["status"])
        for ext in ["pdf", "docx"]:
            r = api.get(f"/v1/packages/{p['id']}/artifacts/{ext}")
            if r.is_success:
                st.download_button(
                    "Download " + ext.upper(), r.content, file_name="CV." + ext, key=p["id"] + ext
                )
        with st.form("edit" + p["id"]):
            subject = st.text_input("Subject", p["subject"])
            body = st.text_area("Email", p["body"], height=240)
            if st.form_submit_button("Save changes and invalidate approval"):
                call("PATCH", f"/v1/packages/{p['id']}", json={"subject": subject, "body": body})
                st.rerun()
        if st.button("Approve this exact email and CV"):
            call("POST", f"/v1/packages/{p['id']}/approve", json={"package_hash": p["package_hash"]})
            st.rerun()
        if st.button("Queue approved package"):
            st.json(call("POST", f"/v1/packages/{p['id']}/queue"))
    st.dataframe(call("GET", "/v1/outbox"), use_container_width=True)
    if st.button("Deliver next package to local test mailbox"):
        st.json(call("POST", "/v1/outbox/dispatch-test"))
else:
    status = call("GET", "/v1/gmail/status")
    st.json(status)
    if st.button("Connect my Gmail"):
        result = call("POST", "/v1/gmail/connect")
        st.link_button("Authorize with Google", result["url"])
    if st.button("Synchronize replies"):
        st.json(call("POST", "/v1/gmail/sync"))
    if st.button("Prepare due follow-ups for review"):
        st.json(call("POST", "/v1/followups/plan"))
    if st.button("Resume local/live dispatch policy"):
        st.json(call("POST", "/v1/outbox/resume-test"))
    if st.button("Send next approved package through Gmail"):
        st.json(call("POST", "/v1/gmail/dispatch"))
    if st.button("Disconnect Gmail"):
        st.json(call("POST", "/v1/gmail/disconnect"))
    st.dataframe(call("GET", "/v1/conversations"), use_container_width=True)
