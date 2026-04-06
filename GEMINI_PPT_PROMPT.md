# Complete Prompt for Google AI — RxScope Client Presentation

Copy everything below this line and paste into Google Gemini / Google AI:

---

Create a professional 16-slide Google Slides presentation for "RxScope" — an AI-Based Medical Content Identification System. This is a client-facing technical proposal for a company called RxNetwork (USA-based).

## Design Requirements:
- WHITE background on all slides
- Clean, corporate, professional design
- Primary accent color: #2563EB (blue)
- Secondary colors: #059669 (green), #D97706 (amber), #7C3AED (purple)
- Font: Calibri or Inter
- Use colored card/box sections with light tinted backgrounds (e.g., light blue #DBEAFE, light green #D1FAE5, light amber #FEF3C7)
- Subtle borders on cards, no harsh shadows
- Page numbers on slides 2–16 (format: "2 / 16")
- Widescreen 16:9 format
- NO emojis — use colored accent cards and clean typography instead
- NO references to India, Mumbai, or any India-specific regions

---

## SLIDE 1: Title Slide

- Small blue accent bar at very top of slide
- Short blue horizontal line above the title
- Title: "RxScope" (large, 52pt, bold, dark text)
- Subtitle: "AI-Based Medical Content Identification System" (blue, 26pt)
- Below: "Technical Architecture & Proposal" (gray, 18pt)
- Thin divider line
- "Prepared for RxNetwork" (14pt)
- "April 2026 | Confidential" (12pt, muted gray)

---

## SLIDE 2: The Problem

Header: "The Problem"
Subheader: "What exists today falls short for HCP-targeted advertising"

Two cards side by side:

**Left card (light blue background, blue border): "Current Industry Gap"**
- Brand safety vendors (IAS, DoubleVerify) classify to avoid — not seek
- No solution targets HCP-oriented content specifically
- No medical entity resolution (NPI, UMLS, drugs)
- No HCP vs consumer content distinction

**Right card (light green background, green border): "What RxNetwork Needs"**
- AI-driven classification of medically relevant HCP content
- Coverage across Scribd, Slideshare & additional platforms
- Pharma ad-targeting whitelist in Excel format (CSV/XLSX)
- Verified entities: physicians, pharma, medical institutions

**Bottom card (gray background): "RxScope: The Solution"**
- Medical taxonomy grounding — MeSH, ICD-10, DSM-5, IAB 3.1 mapping for DSP compatibility
- NPI-verified physician identification via federal registry — not guesswork
- Document-level AI analysis with ensemble confidence scoring (0–1.0)
- Programmatic ad-tech output format — CSV/XLSX whitelist + REST API for real-time DSP integration

---

## SLIDE 3: How RxScope Works

Header: "How RxScope Works"
Subheader: "7-step AI pipeline from URL discovery to whitelist delivery"

Seven numbered cards in a horizontal row with arrows between them:

1. **Discover** (blue) — Crawl sitemaps & URL queues from target platforms
2. **Scrape** (blue) — Fetch content via headless browser, robots.txt compliant
3. **Extract** (blue) — Clean text, metadata, author info from HTML / PDF / PPT
4. **Classify** (green) — AI classification via Claude + scispaCy + MeSH / IAB mapping
5. **Verify** (green) — Entity resolution: NPI, RxNorm, FDA verification
6. **Score** (amber) — Ensemble confidence scoring + human review for edge cases
7. **Deliver** (amber) — CSV/XLSX whitelist + REST API + Admin Dashboard

Each step has a colored circle with the step number inside it.

**Bottom card: "Key Differentiator"**
- Multi-agent AI pipeline powered by LangGraph orchestrates specialized agents for each step.
- Claude Sonnet handles volume classification. Claude Opus handles edge cases (0.6–0.8 confidence). Human-in-the-loop ensures quality.

---

## SLIDE 4: Technology Stack

Header: "Technology Stack"
Subheader: "Production-grade, scalable, medical-domain optimized"

Four cards in a row:

**Card 1 — "AI & Classification" (blue):**
- Claude Sonnet 4 + Opus 4 (Anthropic)
- LangGraph — agent orchestration (MIT, $0)
- LangSmith — monitoring & observability
- scispaCy + MedSpaCy — medical NLP
- BiomedBERT — biomedical embeddings

**Card 2 — "Data & Storage" (green):**
- PostgreSQL 16 + pgvector
- Managed cloud database hosting
- Redis — caching & job queues
- Cloudflare R2 — object storage

**Card 3 — "Infrastructure" (amber):**
- Lightpanda — headless browser scraping
- Cloudflare Workers — edge API
- Cloudflare Pages — dashboard hosting
- Rotating residential proxies

**Card 4 — "Medical APIs (All Free)" (purple):**
- NPI Registry — physician verification
- RxNorm — drug name resolution
- FDA NDC — drug identification
- UMLS / MeSH — medical ontologies

**Bottom section with two columns:**
Left: "LangGraph = the ENGINE" — Open-source framework that builds the AI pipeline. Orchestrates agents: scrape → classify → score → store. Cost: $0 (MIT license)
Right: "LangSmith = the MONITOR" — SaaS platform that watches the pipeline in production. Traces every decision, measures cost & accuracy. Free tier available; scales with usage.

---

## SLIDE 5: Database Architecture

Header: "Database Architecture"
Subheader: "PostgreSQL + pgvector — unified relational + vector database"

Two cards side by side:

**Left card (light green, green border): "✓ PostgreSQL + pgvector (Selected)"**
- Native vector search — single DB for everything
- Full ACID compliance — guaranteed data consistency
- Foreign keys for medical entity relationships
- SQL → CSV/XLSX export (client requirement)
- LangGraph first-class checkpointer support
- Connection pooling via Hyperdrive (Cloudflare)

**Right card (light red, red border): "✗ MongoDB (Rejected)"**
- Separate vector search service needed ($$$)
- No JOINs — denormalized data management
- Limited multi-document transactions
- Complex aggregation pipelines for CSV export
- No official LangGraph checkpointer
- Wrong paradigm for relational medical data

**Bottom card: "Cloud Database Hosting"**
- Managed PostgreSQL with pgvector extension • Automatic backups & connection pooling
- Scalable compute from shared instances ($25/mo) to dedicated 16XL ($3,730/mo)
- 8GB disk included in base plan • Scales seamlessly as data grows • Zero-downtime upgrades

---

## SLIDE 6: What RxNetwork Gets

Header: "What RxNetwork Gets"
Subheader: "Complete end-to-end medical content classification system"

Eight cards in a 4x2 grid:

Row 1 (blue cards): AI Classification, Excel Whitelist, Admin Dashboard, REST API
Row 2 (green/amber/purple cards): Entity Verification, Multi-Taxonomy, Re-validation, Audit Trail

Each card has:
- Colored title
- Colored separator line
- Short 2-line description

Descriptions:
1. AI Classification — Automated identification of HCP-oriented content across multiple platforms
2. Excel Whitelist — Deduplicated URL list in CSV/XLSX with full metadata & confidence scores
3. Admin Dashboard — Real-time monitoring, search, export, and human-in-the-loop review panel
4. REST API — Programmatic whitelist access for DSP integration (OpenRTB compatible)
5. Entity Verification — NPI-verified physicians, FDA-validated drugs, verified medical institutions
6. Multi-Taxonomy — IAB 3.1, MeSH, ICD-10, DSM-5, RxNorm — all mapped & cross-referenced
7. Re-validation — Scheduled re-scraping ensures URLs remain current and accurately classified
8. Audit Trail — Every classification decision is fully traceable and explainable

---

## SLIDE 7: Admin Dashboard

Header: "Admin Dashboard"
Subheader: "Web-based control center for monitoring, review, and export"

Six cards in a 3x2 grid:

1. **Overview** (blue) — Total URLs processed, whitelist count, confidence distribution, queue status, system health metrics
2. **Whitelist Explorer** (blue) — Searchable and filterable table, export to CSV/XLSX, confidence and category filters, inline preview
3. **HITL Review** (green) — Low-confidence review queue, one-click approve/reject, override with audit reason
4. **Entity Browser** (green) — Browse by: pharmaceutical companies, physicians (NPI-verified), medical schools, biotech, institutions
5. **Analytics** (amber) — Accuracy over time, API cost tracking, processing speed metrics, content change rates, exportable reports
6. **Settings** (amber) — Confidence thresholds, platform management, re-scrape scheduling, API keys, user roles

Footer text: "Built with Next.js • Hosted on Cloudflare Pages ($0) • Real-time updates • Secure authentication"

---

## SLIDE 8: Output: Whitelist Format

Header: "Output: Whitelist Format"
Subheader: "Excel-compatible CSV/XLSX per RxNetwork specification"

**Card: "Required Output Columns"** — Table format:

| Column | Description |
|--------|-------------|
| url | Deduplicated URL validated as HCP content |
| source_domain | Platform domain (e.g., scribd.com, slideshare.net) |
| content_type | PDF, PPT, white paper, clinical summary, research poster, educational material |
| detected_medical_categories | MeSH codes + IAB categories (semicolon-separated) |
| detected_entity_associations | Organization names, physician names, drug names |
| confidence_score | Overall classification confidence (0.00 – 1.00) |

**Bottom card (light blue): "Extended Columns (Recommended)"**
audience_type • source_type • iab_category_codes • icd10_codes • dsm5_categories • fda_drug_names • mesh_codes • last_validated_at

---

## SLIDE 9: Target Entity Categories

Header: "Target Entity Categories"
Subheader: "8 categories per RxNetwork specification — all verified against authoritative sources"

Eight cards in a 4x2 grid:

Row 1 (blue cards):
1. Pharmaceutical Manufacturers — FDA-verified pharma company identification
2. Medical Schools & Academic Centers — Accredited medical education institutions
3. Medical Trade Associations — AMA, specialty societies, professional organizations
4. Recognized Physicians — NPI Registry verified, license-confirmed MDs/DOs

Row 2 (green cards):
5. Healthcare Executives — C-suite and leadership in healthcare organizations
6. Biotech Companies — Biotechnology firms, research organizations
7. Medical Device Manufacturers — FDA-listed medical device companies
8. Prominent Medical Institutions — Major hospitals, research centers, health systems

---

## SLIDE 10: Cloud Infrastructure

Header: "Cloud Infrastructure"
Subheader: "Selective use of Cloudflare services — verified against official documentation"

**Left column: "Services We Use"** (green cards):
- Workers — Whitelist REST API at global edge — $5/mo for 10M requests
- R2 Storage — Document & content archival — $0.015/GB, zero egress fees
- Hyperdrive — PostgreSQL connection pooler — Included on paid plan
- Pages — Admin dashboard hosting — $0 — free static hosting

**Right column: "Services We Don't Use (and Why)"** (red cards):
- Browser Rendering — Our scraping engine is 50x cheaper
- Workers AI — No biomedical classification models available
- D1 Database — SQLite-based — cannot replace PostgreSQL
- Vectorize — Cost-prohibitive at scale ($19K/mo at 50M URLs)

**Bottom card:**
"All pricing verified against official Cloudflare documentation (April 2026)"
"Workers: $5/mo + $0.30/M requests • R2: $0.015/GB + $0 egress • Hyperdrive: Free • Pages: Free"

---

## SLIDE 11: Development Investment

Header: "Development Investment"
Subheader: "One-time development cost — milestone-based delivery"

Table with columns: Phase | Deliverable | Scope | Duration

| Phase | Deliverable | Scope | Duration |
|-------|-------------|-------|----------|
| Phase 0 | Infrastructure & Setup | DB schema, evaluation dataset, CI/CD | 1–2 weeks |
| Phase 1 | Scraping Pipeline | Lightpanda, content extraction, proxy setup | 2–3 weeks |
| Phase 2 | Classification Engine | LangGraph + Claude + scispaCy + NLP pipeline | 3–4 weeks |
| Phase 3 | Entity Resolution | NPI, RxNorm, FDA, UMLS integration | 2–3 weeks |
| Phase 4 | Dashboard & Export | Admin panel, CSV/XLSX export, HITL review | 1–2 weeks |
| Phase 5 | Tuning & QA | Accuracy tuning, testing, security audit | 2–3 weeks |
| Phase 6 | Deployment & Docs | Production deployment, documentation, handoff | 1–2 weeks |

**Total row (blue highlight): Total Development — 12–19 weeks**

Bottom note: "Recommended: Milestone-based payments — 20% upfront, remainder tied to deliverable milestones (M1–M5)"

---

## SLIDE 12: Monthly Infrastructure Costs

Header: "Monthly Infrastructure Costs"
Subheader: "Recurring costs scale with URL volume — client pays directly to service providers"

Three-column comparison table:

| Service | Small (100K URLs) | Medium (1M URLs) | Large (50M URLs) |
|---------|-------------------|-------------------|-------------------|
| Database (PostgreSQL) | $25 | $40 | $275–400 |
| AI Classification (Claude) | $50–100 | $500–1,000 | $10.5K–25K |
| Scraping Infrastructure | $20 | $80 | $200–500 |
| Cache & Queues (Redis) | $0 | $10 | $50–100 |
| Edge API (Cloudflare) | $5 | $5 | $5–45 |
| Object Storage | $0 | $5 | $15–75 |
| Monitoring (LangSmith) | $0 | $164 | $300–500 |
| Rotating Proxies | $50–100 | $100–200 | $500–1K |
| **Monthly Total** | **$170–300** | **$1,004–1,704** | **$12K–28K** |

Column headers have colored backgrounds: Blue for Small, Green for Medium, Amber for Large.

**Bottom warning card (amber):** "Note: Claude API is the dominant cost at scale. Pre-filtering heuristics and batch processing can reduce AI costs by 50–70%."

---

## SLIDE 13: Additional Expenses

Header: "Additional Expenses"
Subheader: "One-time setup costs and optional services"

**Left section: "One-Time Setup Costs"**

| Item | Cost | Note |
|------|------|------|
| Claude API initial deposit | $50–100 | Pre-paid credits for AI classification |
| Proxy service setup | $50–100 | Initial deposit for residential proxy plan |
| Domain registration | $10–15/year | Custom domain for dashboard & API |
| SSL Certificate | $0 | Provided free by Cloudflare |
| UMLS License | $0 | Free federal license (1–3 day approval) |
| **Total Setup** | **$110–215** | |

**Right section: "Optional Services"** (amber cards)

| Service | Cost | Note |
|---------|------|------|
| Legal review of scraping approach | $500–2,000 | Recommended before Scribd/SlideShare |
| Evaluation dataset labeling | $500–1,000 | If outsourced (included if in-house) |
| Post-launch maintenance | $1,000–2,000/mo | Monitoring, bug fixes, re-tuning |
| Scale optimization consulting | Custom | Performance tuning at 10M+ URLs |

---

## SLIDE 14: Investment Summary

Header: "Investment Summary"
Subheader: "Complete cost overview for the RxScope system"

Three summary cards across the top:

**Card 1 (blue): "Development"**
- $18,500 – $30,500
- One-time
- 12–19 weeks, milestone-based payments tied to deliverables

**Card 2 (green): "Infrastructure"**
- $170 – $1,704
- Per month (100K–1M URLs)
- Paid directly to cloud providers. Scales with URL volume.

**Card 3 (amber): "Setup & Extras"**
- $110 – $215
- One-time
- API deposits, domain, proxy initial setup

**Bottom section: "Recommended Payment Structure (Milestone-Based)"**

| % | Milestone | Deliverable | When |
|---|-----------|-------------|------|
| 20% | Project Kickoff | Infrastructure setup, DB schema, evaluation dataset begin | Week 0 |
| 20% | Proof of Concept | Working classifier on 3,000 PubMed URLs + accuracy report | Week 4–5 |
| 25% | First Whitelist | 100K URL whitelist delivered in CSV/XLSX format | Week 11 |
| 20% | Dashboard Live | Admin panel with search, export, and HITL review | Week 14 |
| 15% | Production Launch | Full system running at target scale with monitoring | Week 18–22 |

---

## SLIDE 15: Important Considerations

Header: "Important Considerations"
Subheader: "Technical realities to be aware of before project kick-off"

Six cards in a 2x3 grid:

1. **Scribd / SlideShare Access** (amber) — Scribd has no public API since 2017. Content access is limited to metadata scraping. We recommend starting with legally clean sources (PubMed, open-access journals) in Phase 1, adding Scribd/SlideShare in Phase 2.

2. **Classification Accuracy** (blue) — Expect 85–90% accuracy initially, improving to 95%+ after human-in-the-loop feedback cycles. This is standard for AI classification systems — there is a 2–4 week tuning period.

3. **Cost Scales with Volume** (green) — At 100K URLs: ~$200/month infrastructure. At 50M URLs: ~$15K–20K/month (dominated by Claude API). Pre-filtering heuristics can reduce AI costs by 50–70%.

4. **robots.txt Compliance** (blue) — We respect robots.txt on all platforms. Some sites may limit scraping rate. This is a legal requirement and protects the project long-term.

5. **Ongoing Maintenance** (amber) — Medical content changes constantly — new drugs, guidelines, HCPs. Whitelists need periodic re-scraping and re-classification. Post-launch maintenance recommended.

6. **Separate Billing** (green) — Development is a one-time cost. Infrastructure is monthly recurring, billed directly by service providers (Anthropic, Cloudflare, etc.) to your accounts.

---

## SLIDE 16: Next Steps

Header: "Next Steps"
Subheader: "Questions to finalize scope, and immediate action items"

**Left card (light blue, blue border): "Questions We Need From You"**
- How many URLs in the first batch?
- One-time batch or continuously running system?
- Dashboard required, or CSV exports only?
- Who provides the seed URL list?
- Expected turnaround time?
- Which platforms are mandatory for Phase 1?
- Specific DSP integration needed?
- Budget range for development?

**Right card (light green, green border): "Once Confirmed — We Begin"**
- Confirm URL volume to finalize cost quote
- Agree on milestone-based payment schedule
- Confirm Phase 1 platform scope
- Sign-off on technology stack
- Set up shared cloud accounts
- Kick off Phase 0: Foundation
- Schedule weekly progress demos
- Begin 3,000-URL evaluation dataset

**Bottom card (gray with blue border): "Ready to Build"**
"Architecture is researched & documented • Technology stack selected • Cost models built • Awaiting your confirmation to start"

---

END OF PROMPT. This should generate a complete 16-slide professional presentation.
