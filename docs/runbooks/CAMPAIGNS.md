# Bounded campaigns and manual applications

Create a campaign under **Campaigns & applications** with a profile, countries, roles, coverage threshold and explicit mode/enabled setting. Each run considers at most 200 stored opportunities and returns a bounded preparation batch; it does not claim to discover every employer on the internet.

- `draft_only` and `review_each` prepare packages for exact review; neither approves or queues automatically.
- `policy_auto` may approve and queue the deterministic approved-content lane. Required eligibility/language/seniority blockers and detected mandatory skill gaps remain in review. Contacts must already be explicitly confirmed, current and unsuppressed. Novel model prose is never automatically approved.
- Runs persist prepared package IDs by opportunity/profile revision. Repeated runs do not create duplicate packages for the same campaign input. Pausing the campaign cancels its queued packages; the global pause remains available independently.
- Queueing retains exact hash validation, one active company sequence, uncertain-send holds and a 60-day cooldown after a successful first contact. The one reviewed follow-up can refer to its original sequence. Gmail live enablement, synchronization, national holidays, recipient-local windows, spacing and daily cap remain separate send gates.

Research official sources and inspect published contact candidates under **Companies & research**. Candidate discovery never invents a name/title or confirms an address. Add the actual identity, professional role and source evidence in Contacts, then confirm after review. A missing professional email produces a manual-contact route. Source-based requirement mapping shows literal technology mentions, exact description excerpts, supporting approved fact IDs and gaps; it cannot prove experience depth or hiring probability. Speculative opportunities do not acquire invented vacancy requirements.

`Career Run Campaign` is an inactive authenticated n8n webhook workflow. Supply `{"campaign_id":"campaign:UUID"}` after binding local inbound/API credentials. Choose a schedule in your local n8n instance only after enabling the intended policy. Discovery failures, source restrictions and missing contacts require review; no paid enrichment service is used.

For unsupported employer portals, use the handoff screen and authenticated package downloads. Complete the real form yourself, including legal attestations and unknown work-rights answers. Record the actual reference and timestamp afterward. Email acceptance, queueing and test delivery never change portal status to submitted. A recorded portal confirmation is explicitly user-supplied evidence, not an automatically verified employer receipt.

National holiday calendars cover the ten target countries; regional and employer-specific closures still need review. New-subject messages from an exact current contact after the send time conservatively stop that company sequence and create a response task. Ambiguous aliases/forwarded messages and messages older than the bounded 30-day search still require Gmail inspection. No classifier makes salary, interview or legal commitments for you.
