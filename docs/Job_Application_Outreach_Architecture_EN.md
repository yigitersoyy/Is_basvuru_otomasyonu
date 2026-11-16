# Yiğit Ersoy — Job Application and Outreach System

**Detailed architecture and implementation plan**  
**Prepared:** 16 November 2026  
**Status:** Planning complete; implementation requires your next instruction.

This proposal is tailored to your uploaded two-page CV, your Windows 11 computer with 32 GB RAM and an RTX 4060, your Gmail account, and your interest in Türkiye and selected European countries. It uses existing applications for orchestration, local AI, the interface, document conversion, and storage. Custom work is limited to connecting these applications and enforcing application-specific rules.

The intended outcome is a personal application that finds suitable companies and vacancies, selects a relevant role, prepares a truthful CV version for each opportunity, identifies an appropriate professional contact, sends a personalized introduction under your configured rules, and tracks replies and follow-ups. A vacancy is optional.

The architecture has **no required software subscription, paid LLM API, purchased contact database, or paid hosting**. Existing hardware, electricity, internet access, storage, maintenance time, and a provider-permitted Gmail account are still required. Free software does not provide unlimited email delivery, guaranteed contact discovery, or continuous operation while the computer is off.

## 1. Decisions and scope

| Area | Decision |
|---|---|
| Intended user | One person: Yiğit Ersoy. This is a personal system, not a public recruitment SaaS. |
| Computer | Windows 11, 32 GB RAM, RTX 4060. Confirm actual VRAM, free disk space, and CPU during setup. |
| Runtime | Docker Desktop for personal use, WSL 2, and Docker Compose. |
| Main interface | Self-hosted Appsmith Community Edition. |
| Workflow engine | Self-hosted n8n Community Edition. |
| AI inference | Local Ollama with a quantized Qwen3 8B model initially; 4B fallback. |
| Business records | PostgreSQL, separate from n8n's internal database. |
| CV documents | One controlled DOCX template, filled with docxtpl, converted to PDF by Gotenberg. |
| Email | Gmail API through OAuth; one sender and one recipient per message. |
| Discovery | Official company websites, public job-board endpoints, permitted feeds, user-supplied links, and optional self-hosted SearXNG. |
| Operating modes | Draft only; review each message; automatic sending within an explicitly enabled campaign policy. |
| Languages | English by default for Europe. Turkish or English for Türkiye according to the source and campaign. |
| Countries | Türkiye, Germany, Austria, Switzerland, Netherlands, Denmark, Sweden, Norway, United Kingdom, Belgium. |
| Starting boundary | Produce the architecture now. Deployment, account authorization, CV production, and outreach are later implementation work. |

Scandinavia is interpreted as Denmark, Sweden, and Norway. Finland and Iceland can be enabled as a separate Nordic expansion; they are not silently added to the initial scope.

An email introduction and a formal application are separate events. The system must never mark an employer's application form as submitted merely because it emailed someone at that employer.

## 2. Positioning derived from your CV

### 2.1 What the supplied CV supports

The CV reports a Computer Engineering degree completed in July 2026, an AI Agent Trainee position at YEO from October 2025 to July 2026, and a Data Analyst Internship at ITserv from April 2024 to January 2025. Both jobs are explicitly part-time. It also reports Turkish and C1 English.

Its strongest differentiator is the combination of **enterprise AI implementation, document workflows, local LLMs, and Microsoft business automation**. Your research and local hardware experiments reinforce that positioning.

The following are evidence categories imported from the CV, rather than independently verified claims:

| Evidence | Where it is useful |
|---|---|
| Canias ERP reporting using on-premise Ollama; reported 75% shorter manual reporting cycles | Applied AI, local LLM integration, enterprise reporting, industrial software |
| Contract and BOQ agent with source citations; reported 60% faster review workflows | Document intelligence, retrieval, legal/industrial workflow software |
| CV matching and employee-support agents | AI automation, internal tools, HR technology |
| Power Apps, Power Automate, SharePoint, Teams, Copilot Studio | Junior Power Platform and enterprise AI implementation positions |
| SQL, ETL and Python analysis of 50,000+ records at ITserv | Junior data analysis, BI and selected data integration positions |
| IEEE SIU 2026 research involving latent diffusion and BiLSTM | Selected graduate applied ML and research engineering roles |
| Local RAG experiments using Ollama, LangChain, FAISS and Chroma | Junior RAG/LLM engineering and integration roles |

Before these claims become an approved reusable fact bank, you review their wording and measurement context once. Employer-confidential details stay out of outreach. Publication identifiers and public project links can be added if available; the system must not invent them.

### 2.2 Recommended target roles

| Priority | Role family and search titles | Positioning and boundary |
|---|---|---|
| Primary | Junior AI Engineer; Associate AI Engineer; Graduate Applied AI Engineer; Junior Generative AI Engineer | Strongest overall fit. Emphasize implemented business workflows and local AI. |
| Primary | Junior LLM Engineer; RAG Engineer; AI Integration Engineer; Junior GenAI Developer | Emphasize retrieval, document processing, Python APIs, local inference and evaluation. Treat extensive production infrastructure requirements individually. |
| Primary | AI Automation Engineer; Intelligent Automation Developer; Junior AI Solutions Engineer | Connect n8n, document pipelines and enterprise automation to business outcomes. |
| Strong secondary | Junior Copilot Studio Developer; Power Platform Developer; Junior Power Platform Consultant; Microsoft AI Solutions Developer | Strong match to concrete YEO work. The employer may use licensed Microsoft products; this personal application does not need those subscriptions. |
| Selective secondary | Junior Data Analyst; BI Analyst; Junior Power BI Developer; Reporting Analyst | Use the ITserv experience, SQL, Python, ETL and reported BI skills. Distinguish listed skills from demonstrated project achievements. |
| Selective stretch | Graduate ML Engineer; Junior Applied ML Engineer; Research Engineer, entry level | Use the diffusion/BiLSTM work. Check degree and research requirements; do not assume eligibility for PhD-only posts. |

Initial research allocation: approximately 40% applied AI/GenAI, 25% RAG/LLM integration, 20% AI automation/Power Platform, 10% analytics/BI, and 5% graduate applied ML. These are starting preferences, not predicted success rates. Deduplicate overlapping job titles before allocating effort.

Avoid automatically pursuing senior, lead, principal, architect, or management roles. Do not present part-time trainee and internship experience as several years of full-time engineering employment. Consider ambiguous mid-level listings only when their actual requirements fit.

### 2.3 Reusable CV families

Create four approved content families from the same facts:

1. **Applied AI and RAG:** local LLMs, contract intelligence, retrieval, Python, FastAPI and research.
2. **AI automation and Microsoft ecosystem:** Copilot Studio, Power Automate, Power Apps, SharePoint and internal agents.
3. **Data and BI:** SQL, ETL, Python analysis, reporting, relevant data skills and ERP work.
4. **Graduate applied ML:** PyTorch, BiLSTM, latent diffusion, evaluation methodology, publication and research projects.

Each application gets a version selected from one family, then adapted to the specific opportunity. The company version must not overwrite the master CV or become the source for later factual claims.

### 2.4 Company types to prioritize

Start with industrial and energy software companies, enterprise software vendors, AI implementation consultancies, Microsoft partners, internal-tools teams, document-intelligence products, and companies building private or on-premise AI. HR technology and contract-processing companies are relevant when the actual work matches your experience.

Startups with a clear AI integration need are suitable for founder or CTO introductions. Larger employers usually justify a recruiter, relevant hiring manager, Head of AI, or Head of Automation contact instead of the CEO.

This plan does not claim that any particular company is currently hiring or sponsoring relocation. Those are discovery outputs to substantiate during operation.

## 3. Country, language and eligibility routing

Use the following as research strategies, not blanket claims about national employment markets.

