# RxScope — Pre-Build Architecture Document

**Version:** 0.1.0-draft  
**Date:** April 5, 2026  
**Author:** Architecture Review  
**Classification:** Confidential (Post-NDA)

---

## Table of Contents

1. [Research Phase — Findings & Reasoning](#1-research-phase)
2. [System Architecture](#2-system-architecture)
3. [LangGraph Agent Pipeline](#3-langgraph-agent-pipeline)
4. [Database Schema Design](#4-database-schema-design)
5. [Classification Pipeline Logic](#5-classification-pipeline-logic)
6. [Entity Resolution Strategy](#6-entity-resolution-strategy)
7. [Gaps & Risks](#7-gaps--risks)
8. [Open Questions for Decision](#8-open-questions-for-decision)
9. [Cloudflare Workers — What They Are & How They Fit](#9-cloudflare-workers)
10. [Timeline Estimate](#10-timeline-estimate)

---

# 1. RESEARCH PHASE

## 1a. Current State of Medical Content Classification in Programmatic Advertising

### Industry Standards

**IAB Content Taxonomy 3.1** (Dec 2024, current) is the ad-industry standard for content categorization. It expanded from ~400 categories (v2.x) to 1,500+ (v3.0/3.1). Version 2.x is being deprecated. RxScope MUST classify against 3.1 or buyers literally cannot ingest your whitelist into their DSP.

Relevant IAB 3.1 tier mappings for RxScope:

```
Tier-1: Health & Fitness (IAB7)
  Tier-2: IAB7-1  Exercise
  Tier-2: IAB7-2  A.D.D.
  Tier-2: IAB7-3  AIDS/HIV
  Tier-2: IAB7-4  Allergies
  Tier-2: IAB7-5  Alternative Medicine
  ...
  Tier-2: IAB7-17 Diseases and Conditions (catch-all)
  Tier-2: IAB7-18 Drugs (Prescription)
  Tier-2: IAB7-19 Drugs (Over-the-Counter)
  ...
  Tier-2: IAB7-38 Nutrition
  Tier-2: IAB7-44 Senior Health
  Tier-2: IAB7-45 Sexuality

Tier-1: Science (IAB15)
  Tier-2: IAB15-2 Biology
  Tier-2: IAB15-4 Chemistry
  Tier-2: IAB15-6 Medicine (General)

Pharma-specific: Maps across IAB7-18 (Prescription Drugs) and custom 
                  advertiser-defined segments
```

**IAB Tech Lab Taxonomy Mapper** (Feb 2026, open-source by Mixpeek): Converts 2.x → 3.0 codes using AI techniques including LLM re-ranking. RxScope should use this mapper to ensure backward compatibility with buyers still on 2.x.

**TAG (Trustworthy Accountability Group):** Brand Safety Certified program. TAG's Brand Safety Framework defines inventory quality tiers. RxScope's whitelist essentially creates "TAG-equivalent" verified inventory. Consider TAG certification for the whitelist itself.

**DAAST (Digital Audio Ad Serving Template) / VAST:** Not directly relevant — these are video/audio ad serving standards, not content classification. What IS relevant is OpenRTB bid request fields where IAB content categories are transmitted. Your whitelist needs to map to `bcat` (blocked categories) and `cat` (content categories) fields in OpenRTB 2.6+.

### What Exists Today

Current brand safety vendors (IAS, DoubleVerify, Oracle/MOAT) do page-level content classification but:
- They classify for brand safety (avoid), not for HCP targeting (seek)
- They don't do medical entity resolution
- They don't verify physician identity via NPI
- They treat all health content equally — no HCP vs. consumer distinction

**This is the core gap RxScope fills.** No existing solution combines medical taxonomy grounding + NPI verification + document-level analysis + programmatic ad-tech output format.

---

## 1b. Scribd & Slideshare API Capabilities

### Scribd

**No public developer API exists.** The Scribd developer page (`scribd.com/developers`) is effectively dead — it shows no documentation, no API keys, no endpoints. Scribd shut down their public API years ago (circa 2016-2017). Scribd, Inc. (which now owns Everand and Slideshare) has NO partner API that provides document content access.

**ToS implications:** Scribd's Global Terms of Use prohibit automated data collection. Their Privacy Policy explicitly addresses data collection methods. Scraping Scribd violates ToS.

### Slideshare

**Partial API via oEmbed.** Slideshare supports oEmbed for embedding — this gives you title, author, thumbnail for any public slide deck via `https://www.slideshare.net/api/oembed/2`. But it does NOT give you slide content text. The old LinkedIn-era Slideshare API was deprecated. No full content API exists.

### Legal Assessment

Both platforms have:
- robots.txt that restrict automated crawling of document content
- ToS that prohibit scraping
- No available developer/partner API for content access

**Critical decision point:** See Section 8, Open Questions #1. You either need:
1. A formal data partnership/licensing agreement with Scribd Inc.
2. To accept legal risk of ToS-violating scraping
3. To pivot to alternative content sources (PubMed, Google Scholar, preprint servers)

---

## 1c. Medical NLP Libraries — Production-Grade Assessment

### Tier 1: Production-Ready

| Library | Type | Best For | Maturity | Stars |
|---------|------|----------|----------|-------|
| **scispaCy** (Allen AI) | spaCy models for biomedical text | Entity detection, dependency parsing, UMLS linking | Stable, actively maintained | ~1.8k |
| **MedSpaCy** (VA/AMIA) | Clinical NLP pipeline on spaCy 3 | Negation detection (ConText), section detection, clinical modifiers | v1.3.1 (Nov 2024), stable | ~644 |
| **Stanza (Biomedical)** (Stanford NLP) | Neural NLP pipeline | Tokenization, POS, NER, dependency parsing for biomedical text | Stable | ~7k+ |

### Tier 2: Powerful but Heavier

| Library | Type | Best For | Notes |
|---------|------|----------|-------|
| **cTAKES** (Apache) | Java-based clinical NLP | UMLS concept extraction, temporal relations | Very mature but Java ecosystem; heavy for a Python pipeline |
| **MetaMap / MetaMap Lite** (NLM) | UMLS concept mapper | Gold-standard UMLS/MeSH mapping | MetaMap Lite is lighter; both require UMLS license |
| **QuickUMLS** | Fast UMLS concept extraction | Approximate string matching to UMLS | Integrated with MedSpaCy; fast but less precise than MetaMap |

### Recommendation for RxScope

**Use scispaCy + MedSpaCy together:**

```
scispaCy:
  - en_core_sci_lg (600k word vectors, general biomedical NER)
  - en_ner_bc5cdr_md (DISEASE + CHEMICAL entities — 84.28% F1)
  - en_ner_bionlp13cg_md (CANCER, GENE, CELL, CHEMICAL, etc. — 77.84% F1)
  - UMLS Entity Linker (links detected entities → UMLS CUI codes)
  
MedSpaCy:
  - medspacy.context → ConText algorithm for negation/uncertainty detection
  - medspacy.section_detection → identifies document sections
  - medspacy.ner → custom target rules for domain-specific terms
  - QuickUMLS integration → fast UMLS concept lookup
```

**Why this combo:**
- scispaCy handles entity extraction with UMLS linking (maps to MeSH/SNOMED/ICD-10 via UMLS CUI codes)
- MedSpaCy handles clinical context (negation — "no evidence of pneumonia" should NOT tag as pneumonia)
- Both are spaCy-native, so they compose into a single `nlp` pipeline
- Python-native, no Java dependency
- Well-tested in production (VA COVID-19 NLP pipeline used MedSpaCy)

**For entity resolution beyond NER:** Use RxNorm API (NLM) for drug name normalization and NPI Registry API (CMS NPPES) for physician verification. These are free federal APIs.

---

## 1d. Vector Embedding Models for Medical/Clinical Text

### Biomedical-Specific Models

| Model | Params | Training Data | Best For | BLURB Score |
|-------|--------|---------------|----------|-------------|
| **BiomedBERT (PubMedBERT)** (Microsoft) | 110M | PubMed abstracts + PMC full-text | Biomedical NER, relation extraction, QA | SOTA on BLURB |
| **SciBERT** (Allen AI) | 110M | Semantic Scholar papers (18% bio, 82% CS) | General scientific text | Good but not best for clinical |
| **ClinicalBERT** | 110M | MIMIC-III clinical notes | Clinical/EHR text specifically | Best for clinical notes, not papers |
| **BioGPT** (Microsoft) | 1.5B | PubMed abstracts | Generative biomedical tasks | Good for generation, overkill for embeddings |
| **BioLinkBERT** (Stanford) | 110M/340M | PubMed with citation graph structure | Document-level understanding | Very strong for document classification |
| **SapBERT** | 110M | UMLS synonyms | Entity linking specifically | Best pure entity resolution model |

### General Models for Comparison

| Model | Dims | Notes |
|-------|------|-------|
| OpenAI `text-embedding-3-large` | 3072 | Very good general; not domain-tuned |
| Cohere `embed-v3` | 1024 | Good multilingual; not biomedical-specific |
| Voyage `voyage-large-2` | 1024 | General purpose |

### Recommendation for RxScope

**Two-model approach:**

1. **BiomedBERT** (`microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`) for content embeddings
   - 357k+ downloads/month (proven adoption)
   - Pretrained from scratch on PubMed + PMC (not fine-tuned general model)
   - SOTA on BLURB benchmark
   - 768 dimensions — manageable for vector DB at 10-50M scale

2. **SapBERT** for entity resolution embeddings
   - Specifically trained on UMLS concept synonymy
   - Maps "Humira" and "adalimumab" to nearby vector space
   - Use for drug/entity name matching when exact string lookup fails

**Why not general models:** The BiomedBERT paper (Gu et al., arXiv:2007.15779) demonstrates that domain-specific pretraining from scratch substantially outperforms continued pretraining of general models for biomedical NLP. For RxScope's classification accuracy, this is not optional.

---

## 1e. IAB Health Taxonomy Tier Mappings

RxScope must output classifications that DSPs can consume. The mapping:

```
RxScope Internal Classification → IAB Content Taxonomy 3.1 Category Code

EXAMPLES:
  Oncology research paper     → IAB7-17 (Diseases/Conditions), IAB15-6 (Medicine)
  Cardiology device study     → IAB7-17, IAB7-15 (Heart Disease)  
  Pharma drug labeling        → IAB7-18 (Prescription Drugs)
  OTC drug guide              → IAB7-19 (OTC Drugs)
  Mental health clinical      → IAB7-33 (Psychology/Psychiatry)
  Orthopedic surgery slides   → IAB7-37 (Orthopedics)
  Nursing education           → IAB7-36 (Nursing)
  Pediatrics lecture          → IAB7-39 (Pediatrics)
  Dental research             → IAB7-10 (Dental Care)
  Dermatology presentation    → IAB7-11 (Dermatology)
```

**Critical: Custom HCP extension.** IAB taxonomy has NO "HCP-only" flag. You must create a custom dimension:

```json
{
  "iab_category": "IAB7-18",
  "iab_category_label": "Prescription Drugs",
  "rxscope_hcp_confidence": 0.92,
  "rxscope_audience_type": "HCP",      // HCP | CONSUMER | MIXED | UNKNOWN
  "rxscope_content_source": "PHARMA_MANUFACTURER",
  "rxscope_attribution_entity": "Pfizer Inc.",
  "rxscope_mesh_codes": ["D000068879"],
  "rxscope_icd10_codes": ["L40.0"]
}
```

This is transmitted to DSPs via deal-level metadata or custom key-value pairs in the bid request.

---

## 1f. Healthcare Content Classification Datasets & Benchmarks

### Available Datasets

| Dataset | Size | Task | Access |
|---------|------|------|--------|
| **BLURB** (Microsoft) | Multiple tasks | Biomedical NER, RE, QA, document classification | Public |
| **MedMentions** (Chan Zuckerberg) | 4,392 PubMed abstracts, 352k mentions | Entity linking to UMLS | Public |
| **BC5CDR** | 1,500 PubMed articles | Chemical-Disease NER | Public |
| **NCBI Disease** | 793 PubMed abstracts | Disease NER | Public |
| **PubMedQA** | 1k expert, 61.2k auto | Biomedical QA | Public |
| **HOC (Hallmarks of Cancer)** | 1,852 PubMed abstracts | Multi-label classification | Public |
| **LitCovid** | 200k+ COVID papers | Document classification by topic | Public |
| **OHSUMED** | 348,566 MEDLINE refs | Document classification | Public (older) |

### What Doesn't Exist

**No public dataset for "is this URL HCP content vs. consumer content."** This is the core classification task, and no benchmark exists. You MUST build your own gold-standard evaluation set:

1. Manually label 2,000-5,000 Scribd/Slideshare URLs as HCP / Consumer / Mixed / Irrelevant
2. Have at minimum 2 independent annotators (ideally with clinical background)
3. Measure inter-annotator agreement (Cohen's kappa ≥ 0.75 target)
4. Split: 70% train/validation for prompt tuning, 30% held-out evaluation
5. This is a **gating prerequisite** before you can measure classifier quality

---

## 1g. Legal Risks of Scraping Scribd & Slideshare at Scale

### Relevant Legal Precedents

| Case | Year | Ruling | Relevance |
|------|------|--------|-----------|
| **hiQ Labs v. LinkedIn** | 2022 (9th Cir.) | Scraping publicly accessible data not a CFAA violation | Favorable for scraping public pages |
| **Meta v. Bright Data** | 2024 | Scraping logged-in content violates ToS and CFAA | Scribd content behind login = risky |
| **X Corp v. Bright Data** | 2024 | Court dismissed some claims on public data scraping | Mixed signals |
| **Clearview AI** (EU/UK/AU) | 2022-2024 | Massive fines for scraping publicly available photos | Privacy risk for any PII extraction |

### Risk Assessment for RxScope

**HIGH RISK areas:**
1. **Scribd content is behind a paywall/login wall.** Most document content requires authentication to view. This pushes into hiQ's "logged-in" territory which courts treat differently from public data. This is the #1 legal risk.
2. **Scribd ToS explicitly prohibit automated access.** While ToS violations aren't necessarily federal crimes post-Van Buren (2021), they are civil tort claims (breach of contract, trespass to chattels).
3. **Volume:** Scraping 10-50M URLs signals commercial intent, increasing damages exposure.

**MEDIUM RISK areas:**
4. Slideshare content is more publicly accessible (many decks viewable without login). Lower risk than Scribd.
5. GDPR Article 6 analysis: if scraping captures European user data, legitimate interest defense is weak for commercial ad-tech use.

**MITIGATION strategies:**
- **Best:** Negotiate a data partnership/licensing deal with Scribd Inc. They have advertising partners (per their privacy policy) — position RxScope as adding value to their ad inventory.
- **Good:** Limit scraping to publicly accessible pages only. Respect robots.txt. Use Lightpanda's `--obey_robots` flag.
- **Acceptable:** Scrape only metadata (title, author, description) available without login. Use this metadata + ML to classify without full content extraction.
- **Also consider:** Common Crawl / WARC archives may contain cached Scribd/Slideshare pages from earlier crawls. These are legally clean to analyze.

---

## 1h. Database Architecture at 10-50M URL Scale

### The Dual Requirement

RxScope needs:
1. **Structured relational data:** URL metadata, entity records, classification results, audit logs, NPI lookups, taxonomy mappings
2. **Vector similarity search:** Content embeddings for deduplication, semantic similarity, nearest-neighbor entity matching

### Option A: PostgreSQL + pgvector (RECOMMENDED)

**Single database, both workloads.**

pgvector (v0.8.2, latest) now supports:
- HNSW and IVFFlat indexes
- Up to 16,000-dimension vectors
- Half-precision vectors (2x storage savings)
- Binary quantization (32x storage savings for initial filtering)
- Iterative index scans (automatically scan more results when filtering)
- Hybrid search (vector + full-text search combined)
- Partitioning for scale
- All PostgreSQL ACID guarantees, replication, JOINs

**At 50M rows with 768-dim vectors:**
- Vector storage: 50M × (768 × 4 + 8) bytes ≈ 144 GB for vectors alone
- HNSW index: ~2x vector storage ≈ 290 GB
- With half-precision: cuts to ~72 GB vectors, ~145 GB index
- Total including relational data: ~300-500 GB — fits comfortably on a single high-memory instance

**Performance:** HNSW gives sub-100ms vector queries at 50M scale with proper tuning (`ef_search=100`, `m=16`).

### Option B: PostgreSQL + Qdrant (separate vector DB)

**Two databases, specialized workloads.**

Qdrant advantages over pgvector:
- Purpose-built vector engine — faster at very high QPS
- Built-in payload filtering extends HNSW graph (single-pass filter+search)
- Better horizontal scaling (sharding + replication built-in)
- Quantization and segment optimization out of the box

Qdrant disadvantages for RxScope:
- Additional infrastructure to maintain
- Data synchronization between PG and Qdrant needed
- No transactional consistency across both stores
- JOINing relational + vector results requires application-level logic

### Recommendation: Start with PostgreSQL + pgvector

**Reasoning:**
1. At 50M URLs, pgvector is well within its performance envelope
2. Single transactional boundary — classification result + vector embedding stored atomically
3. Hybrid search (full-text + vector) is native
4. You eliminate an entire synchronization layer
5. If pgvector becomes a bottleneck at >100M URLs, migrate vectors to Qdrant later — your relational schema stays intact

**When to revisit:** If vector query latency exceeds 200ms at p99, or if you need >1,000 concurrent vector queries/second.

### Redis Role

Redis is NOT a database here. Use it for:
- **Job queue:** Bull/BullMQ for scrape job scheduling, classification pipeline tasks
- **Caching:** NPI lookup results (cache for 24h — physician data changes slowly), RxNorm drug lookups, FDA drug label data
- **Rate limiting:** Per-domain scrape rate limiting, API rate limiting
- **Session/state:** LangGraph checkpointer can use Redis for agent state persistence

---

## 1i. What's Missing From Your Current Thinking

### CRITICAL MISSES (will kill the product)

1. **No gold-standard evaluation dataset.** You cannot measure classifier quality without one. You need labeled data BEFORE building the pipeline.

2. **No advertiser integration specification.** How does the whitelist reach DSPs? Prebid? Custom deal IDs? A segment API? The output format and delivery mechanism determines whether anyone can actually USE the whitelist.

3. **No content access strategy.** Scraping Scribd at scale without a data deal is a legal landmine. This is an existential risk.

4. **No incremental processing strategy.** Processing 50M URLs from scratch takes weeks. You need an incremental pipeline that processes new/changed content and doesn't re-process stable URLs.

### SIGNIFICANT MISSES

5. **Cost model for Claude API.** Processing 10-50M URLs through Claude Sonnet for classification is extremely expensive. At ~$3/MTok input: even 1,000 tokens per URL × 10M URLs = 10B tokens = ~$30,000 per full pass. Budget this.

6. **No monitoring/observability plan.** Classification drift, scrape success rates, entity resolution accuracy — you need metrics from day 1.

7. **No versioning strategy for classifications.** When you retrain/update the classifier, old classifications must be versioned. Advertisers need stable category assignments.

8. **Sitemap-based discovery is missing.** Before scraping content, you need to discover URLs. Scribd/Slideshare sitemaps are the starting point.

9. **No handling for PDFs and images.** Scribd documents are often PDFs. Slideshare decks are images of slides. You need OCR (Tesseract/PaddleOCR) or PDF text extraction (PyMuPDF/pdfplumber) before NLP.

10. **Rights and attribution metadata.** Creative Commons, copyright status of scraped documents — some content cannot legally be analyzed even if accessible.

---

# 2. SYSTEM ARCHITECTURE

## 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RXSCOPE SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────── INGESTION LAYER ─────────────────────────┐
│                                                                   │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐    │
│  │  Sitemap     │   │  URL Queue   │   │  robots.txt Cache  │    │
│  │  Discoverer  │──▶│  (Redis/Bull)│   │  (Redis, 24h TTL)  │    │
│  └─────────────┘   └──────┬───────┘   └────────────────────┘    │
│                            │                                      │
│  ┌────────────────────────▼────────────────────────────┐         │
│  │              SCRAPING ENGINE                         │         │
│  │  ┌──────────────────┐   ┌────────────────────────┐  │         │
│  │  │  Lightpanda       │   │  Playwright (fallback) │  │         │
│  │  │  (Primary, Zig)   │   │  Chrome, JS-heavy      │  │         │
│  │  │  --obey_robots    │   │  pages                  │  │         │
│  │  └────────┬─────────┘   └──────────┬─────────────┘  │         │
│  │           └──────────┬─────────────┘                 │         │
│  │                      ▼                               │         │
│  │  ┌──────────────────────────────────┐                │         │
│  │  │  Rotating Residential Proxy Pool │                │         │
│  │  │  (BrightData / Oxylabs)          │                │         │
│  │  └──────────────────────────────────┘                │         │
│  └──────────────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Raw HTML / PDF / Images
┌──────────────────────── PROCESSING LAYER ────────────────────────┐
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              LANGGRAPH MULTI-AGENT PIPELINE                │   │
│  │                                                            │   │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐             │   │
│  │  │ Extractor │─▶│ Classifier│─▶│  Entity    │             │   │
│  │  │ Agent     │  │ Agent     │  │  Resolver  │             │   │
│  │  │           │  │(Sonnet)   │  │  Agent     │             │   │
│  │  │ -HTML→text│  │           │  │            │             │   │
│  │  │ -PDF→text │  │ -MeSH tag │  │ -RxNorm    │             │   │
│  │  │ -OCR      │  │ -IAB map  │  │ -NPI verify│             │   │
│  │  │ -metadata │  │ -HCP flag │  │ -FDA NDC   │             │   │
│  │  └──────────┘  └───────────┘  └──────┬─────┘             │   │
│  │                                       ▼                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │   │
│  │  │  Confidence  │◀─│  Validator   │◀─│  Dedup Agent  │   │   │
│  │  │  Scorer      │  │  Agent       │  │               │   │   │
│  │  │              │  │              │  │ -Content hash  │   │   │
│  │  │ -Ensemble    │  │ -Cross-check │  │ -SimHash      │   │   │
│  │  │  score 0-1   │  │ -Consistency │  │ -Vector dedup │   │   │
│  │  │ -Threshold   │  │ -Edge cases  │  │               │   │   │
│  │  │  routing     │  │  → Opus 4    │  └───────────────┘   │   │
│  │  └──────┬───────┘  └──────────────┘                       │   │
│  │         │                                                  │   │
│  │         ▼ score < 0.6                                      │   │
│  │  ┌──────────────────┐                                      │   │
│  │  │  Human Review    │                                      │   │
│  │  │  Queue (HITL)    │                                      │   │
│  │  └──────────────────┘                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼  Scored, tagged, verified entries
┌──────────────────────── STORAGE LAYER ───────────────────────────┐
│                                                                   │
│  ┌─────────────────────────────────────────────┐                 │
│  │        PostgreSQL 16+ with pgvector          │                 │
│  │                                              │                 │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────┐  │                │
│  │  │  URLs &   │ │  Entities │ │  Vector    │  │                │
│  │  │  Classif. │ │  (drugs,  │ │  Embeddings│  │                │
│  │  │  Results  │ │  MDs, orgs│ │  (pgvector)│  │                │
│  │  └──────────┘ └───────────┘ └────────────┘  │                │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────┐  │                │
│  │  │  Audit   │ │  Taxonomy │ │  Feedback   │  │                │
│  │  │  Logs    │ │  Mappings │ │  Signals    │  │                │
│  │  └──────────┘ └───────────┘ └────────────┘  │                │
│  └─────────────────────────────────────────────┘                 │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────────┐           │
│  │  Redis               │  │  Object Storage (S3/R2) │           │
│  │  -Job queues         │  │  -Raw scraped content    │           │
│  │  -NPI/RxNorm cache   │  │  -PDF/HTML archives     │           │
│  │  -Rate limiting      │  │  -Classification snapshots│          │
│  │  -Agent state        │  │  -Audit evidence         │           │
│  └─────────────────────┘  └─────────────────────────┘           │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────── DELIVERY LAYER ──────────────────────────┐
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Whitelist API    │  │  Webhook/Push    │  │  Bulk Export  │  │
│  │  (REST/GraphQL)   │  │  Notifications   │  │  (CSV/JSON)   │  │
│  │                   │  │  to DSPs         │  │  for DSP      │  │
│  │  -Query by IAB    │  │                  │  │  import       │  │
│  │  -Query by MeSH   │  │                  │  │               │  │
│  │  -Query by score  │  │                  │  │               │  │
│  │  -Query by entity │  │                  │  │               │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  HITL Review Dashboard (Web UI)                           │    │
│  │  -Low-confidence URL review queue                         │    │
│  │  -Advertiser feedback management                          │    │
│  │  -Classification override workflow                        │    │
│  │  -System health metrics                                   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Re-Scrape Scheduler (Cron)                               │    │
│  │  -30-day cycle for high-value URLs                        │    │
│  │  -90-day cycle for stable URLs                            │    │
│  │  -Immediate re-check on advertiser flag                   │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘

┌──────────────────────── EXTERNAL APIs ───────────────────────────┐
│                                                                   │
│  NPI Registry (CMS NPPES) — Physician identity verification      │
│  RxNorm (NLM) — Drug name ↔ synonym resolution                  │
│  FDA NDC Database — Drug product identification                   │
│  OpenFDA — Adverse events + drug labeling                        │
│  UMLS API (NLM) — Concept ↔ Code crosswalk                      │
│  ClinicalTrials.gov — Research content identification            │
│  MeSH API (NLM) — Medical subject heading lookup                 │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 2.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Sitemap Discoverer | Parse sitemap.xml for Scribd/Slideshare, discover crawlable URLs | Python, `lxml` |
| URL Queue | Priority-based job scheduling, rate limiting per domain | Redis + BullMQ |
| Scraping Engine | Fetch page content, handle JS rendering, obey robots.txt | Lightpanda (primary), Playwright (fallback) |
| Proxy Pool | Rotate residential IPs, avoid rate limits | BrightData / Oxylabs API |
| LangGraph Pipeline | Multi-agent content classification pipeline | LangGraph + Claude API |
| PostgreSQL | Relational data + vector embeddings | PostgreSQL 16 + pgvector 0.8.2 |
| Redis | Job queues, caching, rate limiting | Redis 7+ |
| Object Storage | Raw content archival | Cloudflare R2 or AWS S3 |
| Whitelist API | Serve classified URLs to ad-tech buyers | FastAPI or Cloudflare Workers |
| HITL Dashboard | Review low-confidence classifications | React/Next.js |
| Re-scrape Scheduler | Periodic re-validation of classified URLs | pg_cron or APScheduler |

---

# 3. LANGGRAPH AGENT PIPELINE

## 3.1 Why LangGraph — Yes, Use It

LangGraph is the right choice for RxScope. Here's why after research:

### LangGraph Core Capabilities (Current, 2026)

1. **StateGraph:** Directed graph of agents with typed state passed between nodes. Each agent reads/writes to shared state.
2. **Durable Execution:** Agents can persist through failures and resume. Critical when processing 50M URLs — you CANNOT lose progress.
3. **Human-in-the-Loop (HITL):** Built-in `interrupt()` primitive — pause execution at any node, wait for human input, resume. This is exactly what you need for low-confidence classification review.
4. **Conditional Branching:** Route to different agents based on state (e.g., confidence score → HITL vs. DB write).
5. **Checkpointing:** State persistence to Redis/PostgreSQL. LangGraph can resume a pipeline from any checkpoint.
6. **Streaming:** Stream intermediate results — useful for the dashboard to show processing progress.
7. **LangSmith integration:** Trace every agent decision, debug classification logic, measure latency per node.

### What LangGraph Does NOT Do (And Doesn't Need To)

- It doesn't manage the scraping layer (use Bull/Redis for that)
- It doesn't replace your database (it orchestrates agents that write to PostgreSQL)
- It's not a batch processing framework (use it per-URL or per-batch, with Bull managing the batch queue)

## 3.2 LangGraph Agent Graph — Detailed Design

```
                         ┌─────────┐
                         │  START  │
                         └────┬────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  EXTRACTOR NODE │
                    │                 │
                    │ Input: raw_html │
                    │ Output: clean   │
                    │   text, metadata│
                    │   author, title │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ DEDUP NODE      │
                    │                 │
                    │ Input: text     │
                    │ Output: is_dup, │
                    │   dup_of_url    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
          is_duplicate=True        is_duplicate=False
                │                         │
                ▼                         ▼
        ┌──────────────┐       ┌─────────────────┐
        │ DB_WRITER    │       │ CLASSIFIER NODE │
        │ (mark dup)   │       │                 │
        └──────┬───────┘       │ Input: text,    │
               │               │  metadata       │
               ▼               │ Output:         │
           ┌───────┐           │  mesh_codes,    │
           │  END  │           │  iab_categories,│
           └───────┘           │  hcp_signal,    │
                               │  content_type,  │
                               │  source_type    │
                               └────────┬────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │ ENTITY_RESOLVER NODE │
                              │                      │
                              │ Input: extracted      │
                              │  entities, text       │
                              │ Output:               │
                              │  resolved_drugs[],    │
                              │  verified_physicians[]│
                              │  verified_orgs[],     │
                              │  entity_confidence    │
                              └──────────┬────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │ CONFIDENCE_SCORER    │
                              │                      │
                              │ Input: all upstream   │
                              │  signals              │
                              │ Output:               │
                              │  overall_score (0-1)  │
                              │  component_scores{}   │
                              │  classification_tier  │
                              └──────────┬────────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                   score >= 0.8    0.6 <= score    score < 0.6
                         │          < 0.8               │
                         │               │               │
                         ▼               ▼               ▼
                  ┌────────────┐  ┌────────────┐  ┌──────────────┐
                  │ VALIDATOR  │  │ OPUS_REVIEW│  │ HITL_QUEUE   │
                  │ NODE       │  │ NODE       │  │ NODE         │
                  │            │  │            │  │              │
                  │ Quick      │  │ Claude     │  │ interrupt()  │
                  │ consistency│  │ Opus 4     │  │ Human review │
                  │ checks     │  │ deep review│  │ dashboard    │
                  │            │  │ of edge    │  │              │
                  └─────┬──────┘  │ cases      │  └──────┬───────┘
                        │         └─────┬──────┘         │
                        │               │                │
                        └───────────────┼────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │ DB_WRITER NODE       │
                              │                      │
                              │ - Write to PostgreSQL│
                              │ - Store embedding    │
                              │ - Update whitelist   │
                              │ - Log audit trail    │
                              └──────────┬────────────┘
                                         │
                                         ▼
                                     ┌───────┐
                                     │  END  │
                                     └───────┘
```

## 3.3 LangGraph State Schema

```python
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END

class RxScopeState(TypedDict):
    # Input
    url: str
    raw_html: str
    source_platform: Literal["scribd", "slideshare"]
    
    # Extractor output
    clean_text: str
    title: str
    author: str
    author_credentials: Optional[str]
    document_type: str  # "presentation", "paper", "report", "article"
    language: str
    word_count: int
    metadata: dict
    
    # Dedup output
    content_hash: str  # SimHash or SHA-256 of normalized text
    is_duplicate: bool
    duplicate_of_url: Optional[str]
    embedding: list[float]  # 768-dim BiomedBERT embedding
    
    # Classifier output
    mesh_codes: list[str]
    iab_categories: list[str]
    hcp_signal: float  # 0-1, probability content is HCP-targeted
    content_source_type: Literal[
        "pharma_manufacturer", "medical_school", "trade_association",
        "licensed_physician", "healthcare_executive", "biotech",
        "device_manufacturer", "medical_institution", "unknown"
    ]
    detected_entities: list[dict]  # {text, type, start, end, cui}
    
    # Entity Resolver output
    resolved_drugs: list[dict]  # {name, rxnorm_cui, brand_names[], generic_name}
    verified_physicians: list[dict]  # {name, npi, specialty, org}
    verified_organizations: list[dict]  # {name, type, verified_source}
    icd10_codes: list[str]
    snomed_codes: list[str]
    cpt_codes: list[str]
    
    # Confidence Scorer output
    overall_confidence: float  # 0-1
    component_scores: dict  # {content_quality, entity_resolution, hcp_signal, ...}
    classification_tier: Literal["auto_approve", "opus_review", "human_review"]
    
    # Validator / Review output
    is_approved: bool
    review_notes: Optional[str]
    reviewer: Optional[str]  # "auto", "opus", "human:{user_id}"
    
    # Final output
    whitelist_entry: Optional[dict]
    processing_timestamp: str
    pipeline_version: str
```

## 3.4 LangGraph Code Structure

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

# Define the graph
graph = StateGraph(RxScopeState)

# Add nodes
graph.add_node("extractor", extractor_agent)
graph.add_node("dedup", dedup_agent)
graph.add_node("classifier", classifier_agent)
graph.add_node("entity_resolver", entity_resolver_agent)
graph.add_node("confidence_scorer", confidence_scorer_agent)
graph.add_node("validator", validator_agent)
graph.add_node("opus_review", opus_review_agent)
graph.add_node("hitl_queue", hitl_queue_agent)
graph.add_node("db_writer", db_writer_agent)

# Add edges
graph.add_edge(START, "extractor")
graph.add_edge("extractor", "dedup")

# Conditional: dedup routing
graph.add_conditional_edges(
    "dedup",
    lambda state: "db_writer" if state["is_duplicate"] else "classifier"
)

graph.add_edge("classifier", "entity_resolver")
graph.add_edge("entity_resolver", "confidence_scorer")

# Conditional: confidence-based routing
def route_by_confidence(state: RxScopeState) -> str:
    score = state["overall_confidence"]
    if score >= 0.8:
        return "validator"
    elif score >= 0.6:
        return "opus_review"
    else:
        return "hitl_queue"

graph.add_conditional_edges(
    "confidence_scorer",
    route_by_confidence
)

graph.add_edge("validator", "db_writer")
graph.add_edge("opus_review", "db_writer")
graph.add_edge("hitl_queue", "db_writer")  # After human approves
graph.add_edge("db_writer", END)

# Compile with PostgreSQL checkpointing
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
app = graph.compile(checkpointer=checkpointer, interrupt_before=["hitl_queue"])
```

## 3.5 Agent Implementation Details

### Extractor Agent
```
Input:  raw_html (string), url (string)
Does:   
  1. Detect content type (HTML page, embedded PDF, slide images)
  2. For HTML: BeautifulSoup → clean text, extract title/author/metadata
  3. For PDF: PyMuPDF (fitz) → extract text, fallback to Tesseract OCR
  4. For slides: Extract slide text from Slideshare DOM; fallback OCR
  5. Detect language (langdetect/fasttext)
  6. Extract author credentials from page context
Output: clean_text, title, author, document_type, language, metadata
```

### Classifier Agent
```
Input:  clean_text, title, author, metadata
Does:
  1. Run scispaCy pipeline (en_core_sci_lg + en_ner_bc5cdr_md)
  2. Extract entities: diseases, chemicals, genes, procedures
  3. Run MedSpaCy ConText for negation/uncertainty annotation
  4. Generate BiomedBERT embedding of full text
  5. Call Claude Sonnet with structured prompt:
     "Given this medical document, classify:
      - MeSH subject headings (top 5)
      - IAB content categories (v3.1)
      - Content source type (pharma/academic/physician/etc.)
      - HCP audience probability (0-1)
      - Supporting evidence for each classification"
  6. Map Claude's MeSH suggestions to canonical MeSH tree numbers
  7. Map to IAB 3.1 codes using taxonomy mapper
Output: mesh_codes, iab_categories, hcp_signal, content_source_type, 
        detected_entities, embedding
```

### Entity Resolver Agent
```
Input:  detected_entities, clean_text, author
Does:
  1. FOR EACH drug entity:
     - Query RxNorm API: /rxcui?name={entity}&search=1
     - Get canonical RxCUI, brand names, generic name, NDC codes
     - Cross-reference with OpenFDA drug labels
  2. FOR EACH person entity (potential physician):
     - Query NPI Registry: /api/?first_name=X&last_name=Y
     - Verify NPI number, specialty, organization
     - Check against known medical institution affiliations
  3. FOR EACH organization entity:
     - Check against curated list of med schools, hospitals, pharma cos
     - Verify via ClinicalTrials.gov org search
     - Cross-reference with FDA establishment database
  4. Map entities to ICD-10, SNOMED CT, CPT codes via UMLS crosswalk
Output: resolved_drugs[], verified_physicians[], verified_organizations[],
        icd10_codes, snomed_codes, cpt_codes
```

### Confidence Scorer Agent
```
Input:  All upstream state
Does:
  1. Compute component scores:
     - content_quality: word_count, language, document_type scoring
     - medical_density: ratio of medical entities to total tokens
     - entity_resolution: % of entities successfully resolved
     - hcp_signal_strength: classifier confidence + entity evidence
     - source_verification: physician NPI verified? Org verified?
     - taxonomy_coherence: do MeSH + ICD-10 + IAB codes align?
  2. Weighted ensemble: 
     overall = 0.30 * hcp_signal + 0.25 * entity_resolution + 
               0.20 * source_verification + 0.15 * medical_density + 
               0.10 * taxonomy_coherence
  3. Route decision:
     >= 0.8 → auto_approve (Validator for quick sanity checks)
     0.6-0.8 → opus_review (Claude Opus for deep analysis)
     < 0.6 → human_review (interrupt, queue for HITL dashboard)
Output: overall_confidence, component_scores, classification_tier
```

---

# 4. DATABASE SCHEMA DESIGN

## 4.1 Core Tables

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- trigram similarity for fuzzy text search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- URLS & CLASSIFICATION RESULTS
-- ============================================================

CREATE TABLE urls (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url             TEXT NOT NULL UNIQUE,
    platform        VARCHAR(20) NOT NULL CHECK (platform IN ('scribd', 'slideshare')),
    discovered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ,
    last_classified_at TIMESTAMPTZ,
    scrape_status   VARCHAR(20) DEFAULT 'pending' 
                    CHECK (scrape_status IN ('pending', 'scraped', 'failed', 'blocked', 'removed')),
    http_status     SMALLINT,
    content_hash    BYTEA,  -- SHA-256 of normalized content for exact dedup
    simhash         BIGINT, -- SimHash for near-dedup (Hamming distance comparison)
    duplicate_of_id UUID REFERENCES urls(id),
    robots_allowed  BOOLEAN DEFAULT TRUE,
    
    -- Metadata extracted from page
    title           TEXT,
    author_name     TEXT,
    author_url      TEXT,
    language        VARCHAR(10),
    word_count      INTEGER,
    document_type   VARCHAR(30),
    page_description TEXT,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_urls_platform ON urls(platform);
CREATE INDEX idx_urls_scrape_status ON urls(scrape_status);
CREATE INDEX idx_urls_content_hash ON urls(content_hash);
CREATE INDEX idx_urls_simhash ON urls(simhash);
CREATE INDEX idx_urls_last_scraped ON urls(last_scraped_at);
CREATE INDEX idx_urls_duplicate ON urls(duplicate_of_id) WHERE duplicate_of_id IS NOT NULL;

-- ============================================================
-- CLASSIFICATION RESULTS (versioned — one per classification run)
-- ============================================================

CREATE TABLE classifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_id              UUID NOT NULL REFERENCES urls(id),
    pipeline_version    VARCHAR(20) NOT NULL,
    
    -- Core classification
    is_hcp_content      BOOLEAN NOT NULL,
    hcp_confidence      REAL NOT NULL CHECK (hcp_confidence >= 0 AND hcp_confidence <= 1),
    audience_type       VARCHAR(20) CHECK (audience_type IN ('hcp', 'consumer', 'mixed', 'unknown')),
    
    -- Content source attribution
    source_type         VARCHAR(40),  -- pharma_manufacturer, medical_school, etc.
    attribution_entity  TEXT,         -- e.g., "Pfizer Inc.", "Johns Hopkins University"
    attribution_verified BOOLEAN DEFAULT FALSE,
    
    -- Confidence scores (JSONB for flexibility)
    overall_confidence  REAL NOT NULL CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    component_scores    JSONB,
    
    -- Review status
    classification_tier VARCHAR(20) CHECK (classification_tier IN ('auto_approve', 'opus_review', 'human_review')),
    review_status       VARCHAR(20) DEFAULT 'pending'
                        CHECK (review_status IN ('pending', 'approved', 'rejected', 'overridden')),
    reviewed_by         VARCHAR(100),  -- "auto", "opus", "human:{user_id}"
    review_notes        TEXT,
    reviewed_at         TIMESTAMPTZ,
    
    -- Whitelist inclusion
    on_whitelist        BOOLEAN DEFAULT FALSE,
    whitelist_added_at  TIMESTAMPTZ,
    whitelist_removed_at TIMESTAMPTZ,
    removal_reason      TEXT,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Only one active classification per URL
    is_current          BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_classifications_url ON classifications(url_id);
CREATE INDEX idx_classifications_current ON classifications(url_id) WHERE is_current = TRUE;
CREATE INDEX idx_classifications_whitelist ON classifications(on_whitelist) WHERE on_whitelist = TRUE;
CREATE INDEX idx_classifications_review ON classifications(review_status, classification_tier) 
    WHERE review_status = 'pending';
CREATE INDEX idx_classifications_confidence ON classifications(overall_confidence);

-- ============================================================
-- TAXONOMY TAGS (many-to-many: one classification → many codes)
-- ============================================================

CREATE TABLE classification_taxonomy_tags (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    classification_id   UUID NOT NULL REFERENCES classifications(id) ON DELETE CASCADE,
    taxonomy_system     VARCHAR(20) NOT NULL 
                        CHECK (taxonomy_system IN ('mesh', 'iab', 'icd10', 'snomed', 'cpt', 'dsm5')),
    code                VARCHAR(50) NOT NULL,
    label               TEXT,
    confidence          REAL,
    
    UNIQUE(classification_id, taxonomy_system, code)
);

CREATE INDEX idx_taxonomy_tags_classification ON classification_taxonomy_tags(classification_id);
CREATE INDEX idx_taxonomy_tags_system_code ON classification_taxonomy_tags(taxonomy_system, code);
CREATE INDEX idx_taxonomy_tags_iab ON classification_taxonomy_tags(code) 
    WHERE taxonomy_system = 'iab';

-- ============================================================
-- ENTITIES (drugs, physicians, organizations)
-- ============================================================

CREATE TABLE entities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(30) NOT NULL 
                    CHECK (entity_type IN ('drug', 'physician', 'organization', 'disease', 'procedure', 'device')),
    canonical_name  TEXT NOT NULL,
    
    -- Drug-specific
    rxnorm_cui      VARCHAR(20),
    ndc_codes       TEXT[],
    brand_names     TEXT[],
    generic_name    TEXT,
    
    -- Physician-specific
    npi_number      VARCHAR(10),
    specialty       TEXT,
    medical_school  TEXT,
    
    -- Organization-specific
    org_type        VARCHAR(30),  -- pharma, hospital, medical_school, biotech, device_mfg
    verified_source TEXT,         -- fda_establishment, clinicaltrials_gov, manual
    
    -- UMLS linkage
    umls_cui        VARCHAR(20),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_entities_drug_rxnorm ON entities(rxnorm_cui) 
    WHERE entity_type = 'drug' AND rxnorm_cui IS NOT NULL;
CREATE UNIQUE INDEX idx_entities_physician_npi ON entities(npi_number) 
    WHERE entity_type = 'physician' AND npi_number IS NOT NULL;
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name_trgm ON entities USING gin (canonical_name gin_trgm_ops);

-- Junction table: classifications ↔ entities
CREATE TABLE classification_entities (
    classification_id UUID NOT NULL REFERENCES classifications(id) ON DELETE CASCADE,
    entity_id         UUID NOT NULL REFERENCES entities(id),
    mention_text      TEXT,     -- exact text as found in document
    mention_count     INTEGER DEFAULT 1,
    confidence        REAL,
    
    PRIMARY KEY (classification_id, entity_id)
);

-- ============================================================
-- VECTOR EMBEDDINGS (pgvector)
-- ============================================================

CREATE TABLE content_embeddings (
    url_id          UUID PRIMARY KEY REFERENCES urls(id),
    embedding       vector(768) NOT NULL,  -- BiomedBERT dimension
    model_version   VARCHAR(50) NOT NULL DEFAULT 'BiomedBERT-base-v1',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX idx_embeddings_hnsw ON content_embeddings 
    USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 200);

-- ============================================================
-- DRUG NAME SYNONYMS (for entity resolution)
-- ============================================================

CREATE TABLE drug_synonyms (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rxnorm_cui      VARCHAR(20) NOT NULL,
    synonym         TEXT NOT NULL,
    synonym_type    VARCHAR(20),  -- brand, generic, abbreviation, misspelling
    source          VARCHAR(30),  -- rxnorm, fda_ndc, manual
    
    UNIQUE(rxnorm_cui, synonym)
);

CREATE INDEX idx_drug_synonyms_name ON drug_synonyms USING gin (synonym gin_trgm_ops);
CREATE INDEX idx_drug_synonyms_cui ON drug_synonyms(rxnorm_cui);

-- ============================================================
-- ADVERTISER FEEDBACK LOOP
-- ============================================================

CREATE TABLE advertiser_feedback (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_id              UUID NOT NULL REFERENCES urls(id),
    classification_id   UUID REFERENCES classifications(id),
    advertiser_id       VARCHAR(100) NOT NULL,
    feedback_type       VARCHAR(30) NOT NULL 
                        CHECK (feedback_type IN ('brand_unsafe', 'misclassified', 'not_hcp', 'content_removed', 'approved')),
    feedback_details    TEXT,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed           BOOLEAN DEFAULT FALSE,
    processed_at        TIMESTAMPTZ,
    action_taken        TEXT  -- 'reclassified', 'removed_from_whitelist', 'confirmed', etc.
);

CREATE INDEX idx_feedback_url ON advertiser_feedback(url_id);
CREATE INDEX idx_feedback_unprocessed ON advertiser_feedback(processed) WHERE processed = FALSE;

-- ============================================================
-- AUDIT LOG (immutable)
-- ============================================================

CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,
    entity_type     VARCHAR(30),  -- url, classification, entity, whitelist
    entity_id       UUID,
    actor           VARCHAR(100), -- system, pipeline:{version}, human:{user_id}
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_time ON audit_log(created_at);

-- ============================================================
-- SCRAPE SCHEDULE
-- ============================================================

CREATE TABLE scrape_schedule (
    url_id          UUID PRIMARY KEY REFERENCES urls(id),
    next_scrape_at  TIMESTAMPTZ NOT NULL,
    scrape_interval INTERVAL NOT NULL DEFAULT '30 days',
    priority        SMALLINT DEFAULT 5,  -- 1=highest
    consecutive_failures SMALLINT DEFAULT 0,
    last_change_detected BOOLEAN
);

CREATE INDEX idx_scrape_schedule_next ON scrape_schedule(next_scrape_at) 
    WHERE next_scrape_at <= NOW();

-- ============================================================
-- TAXONOMY REFERENCE TABLES (loaded from external sources)
-- ============================================================

CREATE TABLE mesh_terms (
    tree_number     VARCHAR(20) PRIMARY KEY,
    descriptor_ui   VARCHAR(10) NOT NULL,
    descriptor_name TEXT NOT NULL,
    parent_tree     VARCHAR(20),
    scope_note      TEXT
);

CREATE TABLE iab_categories (
    code            VARCHAR(20) PRIMARY KEY,
    label           TEXT NOT NULL,
    parent_code     VARCHAR(20),
    taxonomy_version VARCHAR(10) DEFAULT '3.1'
);

CREATE TABLE icd10_codes (
    code            VARCHAR(10) PRIMARY KEY,
    description     TEXT NOT NULL,
    category        VARCHAR(100)
);
```

## 4.2 Key Queries the Schema Supports

```sql
-- 1. Get whitelist entries for a DSP export
SELECT u.url, c.hcp_confidence, c.overall_confidence, c.audience_type,
       c.source_type, c.attribution_entity,
       array_agg(DISTINCT t.code) FILTER (WHERE t.taxonomy_system = 'iab') AS iab_codes,
       array_agg(DISTINCT t.code) FILTER (WHERE t.taxonomy_system = 'mesh') AS mesh_codes
FROM urls u
JOIN classifications c ON c.url_id = u.id AND c.is_current = TRUE AND c.on_whitelist = TRUE
LEFT JOIN classification_taxonomy_tags t ON t.classification_id = c.id
WHERE c.overall_confidence >= 0.7
GROUP BY u.id, c.id;

-- 2. Find near-duplicate content by vector similarity
SELECT u2.url, 1 - (ce1.embedding <=> ce2.embedding) AS similarity
FROM content_embeddings ce1
JOIN content_embeddings ce2 ON ce1.url_id != ce2.url_id
JOIN urls u2 ON u2.id = ce2.url_id
WHERE ce1.url_id = '{target_url_id}'
  AND ce1.embedding <=> ce2.embedding < 0.1  -- cosine distance < 0.1 = very similar
ORDER BY ce1.embedding <=> ce2.embedding
LIMIT 10;

-- 3. Get URLs pending human review
SELECT u.url, c.overall_confidence, c.component_scores, c.source_type
FROM classifications c
JOIN urls u ON u.id = c.url_id
WHERE c.review_status = 'pending' AND c.classification_tier = 'human_review'
ORDER BY c.overall_confidence DESC  -- easiest first
LIMIT 50;

-- 4. Drug entity lookup with synonym resolution
SELECT e.canonical_name, e.generic_name, e.brand_names, 
       array_agg(DISTINCT u.url) AS appearing_in_urls
FROM entities e
JOIN classification_entities ce ON ce.entity_id = e.id
JOIN classifications c ON c.id = ce.classification_id AND c.is_current = TRUE
JOIN urls u ON u.id = c.url_id
WHERE e.entity_type = 'drug' 
  AND (e.canonical_name ILIKE '%humira%' OR 'humira' = ANY(e.brand_names))
GROUP BY e.id;
```

---

# 5. CLASSIFICATION PIPELINE LOGIC

## Step-by-step: URL → Whitelist Entry

```
URL Discovered
     │
     ▼
[1] ROBOTS CHECK
     - Fetch and cache robots.txt for domain (24h cache in Redis)
     - Parse with robotparser, check if URL is allowed for our User-Agent
     - If disallowed → mark url.robots_allowed = false, STOP
     │
     ▼
[2] SCRAPE
     - Queue job in BullMQ with rate limiting (max 2 req/sec per domain)
     - Lightpanda fetches page (--obey_robots, CDP protocol)
     - If Lightpanda fails (JS-heavy page) → retry with Playwright + Chrome
     - Store raw HTML in Object Storage (S3/R2) with URL as key
     - Extract HTTP status, store in urls table
     - If 404/410 → mark as 'removed', remove from whitelist if present
     │
     ▼
[3] CONTENT EXTRACTION (Extractor Agent)
     - Detect content type:
       • HTML page with embedded document viewer → extract from viewer DOM
       • PDF (direct link) → PyMuPDF text extraction
       • Slide deck (Slideshare) → extract slide text from DOM spans
       • Image-based slides → OCR with Tesseract/PaddleOCR
     - Normalize text: strip boilerplate, navigation, ads
     - Extract metadata: title, author, publication date, description
     - Detect language (fasttext model)
     - If non-English AND scope is English-only → mark and STOP
     │
     ▼
[4] CONTENT DEDUPLICATION (Dedup Agent)
     - Compute SHA-256 of normalized text → exact dedup
     - Compute SimHash → near-dedup (Hamming distance ≤ 3 = duplicate)
     - Generate BiomedBERT embedding → store in content_embeddings
     - Query pgvector: cosine distance < 0.05 to any existing embedding = semantic dup
     - If duplicate → link to original via duplicate_of_id, STOP (don't reclassify)
     │
     ▼
[5] NLP ENTITY EXTRACTION (part of Classifier Agent)
     - Run scispaCy pipeline:
       • en_core_sci_lg: general biomedical NER
       • en_ner_bc5cdr_md: DISEASE + CHEMICAL entities
     - Run MedSpaCy ConText: mark negated/uncertain entities
     - Run QuickUMLS: link entities to UMLS CUI codes
     - Extract: drug names, disease names, procedure mentions, 
       device names, gene/protein references
     │
     ▼
[6] AI CLASSIFICATION (Classifier Agent - Claude Sonnet)
     - Construct structured prompt with:
       • Document text (truncated to ~3000 tokens if needed)
       • Extracted entities list
       • Author/metadata context
       • Classification schema (MeSH codes, IAB categories, source types)
     - Claude returns:
       • Top 5 MeSH headings with confidence
       • IAB 3.1 category codes
       • Content source type
       • HCP audience probability (0-1)
       • Evidence/reasoning for each classification
     - Validate MeSH codes against mesh_terms table
     - Map to IAB 3.1 using taxonomy mapper
     │
     ▼
[7] ENTITY RESOLUTION (Entity Resolver Agent)
     - For each drug entity:
       a. Exact match in drug_synonyms table
       b. If no match: query RxNorm REST API
       c. If no match: fuzzy match using SapBERT embedding similarity
       d. Store resolved entity with RxNorm CUI, NDC codes, brand/generic names
     - For each person name (potential physician):
       a. Query NPI Registry API (CMS NPPES)
       b. Verify: does this person + specialty match the document context?
       c. If multiple NPI matches: use organization/specialty to disambiguate
       d. Store verified physician with NPI, specialty
     - For each organization:
       a. Check against curated org database (pharma companies, hospitals, med schools)
       b. Cross-reference with FDA establishment database
       c. Store with verification source
     │
     ▼
[8] CONFIDENCE SCORING (Confidence Scorer Agent)
     - Component scores (each 0-1):
       • hcp_signal: Claude's HCP audience probability
       • entity_density: medical entities per 100 tokens
       • entity_resolution_rate: % entities resolved to canonical entries
       • source_verification: is author/org verified via NPI/FDA/known list?
       • taxonomy_coherence: do MeSH, ICD-10, IAB codes form a consistent picture?
       • content_quality: word count, language quality, document structure
     - Ensemble formula:
       overall = Σ(weight_i × score_i) / Σ(weight_i)
       weights = {hcp: 0.30, entity_res: 0.25, source_ver: 0.20, 
                  density: 0.15, coherence: 0.10}
     - Tier routing:
       ≥ 0.80 → auto_approve
       0.60-0.79 → opus_review (ambiguous, send to Claude Opus)
       < 0.60 → human_review (too uncertain for automation)
     │
     ▼
[9] VALIDATION / REVIEW
     - auto_approve path:
       • Quick consistency checks (no contradictions in classification)
       • Verify URL is still accessible
       • APPROVED → proceed to DB write
     - opus_review path:
       • Send full context to Claude Opus 4 with detailed prompt
       • "Review this classification. The system is uncertain because..."
       • Opus can: confirm, reject, reclassify, or escalate to human
     - human_review path:
       • LangGraph interrupt() — pipeline pauses
       • URL appears in HITL dashboard
       • Human reviewer: approve, reject, reclassify, add notes
       • Pipeline resumes after human action
     │
     ▼
[10] DB WRITE & WHITELIST UPDATE (DB Writer Agent)
     - Insert classification record with all taxonomy tags
     - Insert/update entity records
     - Set is_current = FALSE on previous classification for this URL
     - If approved AND overall_confidence >= threshold:
       • Set on_whitelist = TRUE
       • Record whitelist_added_at
     - Insert audit_log entry
     - Schedule next re-scrape (30-day default, 90-day for stable content)
     - Emit event for webhook notification to subscribers
```

---

# 6. ENTITY RESOLUTION STRATEGY

## 6.1 Drug Name Resolution

This is the hardest entity resolution problem. Drug names vary wildly:

```
"Humira" = "adalimumab" = "HUMIRA" = "Humira Pen" = "adalimumab-atto" (biosimilar)
"Tylenol" = "acetaminophen" = "paracetamol" (outside US)
"Advair" = "fluticasone/salmeterol" = "Seretide" (outside US)
```

### Resolution Pipeline (ordered by precision)

```
Step 1: Exact Match (drug_synonyms table)
  - Pre-loaded from RxNorm + FDA NDC
  - O(1) lookup, highest confidence
  - Handles: "Humira" → adalimumab

Step 2: RxNorm API Approximate Match
  - POST /rxcui?name={entity}&search=2 (approximate)
  - Handles: "Humira Pen" → adalimumab + device form
  - Handles misspellings: "Humirah" → Humira

Step 3: SapBERT Embedding Similarity
  - Encode entity with SapBERT, compare against pre-computed drug name embeddings
  - Cosine similarity > 0.85 → match
  - Handles: abbreviated/informal drug names

Step 4: Claude Fallback (expensive, use sparingly)
  - "Is '{entity_text}' a drug name? If so, what is the generic name?"
  - Use only when Steps 1-3 all fail and entity looks pharmaceutical
```

### Drug Synonym Database (Pre-Load at System Init)

```
Source: RxNorm full release (download from NLM, ~2GB)
  → Extract: rxcui, term_type (brand/generic/ingredient), name
  → Load into drug_synonyms table
  
Source: FDA NDC database (download from FDA)
  → Extract: proprietary_name, nonproprietary_name, ndc_code, labeler_name
  → Cross-reference with RxNorm CUIs
  → Load into drug_synonyms + entities tables

Source: OpenFDA drug labels
  → Extract: openfda.brand_name, openfda.generic_name, openfda.rxcui
  → Supplement missing entries

Refresh cadence: Monthly (RxNorm publishes monthly updates)
```

## 6.2 Physician Identity Verification

### NPI Registry Lookup

```
API: https://npiregistry.cms.hhs.gov/api/?version=2.1
     &first_name={first}&last_name={last}
     &enumeration_type=NPI-1  (individuals only)
     
Returns: NPI number, specialty, organization, address
Rate limit: None published, but be respectful (1 req/sec)
Cache: Redis, 7-day TTL (physician data is stable)
```

### Disambiguation Strategy

A document says "Dr. James Smith, cardiology" — NPI search returns 47 matches.

```
Step 1: Filter by specialty (taxonomy code match)
Step 2: Filter by state/city if mentioned in document
Step 3: Filter by organization if mentioned
Step 4: If multiple remain → DO NOT verify. Mark as "unverified physician"
  (False verification is worse than no verification)
```

## 6.3 Organization Verification

### Curated Reference Database (Build Once, Maintain)

```
Sources:
  - Top 200 pharmaceutical companies (from PharmaCompass)
  - Top 200 medical device companies (from FDA GUDID)
  - All LCME-accredited medical schools (~160 in US)
  - All ACGME-accredited teaching hospitals
  - Major research institutions (NIH, Mayo, Cleveland Clinic, etc.)
  - Major medical associations (AMA, AHA, ASCO, etc.)

Store in entities table with entity_type = 'organization'
Match incoming text against canonical names with trigram similarity:
  SELECT * FROM entities 
  WHERE entity_type = 'organization' 
    AND similarity(canonical_name, 'Johns Hopkins') > 0.6
  ORDER BY similarity(canonical_name, 'Johns Hopkins') DESC
  LIMIT 5;
```

---

# 7. GAPS & RISKS

## Priority 1: WILL KILL THE PRODUCT IF IGNORED

| # | Gap/Risk | Impact | Mitigation |
|---|----------|--------|------------|
| 1 | **No legal content access strategy** | Scraping Scribd behind paywall = lawsuit risk. No API exists. | Negotiate data partnership with Scribd Inc. OR pivot to publicly accessible medical content platforms (PubMed, preprint servers, open-access journals). |
| 2 | **No evaluation dataset** | Cannot measure if classifier works. Cannot quote accuracy to advertisers. Cannot improve. | Build 3,000-5,000 labeled URL gold standard BEFORE building pipeline. Budget 2-3 weeks. |
| 3 | **Advertiser delivery mechanism undefined** | Whitelist is useless if DSPs can't consume it. "What format? What protocol?" | Define output spec: Prebid segment? Custom deal ID mapping? CSV bulk upload? API endpoint? Talk to 2-3 target DSP/SSP partners BEFORE building. |
| 4 | **Claude API cost at scale** | 10M URLs × $0.003-$0.015 per classification = $30K-$150K per full pass. Re-runs compound cost. | Implement tiered classification: cheap heuristic filter first (eliminate 70% of non-medical content), only send plausible medical content to Claude. |

## Priority 2: REGULATORY RISK

| # | Gap/Risk | Impact | Mitigation |
|---|----------|--------|------------|
| 5 | **HIPAA exposure** | If scraped documents contain patient data (case studies with names/dates), you're a HIPAA business associate by possession. | Implement PII/PHI scanner in Extractor agent. If ANY patient identifiers detected, flag and do NOT store raw content. Use HIPAA-aware NLP (MedSpaCy has some support). |
| 6 | **FDA 21 CFR Part 11** | If pharma clients use whitelist for drug promotion campaigns, classification accuracy becomes a regulatory artifact. Misclassification → off-label promotion liability for advertiser. | Add disclaimers in service agreement. Classification is "content categorization for ad placement" — NOT "drug promotion approval." Legal review of client contracts. |
| 7 | **GDPR/CCPA data collection** | Scraping captures author names, potentially EU persons. Storing this data without consent = GDPR violation. | Minimize PII storage. Store only what's needed for classification. Implement data retention policy. GDPR Article 6(f) legitimate interest assessment needed. |
| 8 | **Copyright of scraped content** | Storing full document text = potential copyright infringement. Fair use defense is weak for commercial purpose. | Store only extracted features, classifications, and embeddings — NOT full text. Store text temporarily in RAM during pipeline processing, then discard. |

## Priority 3: CLASSIFICATION QUALITY RISK

| # | Gap/Risk | Impact | Mitigation |
|---|----------|--------|------------|
| 9 | **False positive: patient forum quoting physician** | Patient asking "Dr. Smith said I should take Humira — is this right?" gets classified as HCP content. | Multi-signal classification. Don't rely on entity presence alone. Check document STRUCTURE: is this a medical paper or a forum post? Author context > entity extraction. |
| 10 | **Classification drift over time** | Model performance degrades as content distribution shifts. | Implement shadow evaluation: randomly sample 100 classified URLs/week, human-review them, track accuracy over time. Alert if accuracy drops below 85%. |
| 11 | **Multilingual content blind spot** | Non-English medical content on Scribd is substantial (Spanish, Portuguese, Hindi). English-only = missed inventory. | Phase 1: English only. Phase 2: Add top 3 languages. scispaCy has limited multilingual support. May need multilingual BiomedBERT variants. |
| 12 | **Stale content** | URL classified as HCP 6 months ago may now be deleted or changed. Advertiser serves ad on dead page. | Re-scrape scheduler. High-value URLs: 30 days. Stable URLs: 90 days. On advertiser flag: immediate re-check. |

## Priority 4: INFRASTRUCTURE RISK

| # | Gap/Risk | Impact | Mitigation |
|---|----------|--------|------------|
| 13 | **Proxy ban/block** | Scribd/Slideshare detect and block scrapers. Residential proxies flagged. | Proxy rotation with backoff. Fingerprint randomization. Consider headless browser fingerprint rotation (Lightpanda). Budget for proxy costs ($500-2000/month). |
| 14 | **Single point of failure: Claude API** | If Anthropic has an outage, entire classification pipeline stops. | Implement circuit breaker. Queue jobs during outage. Consider fallback to local model (fine-tuned Llama) for basic classification. |
| 15 | **pgvector performance at full scale** | 50M 768-dim vectors + filtered queries may exceed pgvector performance. | Monitor query latency. If p99 > 200ms, migrate to Qdrant. Use half-precision vectors from day 1 (enough for dedup similarity). |
| 16 | **No disaster recovery plan** | Database corruption or accidental deletion of whitelist = advertisers lose targeting. | PostgreSQL streaming replication + daily WAL backups. S3/R2 for content archives. Classification results are the crown jewels — protect accordingly. |

---

# 8. OPEN QUESTIONS FOR DECISION

## Decision 1: Content Access Strategy (BLOCKERS — Decide First)

**Options:**

| Option | Approach | Risk | Cost | Speed |
|--------|----------|------|------|-------|
| **A: Data Partnership** | Negotiate licensing deal with Scribd Inc. for content access API | Low legal risk. Best long-term. | $$$$ (licensing fees) | Slow (3-6 months negotiation) |
| **B: Scrape with Legal Acceptance** | Scrape public pages only, respect robots.txt, accept ToS risk | Medium legal risk. Scribd ToS violation. | $$ (proxy costs) | Fast (can start now) |
| **C: Hybrid Source Pivot** | Scribd/Slideshare for metadata only + PubMed/PMC/preprint servers for full content | Low legal risk. Less inventory. | $ | Fast (PubMed is open) |

**Recommendation:** Start with C (build pipeline on legally clean PubMed/PMC content), pursue A in parallel (data deal takes time). If A succeeds, backfill Scribd content legally.

---

## Decision 2: Language Scope

| Option | Scope | Inventory Size | Complexity |
|--------|-------|----------------|------------|
| **A: English Only** | English documents only | ~60% of medical content on these platforms | Simple. Best NLP tools. |
| **B: English + Top 5** | EN, ES, PT, FR, DE, ZH | ~90% coverage | scispaCy has limited non-EN. Need multilingual models. 2-3x effort. |
| **C: Language-Agnostic** | Embed with multilingual model, classify in any language | ~100% coverage | Significant accuracy trade-off. Not recommended for Phase 1. |

**Recommendation:** A for MVP. Add Spanish (biggest non-EN medical content on Scribd) as Phase 2.

---

## Decision 3: Confidence Threshold for Whitelist Inclusion

| Threshold | Precision (est.) | Recall (est.) | Trade-off |
|-----------|-------------------|---------------|-----------|
| **0.90** | Very high (~98%) | Low (~40%) | Very safe, small whitelist. Advertisers get premium quality. |
| **0.75** | High (~92%) | Medium (~65%) | Good balance. Some edge cases slip through. |
| **0.60** | Medium (~85%) | High (~80%) | Larger whitelist but more false positives. Needs advertiser feedback loop. |

**Recommendation:** 0.75 default, allow per-advertiser threshold override. Some advertisers want precision (branded pharma), others want reach (medical education).

---

## Decision 4: Vector Database Strategy

| Option | Pros | Cons |
|--------|------|------|
| **A: pgvector only** | Single DB, ACID, simpler ops | Slower at >100M vectors, less optimized for pure vector workloads |
| **B: pgvector + Qdrant** | Best-of-both, Qdrant is faster for vector-only queries | Two systems to maintain, sync complexity |
| **C: Qdrant only** (for vectors) + PG for relational | Cleanest separation | Still need sync; can't do atomic writes |

**Recommendation:** A (pgvector only) for now. The 50M URL scale is well within pgvector's capability with HNSW indexes and half-precision vectors. Migrate to B only if you measure a performance problem.

---

## Decision 5: HITL Review Interface

| Option | Approach | Build Time | Quality |
|--------|----------|------------|---------|
| **A: Custom Web App** | Build React dashboard with classification review UI | 3-4 weeks | Best UX, tailored to workflow |
| **B: Retool/Appsmith** | Low-code internal tool builder connected to PostgreSQL | 1 week | Functional, ugly, faster to ship |
| **C: Label Studio** | Open-source annotation platform, adapt for URL review | 1-2 weeks | Built for annotation, may need customization |

**Recommendation:** B for MVP (get reviews flowing immediately), transition to A when you have revenue.

---

## Decision 6: Hosting & Deployment

| Option | Where | Cost (est.) | Notes |
|--------|-------|-------------|-------|
| **A: AWS** | ECS/EKS + RDS + ElastiCache | $2,000-5,000/mo at scale | Most services, most expensive |
| **B: Cloudflare + Fly.io + Neon** | Workers (API) + Fly (pipeline) + Neon (PG) | $500-2,000/mo | Cheaper, modern. Workers for API edge distribution. |
| **C: Self-managed VPS** | Hetzner/OVH dedicated servers | $200-800/mo | Cheapest, most ops burden |

**Recommendation:** B is the sweet spot. Cloudflare Workers for the whitelist API (global edge, low latency — this is what your client was referring to). Fly.io or Railway for the LangGraph pipeline (needs long-running processes). Neon or Supabase for PostgreSQL with pgvector.

---

## Decision 7: MVP Scope

| Option | Scope | Time |
|--------|-------|------|
| **A: Full Pipeline** | Everything described here | 4-6 months |
| **B: Scribd/Slideshare Only + Core Classification** | Scrape → Extract → Classify → Score → Whitelist API | 8-12 weeks |
| **C: PubMed Proof-of-Concept** | PubMed/PMC content only, no scraping, demonstrate classification quality | 3-4 weeks |

**Recommendation:** C first (prove classifier works on clean data), then B (add scraping), then A (add all entity resolution, HITL, feedback loops).

---

# 9. CLOUDFLARE WORKERS — What They Are & How They Fit

## What Are Cloudflare Workers?

Cloudflare Workers are a **serverless computing platform** that runs JavaScript/TypeScript/Python code at Cloudflare's **300+ global edge locations**. Think "AWS Lambda, but deployed to every continent automatically, running within 50ms of any user globally."

### Key Properties:
- **Edge execution:** Code runs at the nearest Cloudflare data center to the requester — typically <50ms latency
- **V8 isolates:** Not containers, not VMs — lightweight V8 engine isolates. Cold start in <5ms (vs. Lambda's 100-500ms)
- **No server management:** Zero infrastructure. Deploy code, it runs everywhere
- **Free tier:** 100k requests/day free. Paid: $5/month for 10M requests
- **Integrations:** D1 (SQL), KV (key-value), R2 (S3-compatible storage), Vectorize (vector DB), Queues, Durable Objects

## How They Relate to RxScope

Your client mentioned Cloudflare Workers because they're ideal for several RxScope components:

### 1. Whitelist API (PRIMARY USE CASE)
```
Advertiser DSP → Cloudflare Worker (edge) → Query PostgreSQL → Return whitelist results

Why Workers:
- DSPs make bid decisions in <100ms. Your API MUST respond fast.
- Workers run at the edge — 20ms response time vs. 200ms from a central server.
- Auto-scales to handle auction traffic spikes (100k+ RPM during peak).
- Hyperdrive: Cloudflare's connection pooler for PostgreSQL. Caches queries at edge.
```

### 2. Object Storage (R2)
```
Cloudflare R2 = S3-compatible storage with ZERO egress fees.
Use for: raw scraped HTML/PDF archival, classification snapshots, export files.
Saves significant $ vs. S3 at 50M+ documents.
```

### 3. Queues
```
Cloudflare Queues for lightweight job scheduling.
Use for: webhook delivery to advertisers, scheduled re-scrape triggers.
Not for main pipeline (use Redis/Bull for that — Workers have 30s execution limit).
```

### 4. Vectorize (FUTURE)
```
Cloudflare Vectorize = managed vector database. 
Currently limited to 5M vectors per index. Not enough for 50M URLs.
BUT: If they scale it, you could use it for the edge-based dedup/similarity layer.
```

### What Workers CANNOT Do for RxScope:
- **Run the LangGraph pipeline.** Workers have a 30-second CPU time limit. Classification takes longer. Use Fly.io/Railway/VPS for pipeline workers.
- **Run scispaCy/BiomedBERT.** Python ML models don't run on Workers (it's primarily JS/TS). Run these on dedicated compute.
- **Replace PostgreSQL.** D1 is SQLite-based and limited. Use a real PostgreSQL instance (Neon/Supabase).

### Architecture with Workers:
```
┌──────────────────────────────────────────────────────────┐
│                    CLOUDFLARE EDGE                        │
│                                                          │
│  ┌──────────────┐  ┌─────────┐  ┌─────────────────┐    │
│  │  Whitelist   │  │   R2    │  │   Queues        │    │
│  │  API Worker  │  │ Storage │  │ (webhooks,      │    │
│  │              │  │         │  │  notifications)  │    │
│  └──────┬───────┘  └─────────┘  └─────────────────┘    │
│         │ Hyperdrive                                     │
└─────────┼────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌──────────────────────────────┐
│  PostgreSQL + pgvec │     │  Fly.io / Railway            │
│  (Neon/Supabase)    │◀───▶│  LangGraph Pipeline Workers  │
│                     │     │  scispaCy, BiomedBERT        │
└─────────────────────┘     │  Claude API calls            │
                            └──────────────────────────────┘
```

---

# 10. TIMELINE ESTIMATE

## Phase 0: Foundation (Weeks 1-3)
- [ ] Finalize content access strategy decision
- [ ] Set up PostgreSQL schema + pgvector
- [ ] Set up Redis
- [ ] Build evaluation dataset (label 3,000 URLs manually)
- [ ] Set up LangSmith for pipeline tracing
- **Milestone:** Infrastructure ready, gold-standard dataset exists

## Phase 1: Proof of Concept (Weeks 4-7)
- [ ] Build Extractor agent (HTML → clean text)
- [ ] Build Classifier agent (scispaCy + Claude Sonnet prompt)
- [ ] Build basic Confidence Scorer
- [ ] Test on PubMed/PMC content (legally clean)
- [ ] Measure precision/recall against gold standard
- [ ] Iterate on classification prompt until >85% accuracy
- **Milestone:** Classifier proven on evaluation data

## Phase 2: Entity Resolution (Weeks 8-10)
- [ ] Load RxNorm + FDA NDC drug database
- [ ] Build Entity Resolver agent (drug names, NPI lookup, org verification)
- [ ] Build drug synonym resolution pipeline
- [ ] Integrate UMLS crosswalk (MeSH ↔ ICD-10 ↔ SNOMED)
- **Milestone:** Entity resolution working, drug name normalization proven

## Phase 3: Scraping Layer (Weeks 10-13)
- [ ] Set up Lightpanda (primary) + Playwright (fallback)
- [ ] Build sitemap discoverer for target platforms
- [ ] Implement proxy rotation (BrightData/Oxylabs)
- [ ] Build URL queue with rate limiting (BullMQ)
- [ ] Build Dedup agent (content hash + SimHash + vector similarity)
- [ ] Legal review of scraping approach
- **Milestone:** End-to-end pipeline from URL discovery → classification

## Phase 4: Delivery & HITL (Weeks 14-17)
- [ ] Build Whitelist API (Cloudflare Worker + Hyperdrive)
- [ ] Build HITL Review Dashboard (Retool MVP)
- [ ] Build Re-scrape Scheduler
- [ ] Build Advertiser Feedback ingestion
- [ ] Implement CSV/JSON bulk export for DSP import
- [ ] IAB 3.1 taxonomy mapping validation
- **Milestone:** Advertisers can consume the whitelist

## Phase 5: Scale & Harden (Weeks 18-22)
- [ ] Scale to target URL volume (10M+)
- [ ] Performance optimization (pgvector tuning, batch processing)
- [ ] Implement monitoring/alerting (classification drift detection)
- [ ] Implement classification versioning
- [ ] HIPAA/PHI scanner in Extractor
- [ ] Security audit
- [ ] Documentation for advertiser integration
- **Milestone:** Production-ready system

## Total Estimated Build Time

| Scenario | Time | Team Size |
|----------|------|-----------|
| **Solo developer (you)** | 20-24 weeks (~5-6 months) | 1 |
| **Small team (2-3 devs)** | 12-16 weeks (~3-4 months) | 2-3 |
| **With existing ML infra** | 10-14 weeks (~2.5-3.5 months) | 2-3 |

**Critical path:** Evaluation dataset → Classifier accuracy → Entity resolution → Everything else is parallelizable.

---

## Appendix A: External API Reference

| API | URL | Auth | Rate Limit | Cost |
|-----|-----|------|------------|------|
| NPI Registry | `https://npiregistry.cms.hhs.gov/api/` | None | Unspecified (be respectful) | Free |
| RxNorm | `https://rxnav.nlm.nih.gov/REST/` | None | Unspecified | Free |
| FDA NDC | `https://api.fda.gov/drug/ndc.json` | API key (free) | 240/min with key | Free |
| OpenFDA | `https://api.fda.gov/drug/` | API key (free) | 240/min with key | Free |
| UMLS | `https://uts-ws.nlm.nih.gov/rest/` | API key (free, requires UMLS license) | 20/sec | Free (license required) |
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2/` | None | 10/sec | Free |
| MeSH | `https://id.nlm.nih.gov/mesh/` | None | Unspecified | Free |
| Claude API | `https://api.anthropic.com/v1/` | API key | Per plan | $3/MTok input (Sonnet) |

## Appendix B: Cost Estimation (Monthly at Scale)

| Item | Estimated Monthly Cost |
|------|----------------------|
| Claude Sonnet API (10M classifications/month) | $15,000 - $45,000 |
| Claude Opus (5% of URLs for edge cases) | $3,000 - $10,000 |
| PostgreSQL (Neon/Supabase, 500GB) | $100 - $300 |
| Redis (Upstash or managed) | $50 - $200 |
| Cloudflare Workers (Whitelist API) | $5 - $50 |
| Cloudflare R2 (1TB stored content) | $15 |
| Fly.io (Pipeline workers, 2-4 instances) | $100 - $400 |
| Residential Proxies (BrightData) | $500 - $2,000 |
| BiomedBERT embedding inference (GPU) | $200 - $800 |
| **Total** | **$19,000 - $59,000/month** |

**The Claude API is the dominant cost.** Reduce it with:
1. Pre-filter: keyword/heuristic filter eliminates 60-70% of non-medical URLs before Claude
2. Batch API: Use Claude batch mode for non-urgent classification (50% price reduction)
3. Caching: If URL content hasn't changed on re-scrape, don't reclassify
4. Local model: Fine-tune Llama/Mistral on your labeled data for cheap first-pass classification, use Claude only for uncertain cases

---

*End of Architecture Document — RxScope v0.1.0-draft*
