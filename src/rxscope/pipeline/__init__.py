"""RxScope pipeline state — shared TypedDict passed between all LangGraph agents."""

from __future__ import annotations

from typing import Literal, TypedDict


class RxScopeState(TypedDict, total=False):
    # ── Input ──
    url: str
    raw_html: str
    source_platform: Literal["scribd", "slideshare", "pubmed", "other"]

    # ── Extractor output ──
    clean_text: str
    title: str
    author: str
    author_credentials: str | None
    document_type: str
    language: str
    word_count: int
    metadata: dict

    # ── Dedup output ──
    content_hash: str
    is_duplicate: bool
    duplicate_of_url: str | None
    embedding: list[float]

    # ── Classifier output ──
    mesh_codes: list[str]
    iab_categories: list[str]
    hcp_signal: float
    content_source_type: Literal[
        "pharma_manufacturer",
        "medical_school",
        "trade_association",
        "recognized_physician",
        "healthcare_executive",
        "biotech",
        "device_manufacturer",
        "medical_institution",
        "unknown",
    ]
    detected_entities: list[dict]

    # ── Entity Resolver output ──
    resolved_drugs: list[dict]
    verified_physicians: list[dict]
    verified_organizations: list[dict]
    icd10_codes: list[str]
    snomed_codes: list[str]

    # ── Confidence Scorer output ──
    overall_confidence: float
    component_scores: dict
    classification_tier: Literal["auto_approve", "opus_review", "human_review"]

    # ── Validator / Review output ──
    is_approved: bool
    review_notes: str | None
    reviewer: str | None

    # ── Final ──
    whitelist_entry: dict | None
    processing_timestamp: str
    pipeline_version: str