| Country group | Initial targeting strategy | Required opportunity checks |
|---|---|---|
| Türkiye | AI teams, industrial technology, enterprise automation, Microsoft partners; Turkish and English searches | Location, working arrangement, role level, language and candidate availability |
| Germany and Austria | English-speaking technical teams, industrial software, applied AI and enterprise integrations | Whether German is mandatory; work authorization and employer relocation support |
| Switzerland | International technical teams and closely matched applied AI roles | Canton/location, actual language requirements, permit feasibility and employer support |
| Netherlands | International product teams, AI consultancies and enterprise software | Actual English-language suitability; work route; recognized-sponsor register as one signal |
| Denmark, Sweden and Norway | International technical teams, industrial AI and automation | Country-specific permit route, local language requirements and location restrictions |
| United Kingdom | Graduate/associate AI, automation and data roles | Existing right to work or relevant sponsorship; employer register entry and role-specific willingness |
| Belgium | International software and enterprise AI teams | English versus mandatory Dutch/French, region, work route and relocation support |

Keep English as your supported application language in Europe because the CV reports C1 English. Search queries may use local-language job titles, but that must not cause the system to claim you speak those languages. Translate a submission into another language only under an explicit campaign choice and a suitable quality review.

For each opportunity store: country, city, timezone, working arrangement, employment type, required languages, required experience, mandatory skills, work-authorization restriction, sponsorship evidence, relocation evidence, compensation if published, and source/date for each.

Your citizenship, country-specific work permissions, willingness to relocate, salary expectations and availability are **unknown until you supply them**. Istanbul residence and Turkish language do not establish citizenship or European work rights. An English advertisement does not imply sponsorship, and a remote position does not necessarily permit working from Türkiye.

Use three-valued checks: `eligible`, `ineligible`, and `unknown`. Unknown values create a visible information task; the model cannot turn them into a positive answer. An introductory inquiry may use neutral wording that makes no work-rights claim, if allowed by the campaign. Formal applications requiring eligibility answers remain pending until those answers are known.

