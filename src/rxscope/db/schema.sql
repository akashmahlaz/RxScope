-- RxScope Database Schema v0.1.0
-- PostgreSQL 16 + pgvector + pg_trgm

-- Extensions: gracefully skip if unavailable on managed hosts
DO $$ BEGIN CREATE EXTENSION IF NOT EXISTS vector; EXCEPTION WHEN OTHERS THEN RAISE NOTICE 'pgvector not available — embedding columns will be unused'; END $$;
DO $$ BEGIN CREATE EXTENSION IF NOT EXISTS pg_trgm; EXCEPTION WHEN OTHERS THEN RAISE NOTICE 'pg_trgm not available — fuzzy search disabled'; END $$;
DO $$ BEGIN CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; EXCEPTION WHEN OTHERS THEN RAISE NOTICE 'uuid-ossp not available — use gen_random_uuid() instead'; END $$;

-- ══════════════════════════════════════════
-- URLS & SCRAPE STATUS
-- ══════════════════════════════════════════

CREATE TABLE urls (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url             TEXT NOT NULL UNIQUE,
    platform        VARCHAR(50) NOT NULL,
    discovered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ,
    last_classified_at TIMESTAMPTZ,
    scrape_status   VARCHAR(20) DEFAULT 'pending'
                    CHECK (scrape_status IN ('pending', 'scraped', 'failed', 'blocked', 'removed')),
    http_status     SMALLINT,
    content_hash    BYTEA,
    simhash         BIGINT,
    duplicate_of_id UUID REFERENCES urls(id),
    robots_allowed  BOOLEAN DEFAULT TRUE,
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

-- ══════════════════════════════════════════
-- CLASSIFICATIONS (versioned)
-- ══════════════════════════════════════════

CREATE TABLE classifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_id              UUID NOT NULL REFERENCES urls(id),
    pipeline_version    VARCHAR(20) NOT NULL,
    is_hcp_content      BOOLEAN NOT NULL,
    hcp_confidence      REAL NOT NULL CHECK (hcp_confidence >= 0 AND hcp_confidence <= 1),
    audience_type       VARCHAR(20) CHECK (audience_type IN ('hcp', 'consumer', 'mixed', 'unknown')),
    source_type         VARCHAR(40),
    attribution_entity  TEXT,
    attribution_verified BOOLEAN DEFAULT FALSE,
    overall_confidence  REAL NOT NULL CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    component_scores    JSONB,
    classification_tier VARCHAR(20) CHECK (classification_tier IN ('auto_approve', 'opus_review', 'human_review')),
    review_status       VARCHAR(20) DEFAULT 'pending'
                        CHECK (review_status IN ('pending', 'approved', 'rejected', 'overridden')),
    reviewed_by         VARCHAR(100),
    review_notes        TEXT,
    reviewed_at         TIMESTAMPTZ,
    on_whitelist        BOOLEAN DEFAULT FALSE,
    whitelist_added_at  TIMESTAMPTZ,
    whitelist_removed_at TIMESTAMPTZ,
    removal_reason      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_current          BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_classifications_url ON classifications(url_id);
CREATE INDEX idx_classifications_current ON classifications(url_id) WHERE is_current = TRUE;
CREATE INDEX idx_classifications_whitelist ON classifications(on_whitelist) WHERE on_whitelist = TRUE;
CREATE INDEX idx_classifications_review ON classifications(review_status, classification_tier)
    WHERE review_status = 'pending';
CREATE INDEX idx_classifications_confidence ON classifications(overall_confidence);

-- ══════════════════════════════════════════
-- TAXONOMY TAGS (many-to-many)
-- ══════════════════════════════════════════

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

-- ══════════════════════════════════════════
-- ENTITIES (drugs, physicians, organizations)
-- ══════════════════════════════════════════

CREATE TABLE entities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(30) NOT NULL
                    CHECK (entity_type IN ('drug', 'physician', 'organization', 'disease', 'procedure', 'device')),
    canonical_name  TEXT NOT NULL,
    rxnorm_cui      VARCHAR(20),
    ndc_codes       TEXT[],
    brand_names     TEXT[],
    generic_name    TEXT,
    npi_number      VARCHAR(10),
    specialty       TEXT,
    medical_school  TEXT,
    org_type        VARCHAR(30),
    verified_source TEXT,
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

CREATE TABLE classification_entities (
    classification_id UUID NOT NULL REFERENCES classifications(id) ON DELETE CASCADE,
    entity_id         UUID NOT NULL REFERENCES entities(id),
    mention_text      TEXT,
    mention_count     INTEGER DEFAULT 1,
    confidence        REAL,
    PRIMARY KEY (classification_id, entity_id)
);

-- ══════════════════════════════════════════
-- VECTOR EMBEDDINGS (pgvector)
-- ══════════════════════════════════════════

CREATE TABLE content_embeddings (
    url_id          UUID PRIMARY KEY REFERENCES urls(id),
    embedding       vector(768) NOT NULL,
    model_version   VARCHAR(50) NOT NULL DEFAULT 'BiomedBERT-base-v1',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embeddings_hnsw ON content_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- ══════════════════════════════════════════
-- DRUG SYNONYMS
-- ══════════════════════════════════════════

CREATE TABLE drug_synonyms (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rxnorm_cui      VARCHAR(20) NOT NULL,
    synonym         TEXT NOT NULL,
    synonym_type    VARCHAR(20),
    source          VARCHAR(30),
    UNIQUE(rxnorm_cui, synonym)
);

CREATE INDEX idx_drug_synonyms_name ON drug_synonyms USING gin (synonym gin_trgm_ops);
CREATE INDEX idx_drug_synonyms_cui ON drug_synonyms(rxnorm_cui);

-- ══════════════════════════════════════════
-- ADVERTISER FEEDBACK
-- ══════════════════════════════════════════

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
    action_taken        TEXT
);

CREATE INDEX idx_feedback_url ON advertiser_feedback(url_id);
CREATE INDEX idx_feedback_unprocessed ON advertiser_feedback(processed) WHERE processed = FALSE;

-- ══════════════════════════════════════════
-- AUDIT LOG (immutable)
-- ══════════════════════════════════════════

CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,
    entity_type     VARCHAR(30),
    entity_id       UUID,
    actor           VARCHAR(100),
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_time ON audit_log(created_at);

-- ══════════════════════════════════════════
-- SCRAPE SCHEDULE
-- ══════════════════════════════════════════

CREATE TABLE scrape_schedule (
    url_id          UUID PRIMARY KEY REFERENCES urls(id),
    next_scrape_at  TIMESTAMPTZ NOT NULL,
    scrape_interval INTERVAL NOT NULL DEFAULT '30 days',
    priority        SMALLINT DEFAULT 5,
    consecutive_failures SMALLINT DEFAULT 0,
    last_change_detected BOOLEAN
);

CREATE INDEX idx_scrape_schedule_next ON scrape_schedule(next_scrape_at);

-- ══════════════════════════════════════════
-- TAXONOMY REFERENCE TABLES
-- ══════════════════════════════════════════

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