The [UK licensed sponsor register](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) and [Netherlands IND work register](https://ind.nl/en/public-register-recognised-sponsors/public-register-work) are useful free sources. Presence in a register is not a promise to sponsor this vacancy; absence must not be treated as a universal immigration ruling, especially where nationality-specific exceptions or other routes apply. Store entity-match confidence and consult current official requirements when a specific opportunity requires them.

## 4. Application stack and actual cost boundaries

| Component | Selected application | Purpose and free-use boundary |
|---|---|---|
| Containers | Docker Desktop + WSL 2 + Compose | Free for your personal use; no hosted server required. |
| Interface | Appsmith Community Edition | Existing login, forms, tables, actions and dashboards. Explicitly select the CE image; no Appsmith AI or paid UI feature is required. |
| Orchestration | n8n Community Edition | Scheduling, APIs, email integration and workflow branches. Free self-hosted use under its Sustainable Use License; not an OSI open-source license. |
| Inference | Ollama + Qwen3 8B Q4 | Local model execution without token charges. Qwen3 model license and exact artifact must be recorded. |
| Database | PostgreSQL | Authoritative structured records, transactions, uniqueness and work queues. |
| Search | SearXNG, optional | Self-hosted metasearch. Upstream engines can block or change behavior; this is not a guaranteed unlimited search API. |
| Extraction | pypdf/pdfplumber, python-docx, Trafilatura | Parse documents and permitted public page content in a small utility service. |
| Scanned documents | OCRmyPDF + Tesseract, on demand | Fallback when text extraction fails; not needed for the supplied text-based CV. |
| CV generation | docxtpl + a controlled DOCX template | Fill a template using structured, checked content. |
| PDF conversion | Gotenberg with LibreOffice | Convert DOCX to searchable PDF locally. |
| Email | Personal Gmail + Gmail API | Standard API use within current free limits; mailbox rules and sending restrictions still apply. |
| Test mailbox | Mailpit, development only | Inspect generated messages locally without contacting companies. |
| Backup | PostgreSQL tools + restic + an existing second storage location | Encrypted backup software is free; independent storage must already exist or be provided. |
| Monitoring | n8n error workflow, PostgreSQL health records, Docker health checks; optional Uptime Kuma | Basic monitoring needs no paid observability platform. |

One small Python utility service, using FastAPI and established libraries, handles document parsing, rendering, validation and protected artifact access. This is integration work rather than a custom frontend, workflow engine, email server or AI framework. PostgreSQL functions enforce business transitions. Appsmith supplies the UI; n8n supplies orchestration.

No paid contact providers, automation subscriptions, hosted vector database, public file-storage subscription, Microsoft API subscription or paid LLM fallback is necessary. Existing public portfolio URLs can be referenced after you approve them.

The main non-subscription costs are electricity, internet, SSD capacity and your time. Electricity should be estimated from measured incremental power, operating hours and your tariff. If no second backup location exists, a second folder on the same drive cannot provide protection against drive loss.

Current Gmail documentation states that standard API use has no additional cost and also describes a billing threshold and planned overage charging. Keep the project without a linked billing account where supported, avoid chargeable services, and enforce a local request budget. Recheck this at implementation; stop on any billing requirement rather than silently enabling payment. Mailbox sending limits are separate from API quotas. [Sources 6–9]

## 5. System architecture

```text
                    YOUR LOCAL WINDOWS COMPUTER

  Browser -> Appsmith CE -> authenticated n8n commands
                |                    |
                | read-only views    +--> PostgreSQL business database
                v                    +--> Ollama: local inference
            PostgreSQL               +--> document utility -> Gotenberg
                                     +--> approved artifact directory
                                     +--> public-source research adapters
                                     +--> Gmail API: send and read replies

  Public company/ATS pages -> extraction -> evidence -> role matching
  CV + your corrections   -> approved facts -> tailored CV + email
  Validated package       -> campaign/review decision -> durable outbox
  Gmail replies/bounces   -> event log -> stop/reschedule -> dashboard

  Database + files + settings -> encrypted backup on separate storage
```

The LLM produces suggestions and structured text. It does not have Gmail credentials, unrestricted database access, or the power to send mail. Deterministic workflow checks decide whether a message can reach the outbox.

The initial design contract is one local user, approximately 20 newly researched companies per active day, one inference task at a time and at most ten outreach messages per day. These are capacity targets to benchmark, not quotas the machine must achieve. The core private HTTP contracts are document import/extraction, schema validation, DOCX rendering, artifact retrieval and health checks. Each receives a correlation ID and authenticated request; mutable actions also receive an idempotency key. n8n owns orchestration and database transitions, while the utility service owns file handling. Routine operations should return structured errors with retryability rather than unstructured text.

### 5.1 Trust and storage boundaries

- Appsmith's account and configuration data remain in its own persisted application stack. Its bundled databases/cache are separate from the career database.
- One PostgreSQL service holds separate databases and credentials for `n8n_internal` and `career_app`. Workflows never query or modify n8n's internal tables directly.
- Appsmith reads restricted database views. Actions call authenticated n8n webhook endpoints; they do not directly set an outbox row to `sent` or bypass validation.
- The document service has access to its document directory but no Gmail token. Document IDs resolve to controlled paths; requests cannot supply arbitrary filesystem paths.
- Public-page fetching uses a restricted adapter. Browser rendering, when necessary, runs separately without Gmail credentials or private CV storage mounted.
- Source pages, model output, documents and incoming emails are untrusted input. None can redefine system instructions or enable tools.
- Only local browser-facing services are exposed on loopback. PostgreSQL, Ollama, Gotenberg and utility ports remain on private container networks.
- Email content and an attached CV leave the computer when sent through Gmail. Public search queries leave the computer through their selected engines. Candidate profiles are not uploaded to a hosted LLM.

### 5.2 Windows deployment design

Use WSL 2 and Linux containers. Store database volumes and working artifacts in the Linux filesystem or Docker volumes, rather than putting active database files under `/mnt/c`. Export finished documents to a convenient Windows directory through a controlled download/export action.

Use the RTX 4060 through Docker Desktop's supported Windows/WSL 2 GPU path. Verify the NVIDIA driver, WSL support, GPU visibility and actual VRAM before selecting the model settings. Assume an approximately 8 GB GPU only for initial planning; `nvidia-smi` is the setup check.

Start with a WSL memory budget of approximately 18–20 GB, then measure. Reserve the remaining RAM for Windows and the browser. Suggested planning allowances are 6–8 GB for Appsmith and its bundled services, 1–2 GB for n8n, 1–2 GB for PostgreSQL, 2–4 GB combined for document processing and research, and additional CPU memory for Ollama. These are estimates, not fixed reservations or vendor performance guarantees. Keep at least 60–100 GB free initially for images, models, logs and document history, then measure growth.

GPU inference concurrency starts at one. OCR, browser rendering and PDF conversion are also bounded so a discovery burst cannot exhaust the machine. Do not keep LM Studio or another large model loaded simultaneously during scheduled inference.

If GPU container access cannot be made reliable, the fallback is native Windows Ollama with a private Docker-to-host connection and restrictive Windows Firewall rules, or CPU inference with a smaller model. A paid cloud model is never an automatic fallback.

Windows Task Scheduler starts the local stack in the supported user session; Docker restart policies recover services after process restarts. Startup and Windows Update recovery must be tested. A laptop that is asleep or shut down cannot monitor replies or send messages. On resume, inbox synchronization runs before sending, and overdue messages are spread over future slots rather than sent in a burst.

## 6. Local model configuration

Use an explicitly pinned, downloaded Qwen3 8B Q4 artifact as the first candidate. The official Ollama listing currently describes `qwen3:8b` as about 5.2 GB of weights; runtime memory also includes the context cache and other overhead. Record the resolved model digest because a tag can change. [Sources 4–5]

Initial settings: one request at a time, non-thinking generation where supported, low temperature, structured JSON output, bounded output length, and a 4K context to start. Move to 8K only if memory and quality measurements justify it. Prepare compact evidence bundles instead of passing whole websites or the entire mailbox.

Set `OLLAMA_NO_CLOUD=1`, verify the local-only startup message, and allow only approved local model identifiers. Model download occurs during setup; inference must continue to work without internet access.

| Task | Model behavior | Independent check |
|---|---|---|
| CV extraction | Suggest structured facts and source locations | Schema, exact dates/numbers, source text, user confirmation |
| Job extraction | Separate mandatory, preferred and unspecified requirements | Source snippets and missing-value handling |
| Company analysis | Extract business facts and propose a possible fit | Each factual statement needs a source; hypotheses are labeled |
| Matching | Suggest evidence-to-requirement mappings | Deterministic score calculation and hard filters |
| CV/email writing | Select approved material or propose a new formulation | Claim references, document checks and review where required |
| Reply classification | Suggest reply type and extract relevant dates | Rules immediately stop sends on replies; uncertain classifications are reviewed |

JSON validity is not factual validity. A second LLM pass can detect inconsistencies but cannot certify truth. After two unsuccessful schema repairs, move the item to a visible exception queue. On memory failure, retry with a shorter bundle and the 4B fallback; if quality is inadequate, keep the draft pending.

No vector database is required for one candidate profile and a modest company list. PostgreSQL text search and structured retrieval are sufficient initially. If a large personal knowledge base later warrants semantic retrieval, add pgvector and a small local embedding model after measuring the need.

## 7. Candidate facts and CV integrity

### 7.1 Import and approval

1. Upload the supplied PDF through Appsmith. Preserve the original bytes, filename, SHA-256 hash, import date and page count.
2. Extract text locally with page references. Use OCR only when extraction is missing or unusable.
3. Normalize employment, education, skills, languages, projects, publications and accomplishments into a proposed profile.
4. Display the proposal next to its source passages. Separate a skill merely listed in the CV from an achievement supported by an experience bullet.
5. Review uncertain details once: exact role titles, part-time status, dates, publication status, metric meaning, permission to disclose employer work, and still-current activities.
6. Approve a profile version and an associated bank of reusable statements. Preserve later corrections as new versions.

Each fact contains a stable ID, category, original wording, normalized value, source document/page, verification status, disclosure permission and approval timestamp. Facts copied from the uploaded CV begin as `imported`, not automatically `approved`.

For example, the reported 75% improvement belongs to manual ERP reporting cycles. It must not become a claim of 75% lower company costs. The reported approximately 330 FPS belongs to the research evaluation context; it must not become an LLM throughput claim or a claim about this machine without evidence.

### 7.2 What tailoring may change

Tailoring can select and reorder relevant bullets, choose a role-specific summary, shorten less relevant content, group skills, adjust terminology without changing meaning, and emphasize the projects most relevant to the employer.

Protected facts include employer names, historical job titles, employment type, dates, degree, language proficiency, publication status, numerical achievements and actual skills. The system must not add a technology simply because an advertisement asks for it.

Use two generation lanes:

- **Approved-content lane:** The system selects from previously approved summaries and bullet variants. It can run automatically because substantive wording comes from a controlled content bank.
- **New-wording lane:** The model proposes a paraphrase, translation or new company-specific claim. It receives fact/source checks and remains in review until accepted. Accepted wording can enter the reusable bank.

This allows automatic per-opportunity CV customization without asking you to review every repeated sentence. Arbitrary model-generated prose does not become trusted simply because it includes valid fact IDs.

### 7.3 Per-opportunity document package

Store a canonical JSON content specification, DOCX, PDF, extracted final PDF text, validation report, source profile version, target opportunity, template version, prompt/model versions, file hashes and generation time.

Use a simple single-column layout, recognizable headings, selectable text, embedded or available fonts and standard bullets. Do not add invisible keywords, charts, decorative skill meters, or text placed only in images. Keep contact details in the main reading order. Aim for one or two pages according to selected content; the existing CV is two pages, so do not force a one-page version by making it unreadably dense.

Generate DOCX once and derive PDF from it with Gotenberg's `POST /forms/libreoffice/convert`. Install the chosen fonts in the conversion image. Check page count, missing text, placeholder remnants, extraction order, unsupported claims, empty sections, dates, links, file size and attachment hash. Visually inspect representative versions of every template and unusual overflow cases.

A document passing these checks is designed for reliable text extraction; the product must not claim a universal ATS score or guaranteed ATS acceptance. Prefer PDF unless the employer asks for DOCX. Keep both available for manual portal uploads.

Use a filename such as `Yigit_Ersoy_AI_Engineer_Company_2026-11-16_v01.pdf`. Keep internal identifiers and approval metadata in the database, not in the visible CV.

## 8. Discovery and opportunity matching

### 8.1 Input sources

The system accepts a company name/domain, a job URL, pasted job text, a CSV of companies, a permitted RSS feed, or a scheduled discovery query. A browser bookmark plus a paste form is sufficient initially; a custom extension is unnecessary.

Research order:

1. User-supplied company and job URLs.
2. Official company careers, team, product and contact pages.
3. Public endpoints of an identified employer job board, initially Greenhouse and Ashby.
4. Allowed feeds, public directories and relevant sponsor-register evidence.
5. Optional SearXNG queries to discover additional sources.

Greenhouse public GET endpoints provide job information; its application submission endpoint requires employer-side authentication. Ashby's public posting endpoint provides listed job information. Neither gives a job seeker universal authorization to auto-submit applications. Discover the correct board identifier from the actual company careers page. Respect `isListed` and provider restrictions. [Sources 12–13]

LinkedIn, job boards with sign-in barriers, and CAPTCHA-protected sites are optional manual discovery sources, not infrastructure dependencies. Import a permitted link or description rather than assuming automated access will work. Search failures must never trigger a paid enrichment subscription or proxy service.

### 8.2 A bounded research job

For a candidate/company pair, collect the official identity, domain, country, product/service description, relevant business unit, careers URL, current public vacancies, relevant professional contacts and dated source evidence.

Start with at most three search queries and approximately five relevant company pages per company, then expand only if a useful item is missing. Fetch sequentially per domain with a small delay, reuse cached pages, honor applicable site restrictions, and stop on blocks. Configure JSON output on your own SearXNG instance; public instances may disable it. [Source 10]

Useful query templates include:

- `"{role title}" "{country or city}" (junior OR graduate OR associate)`
- `site:{company-domain} (careers OR jobs OR team OR contact)`
- `"{company}" ("Head of AI" OR "Talent Acquisition" OR "Engineering Manager")`
- `"{company}" ("Copilot Studio" OR "document intelligence" OR "on-premise AI")`

Only business terms and public company names belong in external search queries. Do not send your private CV text, phone number or unpublished work details to search engines.

When discovery fails, store `research_incomplete` with a reason and a manual URL-entry task. Do not interpret an unavailable careers page as proof that no vacancy exists.

### 8.3 Vacancy and speculative branches

For a vacancy, store its exact source, external ID, publication/closing dates when available, current status and requirements. Refresh the source before submitting if its cached version is older than 72 hours or close to its deadline. The 72-hour interval is an initial operational choice.

For speculative outreach, create an opportunity with `type=speculative`, no fabricated vacancy ID, a selected role family, supporting company facts, and a clearly labeled hypothesis about where your experience may help. No published opening is required.

Example hypothesis: an industrial company discussing internal data access may be relevant to your ERP reporting experience. The introduction can express interest in contributing to internal AI workflows; it cannot assert that the company has a reporting problem unless a reliable source establishes it.

### 8.4 Ranking

Apply hard constraints first: excluded employer, duplicate application, explicit seniority mismatch, essential language mismatch, known work-rights incompatibility, expired vacancy or a request not to contact. Unknown eligibility is visible and cannot count as a pass for a required application answer.

Then calculate an explainable internal priority score:

| Component | Weight |
|---|---:|
| Match between required work and approved candidate evidence | 35 |
| Role responsibilities and project relevance | 25 |
| Seniority fit | 15 |
| Language fit | 10 |
| Location/work-arrangement preference | 10 |
| Demonstrated company interest or relevant domain experience | 5 |

Treat these as configurable ranking weights, not hiring probabilities. Track contact quality, evidence confidence and eligibility separately rather than hiding them in one score. Suggested routing is 75+ for preparation, 60–74 for manual inspection, and below 60 for archive or later review. Mandatory criteria can block a high-scoring item.

For speculative opportunities, use company/domain evidence and a role profile instead of invented requirements. The interface must distinguish these scores from vacancy-based matches.

## 9. Finding and selecting HR and management contacts

### 9.1 Contact sources and evidence levels

Use published professional addresses on company pages, recruiting pages, official documents, relevant public professional profiles where access permits it, or contacts you provide. Store the exact source URL, relevant source passage, date checked, company association and role evidence.

Distinguish:

- `published_named`: a named professional and address are explicitly associated with the company.
- `published_functional`: an official recruitment/team mailbox suitable for the purpose.
- `user_confirmed`: supplied or confirmed by you, with its source context recorded.
- `inferred_or_unconfirmed`: a possible address or weak association; ineligible for automatic sending.
- `invalid`, `stale`, and `suppressed`: blocked pending the appropriate resolution.

Validate syntax, internationalized domain handling, domain identity and mail-routing DNS, including explicit null-MX records. DNS can establish domain mail routing, not whether a specific person's mailbox exists. A domain-wide catch-all also proves nothing about that person.

Do not guess `firstname.lastname@company` and treat it as verified. Do not brute-force mailboxes or send test messages to employees to validate addresses. There is no guaranteed, free source for every executive's current work email.

If no appropriate address is available, create a task with the official contact form, careers portal, or named person's public profile. The company remains in the pipeline, with the reason clearly shown.

### 9.2 Routing policy

1. Use the recruiting contact named in the vacancy or official careers page when available.
2. Otherwise select an appropriate recruiter or HR/talent contact for the country or technical group.
3. For a highly relevant technical introduction, use a publicly identified hiring manager, Head of AI, Head of Data, Head of Automation or similar functional leader.
4. For a small company, a founder or CTO may be the appropriate initial contact when the fit is specific and their business address is published.
5. Use a generic careers mailbox if it is the only appropriate published route.

This supports HR and management outreach while avoiding the same introduction to multiple executives at once. Default to one active contact sequence per company. A different stakeholder requires a relevant reason and a company-level cooldown or an explicit referral. HR and executives are not automatically copied together.

Refresh contact-role evidence older than 30 days before a new sequence, and handle a source that disappears as uncertainty. A named professional can have moved companies even if the old email address still routes somewhere.

Respect an employer's explicit instructions to use its application portal or not accept unsolicited CVs. Public availability of a work address does not establish unrestricted permission to contact it. The country/campaign policy must account for applicable outreach and personal-data rules; uncertain cases can use the official application channel.

## 10. Email content and decision to send

### 10.1 Message construction

Each first message contains a factual subject line, appropriate greeting, a specific reason for contacting that company, two or three relevant proof points from your approved facts, a concise request for a conversation or appropriate referral, and your real signature.

Target approximately 100–160 words initially, shorter when that reads better. HR messages emphasize role fit, experience and availability. Technical leaders receive relevant engineering/project details. Founders receive a short explanation of the useful work you can contribute, grounded in their actual company context.

For a speculative introduction, use language such as interest in future or unadvertised opportunities. Never refer to an open position that was not found, invent a referral, fabricate company news, or disguise the message as an existing conversation with `Re:`.

The prepared package includes recipient, company, role, country, subject, plain-text body, optional minimal HTML alternative, attachment, source references, and explanations of the chosen proof points. Use standard MIME encoding and correct Unicode handling for your name. Reject CR/LF injection in mail headers.

Default to one compact PDF attachment, preferably under 1 MB and with a 2 MB application-level cap unless a case explicitly needs more. Provide approved GitHub/LinkedIn/portfolio links selectively. Do not use tracking pixels, link shorteners, or fabricated urgency. Reply-based opt-out is sufficient for the proposed small personal workflow where appropriate; a clear request to stop always suppresses further contact.

Use the authenticated Gmail sender identity and an accurate Reply-To. Google manages the sending infrastructure and domain authentication for an `@gmail.com` address; no separate domain, DNS purchase or self-hosted SMTP server is required. Inbox placement is still not guaranteed. Do not introduce automated warm-up exchanges or additional accounts as a workaround.

### 10.2 Three operating modes

| Mode | Behavior |
|---|---|
| `draft_only` | Research and prepare packages; no external send operation. |
| `review_each` | You review the exact recipient, email and CV package, then approve it for scheduled sending. |
| `policy_auto` | Automatically send packages that meet the enabled campaign's scope, approved-content rules, evidence requirements and limits. Exceptions return to review. |

Begin in draft-only mode, validate a pilot, then enable a bounded campaign. Automatic mode is a real operating capability; it does not require approval for every qualifying message. Changes outside the authorized campaign scope require a new policy decision.

In automatic mode, per-application CVs come from the approved-content lane. New substantive paraphrases, uncertain contacts, unsupported claims, contradictory requirements, sensitive questionnaire answers and ambiguous send results are exceptions.

### 10.3 Send gate

Immediately before sending, enforce all of these conditions in a single controlled transition:

- Sending is enabled globally and for this campaign; the item is due.
- The recipient and company are allowed, current enough and not suppressed.
- The candidate profile and required eligibility answers are current.
- The job remains usable, or the opportunity is explicitly speculative.
- Content and documents passed validation; the selected facts are approved.
- A valid exact-package approval or applicable campaign policy exists.
- Recipient, subject, body and attachment hashes match what was approved.
- No reply, rejection, bounce, manual response or conflicting company sequence has intervened.
- The daily limit, company cooldown and recipient-local send window permit sending.
- Inbox synchronization is healthy and recent.
- No existing outbox entry or send attempt already owns this logical message.

Any edit to an approved recipient, body or attachment invalidates that approval. Directly editing a Gmail draft must be detected before sending; the safer default is to build and send the frozen local message rather than let Gmail drafts become the authoritative copy.

## 11. Gmail integration and reliable delivery records

### 11.1 Account setup to perform during implementation

1. Use your chosen personal Gmail account and confirm the sender identity. Enable suitable account protection and recovery.
2. Create a personal Google Cloud project and enable only the Gmail API needed here; this is an API configuration step, not paid cloud hosting.
3. Configure OAuth for the personal account. A regular personal Gmail account uses an External audience; the Workspace Internal option is not assumed.
4. Create the appropriate OAuth client, enter n8n's exact local callback URL, and store the client credentials in n8n. Localhost callbacks avoid needing a domain or public tunnel.
5. Inspect requested scopes. A send-and-read design can use `gmail.send` plus `gmail.readonly`; use `gmail.modify` only if Gmail labeling or equivalent modifications are actually required. Built-in node scopes may be broader, in which case use an appropriate generic OAuth/HTTP configuration or explicitly document the broader access.
6. Request offline access, obtain a refresh token and test refresh after the initial access token expires.
7. Address the seven-day authorization expiry associated with an External app in Testing. For a qualifying personal-use app, use the appropriate production publishing state and personal-use verification exception; this is not verification of a public SaaS. Reauthorize where required and test the actual outcome. If account policy prevents this, show reauthorization tasks or use another supported personal-account route rather than promising unattended operation.
8. Keep the n8n encryption key stable and backed up, with OAuth secrets excluded from workflow exports and logs.

Google documents the testing expiry and a personal-use verification exception. The exception does not remove Gmail policies or make refresh tokens irrevocable. Account changes and revocation can still require reconnection. [Sources 7–8]

Optional SMTP/IMAP is a fallback only if the account supports the necessary authentication. App passwords may be unavailable under some account settings, and basic account-password login is not an architecture dependency.

### 11.2 Sending limits

Proposed initial pilot: up to three new contacts per active day; after a successful pilot, up to five new contacts and a maximum of ten total outreach messages per day including follow-ups. Use one recipient per message, no bulk CC/BCC, and at least 15 minutes between outreach sends. These are configurable operating choices, not statements that a given volume is safe or provider-approved.

Schedule Tuesday–Thursday, 09:30–16:30 in the recipient's local timezone initially. Use IANA timezone identifiers and daylight-saving-aware conversion; show your dashboard in `Europe/Istanbul`. A company-country estimate can be wrong for a remote recruiter, so retain timezone confidence.

Do not automatically escalate volume when no one replies. Provider warnings pause sending regardless of volume. Do not rotate accounts or domains to get around limits. Personal Gmail's published maximums are ceilings, not recommended outreach targets. [Source 9]

### 11.3 Transactional outbox and uncertain sends

The database is the source of pending work. A dispatcher claims a due message with a transaction and a lease. The logical message has a stable key incorporating sender, candidate, company, opportunity/role, recipient and sequence step. Unique constraints and company-level locks prevent concurrent duplicate preparation and sending.

Before calling Gmail, persist the exact package hash, attempt ID, timestamp and a stable RFC Message-ID. Construct a standards-compliant raw MIME message where needed so that custom Message-ID and reply headers are under control. Save Gmail's message ID and thread ID after a successful response.

Database commits and Gmail sends cannot form one atomic transaction. If Gmail accepts the message but the response is lost, exactly-once delivery cannot be guaranteed by a local retry flag. Mark the attempt `send_unknown`, search/reconcile Sent mail using the RFC Message-ID plus recipient/time evidence, and adopt the provider message if found. If the result remains ambiguous, hold it for review. Never blindly retry an uncertain send.

Do not rely on Gmail itself deduplicating a repeated Message-ID. A uniqueness key prevents duplicate workflow work; it is not a promise that an external provider will reject a repeated message.

Use generic retry/backoff for safe reads and clearly unsubmitted work. Treat ambiguous write failures separately. Persist leases and attempt state before the network call, and reconcile expired send leases after restarts rather than simply returning them to the queue.

Provider acceptance means `sent`, not confirmed inbox delivery or readership. Hard bounces can arrive later. A Gmail message ID is evidence of provider acceptance; it is not a delivery receipt.

## 12. Replies, follow-ups and formal applications

### 12.1 Inbox synchronization

Poll Gmail approximately every five minutes while the system is active. Use an initial bounded synchronization, then a durable `historyId` checkpoint or equivalent incremental mechanism. Persist processed Gmail message IDs with a unique constraint so overlapping polls are harmless.

Advance a checkpoint only after the corresponding events are saved successfully. If the history cursor expires, perform a bounded resynchronization with overlap and refresh all still-active tracked threads. Do not assume unread messages are the only new business events.

Fetch bodies only for relevant tracked threads or credible new messages associated with current contacts. Do not copy your entire private mailbox into the application. Preserve Message-ID, In-Reply-To, References, Gmail message/thread IDs, sender, timestamps, labels and a minimized body excerpt where needed.

Synchronize incoming messages, bounces and your manual outgoing replies. If you answer a recruiter directly in Gmail, the application must see that activity and stop its previous follow-up schedule. A new subject, alias or forwarded message may not match a thread cleanly; uncertain matching creates a review task and pauses the affected company sequence.

Before each outbound attempt, check relevant thread state again. If the last successful inbox synchronization is more than ten minutes old, pause sending. A reply can still arrive during the brief interval between the last read and external send; the product should minimize and explain this residual race rather than claim it is impossible.

### 12.2 Response handling

| Detected event | Action |
|---|---|
| Any human reply | Immediately cancel pending automatic follow-ups for that sequence; classify after stopping. |
| Interest, interview or document request | Create a visible response task and draft a grounded reply. You control scheduling, salary, commitments and documents sent next. |
| Referral to another person | Store the referral as evidence; validate the new association and build a separate reviewed introduction. |
| Rejection | Close the opportunity and stop its sequence; apply configured company cooldown. |
| Request to stop | Add durable suppression at the requested scope and cancel all affected queued messages. |
| Out-of-office response | Pause until the stated return date plus a small buffer; ambiguous dates go to review. |
| Hard bounce | Suppress that address and stop its sequence. Investigate the source before any alternative contact. |
| Temporary delivery failure | Pause and inspect provider evidence; do not create an additional new message blindly. |
| Unclear, multilingual or low-confidence message | Hold automatic action and create a review task. |

Incoming mail is untrusted text. A recruiter reply cannot instruct the automation to reveal credentials, change its policies, open arbitrary files or send the whole database. Strip quoted history for classification where possible, while keeping the original provider message available for review.

### 12.3 Follow-up policy

Default to one follow-up after seven business days, counted from the last relevant message, using the contact timezone and a maintained country holiday calendar when available. If a holiday calendar is unavailable, label the schedule as weekday-based and prefer a conservative delay.

A follow-up uses the same thread, appropriate References/In-Reply-To headers and a short approved template. Send only if the initial message is confirmed sent, there is no reply/bounce/opt-out, no newer manual activity, and all gates still pass. Do not automatically reattach the CV unless useful or requested.

After one unanswered follow-up, close the sequence as `no_response`. Default company cooldown is 60 days. A new relevant vacancy, a direct referral or an explicit user decision can justify reconsideration; silence alone does not trigger escalation through the management hierarchy.

### 12.4 Employer portals

When the employer requires its own application form, generate a handoff package: matched CV PDF/DOCX, optional cover letter, a factual answers sheet, job URL, missing-answer checklist and source evidence.

You complete or supervise the portal submission. Store the confirmation/reference number or a user-recorded submission event afterward. Unsupported portals, CAPTCHA and mandatory legal attestations do not become hidden automation failures. A generic browser agent is not a required part of this free architecture.

Future adapters can prefill an explicitly supported portal, but submission logic must be built and tested per portal. Employer-side ATS credentials are not available to a candidate merely because a public job-reading API exists.

## 13. Concrete n8n workflow inventory

Use small workflows with explicit inputs and outputs. Standard building blocks include Schedule Trigger, Webhook/Form Trigger, HTTP Request, Postgres, IF/Switch, Execute Sub-workflow, Gmail or authenticated HTTP, and Error Trigger. Keep business state in PostgreSQL rather than relying on long-lived Wait executions.

| ID | Workflow | Trigger and durable result |
|---|---|---|
| WF-00 | Startup and health | Startup/periodic check; verify dependencies, restore inbox state and leave sending paused until healthy. |
| WF-01 | Candidate import | Upload; create immutable source document and proposed facts. |
| WF-02 | Profile/content approval | Authenticated action; publish an approved profile/content version and invalidate affected pending packages. |
| WF-03 | Discovery | Daily bounded schedule or manual URL/CSV; upsert companies, sources and job records. |
| WF-04 | Company research | Queued company; create sourced company brief and speculative opportunities where justified. |
| WF-05 | Requirements and matching | New/changed opportunity; store eligibility checks, evidence mapping and explained score. |
| WF-06 | Contact discovery | Eligible opportunity; store professional contacts and select a permitted route. |
| WF-07 | Package generation | Qualified target; select approved content or draft new wording, render CV and prepare email. |
| WF-08 | Validation and decision | Generated package; validate facts/files and route to review or an enabled automatic policy. |
| WF-09 | Outbox dispatcher | Every minute while active; atomically claim due work, recheck gates and make at most one controlled send attempt. |
| WF-10 | Gmail synchronization | Every five minutes and before sending; persist replies, bounces, manual sends and checkpoints. |
| WF-11 | Follow-up planner | Daily and after inbox events; enqueue, pause or cancel the one permitted follow-up. |
| WF-12 | Application/response tasks | User action or recruiter response; track portal submissions, interviews, requested documents and outcomes. |
| WF-13 | Recovery and errors | Error Trigger/expired lease scan; classify safe retry, unresolved send, auth issue or manual exception. |
| WF-14 | Maintenance and reporting | Daily/weekly; prune permitted data, verify backups, report outcomes and source health. |

Every workflow receives a correlation ID and relevant record IDs. Record attempt count, deadline, last error and next retry time. Honor Retry-After for upstream rate limits; use capped backoff for idempotent work and stop after three ordinary transient retries. Document-generation and model validation can use their own smaller repair limits.

An API timeout, invalid schema, blocked page, dead source, unavailable model, OAuth problem, missing PDF, disk-space problem or unresolved send becomes a named status visible in the interface. There is no silent default-to-send branch.

Use one n8n main instance with bounded concurrency. Redis-backed n8n queue mode, Kubernetes and multiple workers are unnecessary for this single-user workload. Appsmith's own bundled cache is an independent implementation detail.

## 14. Data model and state transitions

### 14.1 Main records

| Record group | Essential fields |
|---|---|
| `candidate_profiles`, `candidate_versions` | Identity, language and work preferences, approved version/hash, status |
| `candidate_facts`, `approved_content` | Fact ID, source/page, normalized value, disclosure rule, approved phrases, version |
| `role_profiles` | Role family, title aliases, required/preferred skill mappings, summary variants, score weights |
| `companies` | Canonical name, domain, country, legal/brand aliases, group ID, careers URL, exclusion state |
| `sources`, `source_snapshots` | URL, retrieval time, source type, relevant passage, content hash, expiry, trust and access status |
| `contacts` | Name/title, employer, normalized address, evidence, evidence status, last verified, timezone |
| `opportunities` | Company, role family, vacancy/speculative type, source IDs, external job ID, requirements and current status |
| `eligibility_checks`, `fit_assessments` | Individual criteria, known/unknown values, weighted components, source/fact references, blockers |
| `document_versions`, `artifacts` | Opportunity, profile/template/model versions, JSON specification, file ID, MIME type, size, SHA-256 |
| `campaigns`, `campaign_policies` | Allowed countries/roles/contacts, mode, limits, stop rules, approval/version |
| `message_packages`, `approvals` | Frozen recipient/body/attachment hash, approved content references, approval actor/time/policy |
| `outbox`, `send_attempts` | Logical key, sequence step, due time, lease, attempt ID, Message-ID, provider result, uncertainty |
| `mail_threads`, `mail_events`, `mail_sync_state` | Provider IDs, parent references, type, time, classified result, checkpoints |
| `applications`, `tasks` | Portal/email channel, submission evidence, next action, due date, interview/outcome state |
| `suppressions` | Contact/company/domain scope, reason, source event, created time, removal authority |
| `job_runs`, `audit_events`, `model_runs` | Workflow state, retries, causal actor, model/prompt version, duration, errors and decisions |

Separate profile content from document versions, and applications from email messages. A company can have several opportunities, but the company-level contact policy still prevents conflicting simultaneous outreach.

Use UUIDs, foreign keys, UTC timestamps in storage, indexed due/status fields and schema migrations. Keep display timezones explicitly. Normalize domains without assuming all companies sharing a parent domain are the same legal entity. Preserve mailbox spelling while applying a documented deduplication policy; do not blindly strip dots or plus suffixes from arbitrary corporate addresses.

### 14.2 State machines

```text
Opportunity:
discovered -> researched -> assessed -> ready_for_package
             |              |              |
             v              v              v
       research_incomplete  ineligible     needs_information

Package:
draft -> validated -> needs_review -> approved -> queued
                    \-> policy_eligible --------> queued
Any relevant change -> approval_invalidated -> regenerate/review

Outbox:
queued -> sending -> sent
                    -> definitely_failed -> bounded retry or hold
                    -> send_unknown -> reconcile -> sent or needs_review

Conversation:
sent -> awaiting_reply -> replied / rejected / bounced / opted_out
                      -> followup_due -> followup_sent -> no_response

Application:
prepared -> awaiting_portal_submission -> submitted -> interview
                                                  -> rejected / withdrawn / offer
```

Only whitelisted transitions are permitted. A failed document render cannot advance to approved. An unresolved send cannot create a follow-up. A reply or suppression cancels relevant queued work transactionally.

### 14.3 Important database guarantees

- Unique company/source/job keys prevent rediscovery from creating duplicate opportunities.
- Unique Gmail message IDs make repeated synchronization safe.
- Unique logical outbox keys and locking prevent simultaneous dispatch of the same message.
- A company/candidate sequence lock implements one active sequence per company.
- An approval binds an immutable package hash and policy/profile versions.
- Audit events are append-only to normal application roles.
- No direct UI update can turn a failed or unapproved package into a sendable one.

These are PostgreSQL constraints and transaction rules, not instructions that the LLM is merely asked to follow.

## 15. Appsmith application screens

| Screen | User-facing content and actions |
|---|---|
| Overview | Pipeline counts, next tasks, queued sends, latest replies, system state, global pause/resume |
| My profile | Source CV, extracted facts, evidence snippets, correction/approval, work preferences |
| Target strategy | Selected role families, country list, exclusions, language and work-rights settings |
| Company research | Company facts with source links, relevant roles, contact candidates, missing information |
| Opportunities | Vacancy and speculative cards, explained match, eligibility gaps, deadlines, prepare/archive |
| Review | Source versus tailored CV, PDF preview/download, exact email/recipient, changes and validation issues |
| Outbox | Due times in local and recipient time, status, pause/cancel, approved package version |
| Conversations | Thread activity, classifications, reply drafts, opt-out and follow-up status |
| Applications | Portal handoff files, submission confirmation, interview tasks, offers/rejections |
| Operations | Dependency health, auth status, backup age, research failures, uncertain sends and audit history |

Use existing table, form, text, file-upload and document-preview widgets. Differences can be shown side by side without building a bespoke editor. Fetch sensitive artifacts through authenticated server-side requests and deliver the preview/download to the logged-in user; do not create public CV links to make preview easier.

Store server credentials in Appsmith datasources, not browser JavaScript. Parameterize database queries. Webhook actions authenticate, validate their payload, enforce allowed transitions and use a one-time action ID to prevent accidental double-click duplication.

Do not depend on paid SSO, enterprise role controls or premium audit features for this single-user deployment. Native account access plus private network boundaries are sufficient for the initial scope; business audit records belong to the application database.

## 16. Operations, privacy and recovery

### 16.1 Configuration and access

Pin container versions and model digests after compatibility testing; do not schedule automatic upgrades of a working outreach system. Record software/model licenses and the release date used. Recheck the free-edition feature set before each significant upgrade.

Keep secrets in protected local configuration and application credential stores. Use a generated stable n8n encryption key. Avoid placing CVs, OAuth secrets, password files or source snapshots in Git. Git contains sanitized workflow JSON exports, templates, schema migrations and configuration examples only.

n8n CE lacks features such as native Git version control, external secrets and external binary storage. Use ordinary file-based exports, protected local secrets, PostgreSQL policy configuration and the utility service's artifact directory instead. Environment variables used to configure a container are distinct from n8n's paid custom-variables feature. [Source 2]

Use least-privilege database roles and allowlisted operations. Protect state-changing endpoints with authenticated requests; review actions must not be executable by opening an unauthenticated GET link. Browser-visible text is escaped. Restrict artifact downloads to the logged-in local application and known object IDs.

Block public-fetch requests to loopback, private networks, link-local addresses, cloud metadata endpoints and non-HTTP(S) schemes; validate redirects and DNS resolutions too. Enforce request timeouts, response-size limits and content-type checks. Browser rendering uses a restricted process/container without private data mounts. Keep its network permissions separate from the document converter.

### 16.2 Data minimization and retention

Avoid extracting home address, birth date, national identifiers, marital status or other unnecessary details into outreach. Keep contact data limited to relevant professional contact information and evidence. The supplied CV is processed locally; only the selected final document is attached when sending.

Initial retention policy, configurable by you:

- Keep original CVs and approved candidate facts until you replace/delete them.
- Keep pending and sent application packages for the active job search plus 12 months, unless you choose otherwise.
- Keep raw research snapshots for 90 days where useful and permitted; retain minimal citations and hashes as needed afterward.
- Keep ordinary execution logs for 14 days; use short metadata-only records for successful runs and redact sensitive error details.
- Keep relevant mail excerpts for active conversations plus 90 days after closure; Gmail remains the underlying mailbox.
- Keep the minimum suppression record needed to avoid contacting someone again, even when other contact details are deleted.

Deletion is a workflow: cancel outstanding work, remove relevant files and records, expire cached derivatives, and account for copies in backups until backup retention expires. Deleting a local package cannot recall a delivered email or force a recipient to delete it. Do not describe local retention settings as accomplishing either.

### 16.3 Backup and restore

Perform an encrypted daily backup of the business database, n8n database/configuration, document artifacts and templates, Appsmith's documented persistent state, and the settings required to restore the installation. Coordinate database dumps and file snapshots so manifest hashes and referenced files agree. Do not assume copying a running database volume is a valid database backup.

Use Appsmith's supported backup/export method for its pinned version. Preserve the keys needed to decrypt application credentials in a separately protected recovery location. An encrypted backup without its recovery key is not a restorable system.

Store backups on an existing independent drive or another explicitly selected storage location. Start with seven daily, four weekly and three monthly recovery points, adjusted to available space. The initial target is at most 24 hours of local data loss and restoration within half a day; verify those targets rather than advertise them as guarantees.

Test restore before live outreach and monthly afterward. Restore first into draft-only mode. Then synchronize Gmail and reconcile outbox attempts against provider records before any send resumes. This prevents an older backup from resending messages already delivered after that backup was taken.

### 16.4 Monitoring and shutdown rules

Track last successful inbox sync, OAuth health, pending/unknown sends, queue age, model failures, GPU/RAM usage, disk free space, backup age, stale contacts, search-source failures and document validation failures.

Use an external-to-n8n local check, such as a Windows scheduled health check, so a failed n8n process does not have to report its own outage. Show alerts in the local interface/desktop; notification services are optional. If Gmail authentication fails, a Gmail-based alert is not a reliable fallback.

Stop new sending on a global pause, stale inbox synchronization, auth failure, provider restriction, critical disk exhaustion, missing artifacts, unresolved send ambiguity for the relevant sequence, or evidence that a package no longer matches approval. One hard bounce stops its recipient immediately; a second hard bounce within the last 20 outreach attempts pauses the campaign for source review. During the initial pilot, inspect any hard bounce before continuing.

A pause cancels or defers unsent messages; it cannot recall a Gmail request already accepted. The interface must show that distinction.

## 17. Failure cases and explicit fallback paths

| Failure or limitation | Expected behavior |
|---|---|
| No vacancy exists | Use the speculative opportunity path with an honest introduction. |
| No suitable email is publicly available | Keep the company and create an official-channel/manual-contact task. |
| Search engine blocks SearXNG | Back off; continue direct known-source research or request a pasted URL. |
| Company source is stale or contradictory | Re-fetch and mark unresolved facts; do not personalize using the disputed claim. |
| Website needs JavaScript | Use a restricted browser adapter only if access is allowed; otherwise record a manual task. |
| CV extraction fails | Run local OCR or request a corrected source through the profile UI. |
| Local model hallucinates or fails schema validation | Reject the output, bounded repair, then review; never accept malformed text silently. |
| RTX 4060 runs out of VRAM | Shorter context, one job at a time, 4B model or CPU fallback; no paid-cloud switch. |
| Appsmith exhausts memory | Lower concurrency; use n8n forms and a simpler temporary review interface while retaining all send gates. |
| PDF contains missing text or overflows | Fix template/content and regenerate; package remains unsendable. |
| OAuth token is revoked/expired | Pause outbound work, show reconnection task, then synchronize and reconcile before resuming. |
| Send request times out after possible acceptance | `send_unknown`; reconcile against Sent mail; do not blindly retry. |
| A reply arrives after approval | Cancel queued follow-up; require a new response decision. |
| You edit a document after approval | Hash mismatch invalidates approval. |
| Machine sleeps or loses internet | Durable state persists; inbox catches up first and send slots are recalculated. |
| Employer requires portal submission | Provide application package and capture a real submission confirmation afterward. |
| Work-rights or language answer is missing | Hold applications that require it; show a specific information task. |
| Free service changes pricing or terms | Disable the affected connector and select a free supported fallback or manual route. |
| No independent backup storage exists | Clearly report reduced recovery protection; require a storage choice for the full restore target. |

These fallbacks are part of the product. A system with free discovery and a personal mailbox cannot guarantee that every company is contactable or every application is fully automatic.

## 18. Implementation sequence and deliverables

The estimates below assume one implementer familiar with Docker and n8n, as your CV suggests you may be. Approximately 10–15 focused implementation days plus a controlled live pilot is a planning range. Hardware problems, OAuth restrictions and website differences can change it. Nothing in this schedule authorizes implementation before your next instruction.

| Phase | Work and deliverables | Exit condition |
|---|---|---|
| 0 — Confirm inputs | Confirm VRAM/free disk, sender account, work-rights matrix, relocation, availability, salary constraints, excluded employers, disclosure rules and backup location. Import and approve facts from the actual CV. | Unknowns are explicit; no invented eligibility or unsupported fact enters the approved profile. |
| 1 — Local foundation | Install/configure WSL 2, Docker, NVIDIA support; launch PostgreSQL, n8n, Appsmith, Ollama, utility service and Gotenberg; add persistence, credentials, private networking and health checks. | Restart retains state; local model works; only intended local services are exposed. |
| 2 — Profile and documents | Build fact schema, four role families, approved phrase bank, DOCX template, parser/render endpoints and document validation. | Produce a truthful sample for each role family, with readable DOCX/PDF and a complete fact map. |
| 3 — Discovery and scoring | Add URL/CSV input, company research, Greenhouse/Ashby readers, optional SearXNG, geographic filters, scoring and contact evidence. | Research a small sample across all target country groups; expose failures and eligibility unknowns accurately. |
| 4 — Review application | Configure Appsmith screens, safe actions, profile approvals, package review, company deduplication and campaign settings. | Review/edit invalidates hashes correctly; no UI shortcut bypasses the send gate. |
| 5 — Email and replies | Connect Gmail OAuth, implement outbox, MIME/threading, incremental sync, suppression, manual-send detection, one-follow-up rule and uncertain-send recovery. | Local Mailpit checks and tests to a user-controlled address pass; company outreach is still paused. |
| 6 — Recovery and acceptance | Add backups, restore procedure, restart recovery, prompt-input protections, quota handling and the acceptance tests below. | Restore works and the full end-to-end flow passes, including injected failures. |
| 7 — Controlled pilot | Enable a specific reviewed campaign of roughly 5–10 relevant companies, initially in review-each mode. Inspect all packages and outcomes. | No unsupported claims, duplicate sends or ignored replies; delivery/source quality is acceptable. |
| 8 — Bounded automatic operation | Enable policy-auto for approved role families, geography, content and published contact classes. Review exceptions and weekly results. | Normal qualifying packages run automatically; uncertain cases remain visible. |

Phases 0–6 can produce a complete local system without contacting companies. The pilot introduces real outreach only under the campaign you enable.

### 18.1 Concrete handover artifacts to produce during implementation

- Pinned Compose configuration, environment example and Windows start/stop/recovery instructions.
- PostgreSQL migrations, restricted roles, views, constraints and transition functions.
- Exported n8n workflows WF-00 through WF-14 with no embedded secrets.
- Appsmith application export and datasource setup instructions.
- Small document utility service and optional restricted research adapter.
- Candidate JSON schema, approved fact/content bank and role profiles.
- DOCX template, four sample tailored packages and validation reports.
- Prompt templates, JSON schemas, model digest and a small evaluation set.
- Gmail OAuth setup guide, outbox recovery procedure and thread-handling rules.
- Campaign configuration, suppression controls and pause/resume procedure.
- Backup/restore scripts and a recorded restore test.
- Acceptance results, dependency/license inventory, operations runbook and known limitations.

These are future implementation deliverables, not files that have been deployed by this planning task.

## 19. Acceptance tests and completion criteria

Use a test mailbox and synthetic companies/contacts for failure injection. Real contact addresses must not be used to test retries, bounces or formatting. Test the actual boundary behavior rather than merely asserting that workflow nodes exist.

| Test | Required outcome |
|---|---|
| Import the supplied CV | Preserve employer names, part-time labels, dates, research context, English C1 and source/page mappings. |
| Match four role families | Relevant evidence changes by role; historical facts remain identical. |
| Advert asks for an absent skill | Show a gap; the skill does not appear as candidate experience. |
| Job advert contains malicious instructions | Treat them as source text; no policy or tool permission changes. |
| Company has no vacancies | Produce a speculative package without inventing an opening. |
| Executive address is guessed | No automatic send; contact remains unconfirmed. |
| Mail domain resolves but person is unverified | Do not label the mailbox verified from DNS alone. |
| German is mandatory but candidate lists only Turkish/English | Hold or reject that opportunity; do not claim German proficiency. |
| Work authorization is unknown | Do not answer a mandatory eligibility question affirmatively. |
| Tailored PDF is generated | Text extraction succeeds; protected facts and approved wording match; layout is readable. |
| User edits an approved email or file | Approval becomes invalid and the queue is updated. |
| Same scheduler event runs twice | Only one logical outbox message exists. |
| Two dispatchers claim the same item | Only one obtains the send lease. |
| Gmail accepts but response is lost | Reconciliation finds the original or holds uncertainty; no blind duplicate. |
| Reply or opt-out arrives before a follow-up | Pending follow-up is canceled. |
| You reply directly in Gmail | System detects manual activity and does not send its obsolete follow-up. |
| Gmail history cursor expires | Controlled resync recovers relevant events without duplicate processing. |
| Computer restarts with due messages | Inbox sync and send reconciliation precede outbound work; no catch-up burst. |
| Restore an older backup | Already-sent messages are reconciled before sending can resume. |
| Recipient timezone changes for daylight saving | Sending remains within the intended local window. |
| OAuth fails, quota is exceeded or disk fills | Sending pauses with an actionable error; no data or queued state is silently lost. |
| Model cannot run or cloud access is unavailable | Drafts wait or use the approved local fallback; no paid API request occurs. |
| Formal employer portal is required | Status remains awaiting submission until actual confirmation is recorded. |
| Global pause is pressed | No new send attempt starts; any already in flight is clearly shown. |

The pilot can advance when no unsupported facts or duplicates are observed, each sent package is traceable to its approved inputs, replies/opt-outs stop follow-ups, restore and reconciliation work, and the full workflow stays within the chosen free services.

Before selecting the final model, evaluate around 12–20 representative cases across the role families, including a missing skill, vague job description, speculative introduction, unclear eligibility and multilingual company source. Assess factual fidelity, English quality, useful role relevance, schema success and measured latency. Do not select a larger model merely from parameter count.

## 20. Routine use and outcome measurement

The normal daily flow is: inspect new qualified companies, resolve missing information, review any new wording, check incoming replies, and let the approved campaign process eligible packages. Most repeated tailoring can become automatic once the content bank is mature.

Weekly, inspect role/country performance, source reliability, the proportion of companies with usable contacts, and the reasons packages need review. Update the approved profile only when you provide a correction or new evidence. A model-generated sentence does not become a new accomplishment through repetition.

Track these measures with explicit denominators:

- Qualified opportunities divided by researched opportunities.
- Usable professional contacts divided by researched companies.
- Packages needing revision divided by prepared packages.
- Human replies and positive replies divided by sent introductions after a defined response window.
- Interviews divided by submitted applications or sent introductions, reported separately by channel.
- Hard bounces divided by outreach attempts, alongside the raw counts.
- Time from target selection to a validated package.
- Failure counts, unknown-send counts, backup age and manual exception count.

Do not optimize for raw message count or email opens. Small samples can be misleading; avoid changing the whole strategy after a few unanswered messages. Review outcomes by role family and channel before making substantive changes.

## 21. Inputs still needed at implementation

The architecture and initial target roles are defined. The following are actual user-specific inputs that software cannot responsibly infer:

1. Citizenship and current work rights by target country; whether sponsorship is needed.
2. Relocation preferences, remote/hybrid/on-site preferences, earliest start date and notice period.
3. Compensation constraints, contract preferences and employers/sectors to exclude.
4. Confirmation of CV facts, measurement context, publication details and permission to disclose employer work.
5. Exact GPU VRAM, free SSD space, normal computer uptime and independent backup location.
6. Sender identity/signature and campaign settings to enable after the pilot.

These are onboarding fields with explicit pending states, not missing architecture. Public research can continue while many are unknown; final application answers and send eligibility depend on the relevant fields.

## 22. Official sources and verification notes

Architecture-sensitive documentation was checked on 16 November 2026. The source pages describe products and policies; resource budgets, ranking weights, outreach cadence, retention intervals and implementation estimates are design recommendations for this system.

1. [n8n Community License FAQ](https://docs.n8n.io/n8n-community-license/community-license/license-faq) — self-hosted personal use and licensing boundary.
2. [n8n edition comparison](https://docs.n8n.io/deploy/host-n8n/community-edition-features) — free Community Edition and excluded paid features.
3. [Appsmith official Docker installation source](https://github.com/appsmithorg/appsmith-docs/blob/main/website/docs/getting-started/setup/installation-guides/docker/README.mdx) — CE image, persistence and current all-in-one resource guidance.
4. [Ollama local FAQ](https://docs.ollama.com/faq) — local-only mode, memory/concurrency considerations and context configuration.
5. [Qwen3 8B on Ollama](https://ollama.com/library/qwen3:8b) — downloadable model, size, quantization and license.
6. [Gmail API usage limits and pricing](https://developers.google.com/workspace/gmail/api/reference/quota) — standard free use, quotas, billing threshold and overage notice.
7. [Google: when OAuth verification is not needed](https://support.google.com/cloud/answer/13464323?hl=en) — personal-use exception and continuing policy obligations.
8. [Google: manage app audience](https://support.google.com/cloud/answer/15549945?hl=en) — testing-mode authorization expiry and publishing state.
9. [Gmail sending and receiving limits](https://support.google.com/mail/answer/22839?hl=en) — mailbox limits, separate from API quotas.
10. [SearXNG search API](https://docs.searxng.org/dev/search_api.html) — JSON configuration and public-instance limitations.
11. [Gotenberg DOCX/office conversion](https://gotenberg.dev/docs/convert-with-libreoffice/convert-to-pdf) — local conversion endpoint, fonts and conversion behavior.
12. [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html) — public job reads and authenticated application submissions.
13. [Ashby public job posting API](https://developers.ashbyhq.com/docs/public-job-posting-api) — job-board lookup, listing visibility and field availability.
14. [Docker Desktop license](https://docs.docker.com/subscription-billing/desktop-license/) — personal-use eligibility.
15. [Docker Desktop GPU support on Windows](https://docs.docker.com/desktop/features/gpu/) — Windows/WSL 2 GPU execution path.
16. [n8n Google OAuth credential documentation](https://github.com/n8n-io/n8n-docs/blob/main/docs/integrations/builtin/credentials/google/oauth-generic.md) — custom credentials and localhost callback setup.
17. [Appsmith repository and license](https://github.com/appsmithorg/appsmith) — Community source and Apache 2.0 license.
18. [Ollama structured-output documentation](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx) — schema-constrained generation and client validation.
19. [UK licensed worker-sponsor register](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) — a free employer-research signal.
20. [Netherlands IND work-sponsor register](https://ind.nl/en/public-register-recognised-sponsors/public-register-work) — a free employer-research signal.

The uploaded `Yigit_Ersoy_CV_ENG.pdf`, pages 1–2, is the source for the personal positioning in this proposal. Its claims were read as candidate-supplied evidence, not independently certified employment or publication records. No candidate information was needed in the public documentation searches.

**Handoff status:** The plan is ready for review. Implementation remains paused until your next instruction.
