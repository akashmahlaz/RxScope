"""Confidence Scorer agent — ensemble scoring from all upstream signals."""

from __future__ import annotations

import structlog

from rxscope.config import settings
from rxscope.pipeline import RxScopeState

log = structlog.get_logger()

# Weights per architecture doc Section 5 Step 8
WEIGHTS = {
    "hcp_signal": 0.30,
    "entity_resolution": 0.25,
    "source_verification": 0.20,
    "medical_density": 0.15,
    "taxonomy_coherence": 0.10,
}


def confidence_scorer_agent(state: RxScopeState) -> dict:
    """Compute a weighted ensemble confidence score."""
    url = state.get("url", "")
    log.info("confidence_scorer.start", url=url)

    # ── Component scores ──
    hcp_signal = state.get("hcp_signal", 0.0)

    # Entity resolution rate
    total_entities = len(state.get("detected_entities", []))
    resolved = len(state.get("resolved_drugs", [])) + len(state.get("verified_physicians", []))
    entity_resolution = (resolved / total_entities) if total_entities > 0 else 0.0

    # Source verification
    source_verified = any(
        p.get("npi") for p in state.get("verified_physicians", [])
    ) or any(
        o.get("verified_source") for o in state.get("verified_organizations", [])
    )
    source_verification = 1.0 if source_verified else 0.3

    # Medical density (entities per 100 words)
    word_count = state.get("word_count", 1)
    medical_density = min(1.0, (total_entities / max(word_count, 1)) * 100 * 2)

    # Taxonomy coherence — do we have both MeSH and IAB codes?
    has_mesh = len(state.get("mesh_codes", [])) > 0
    has_iab = len(state.get("iab_categories", [])) > 0
    taxonomy_coherence = 1.0 if (has_mesh and has_iab) else 0.5 if (has_mesh or has_iab) else 0.0

    component_scores = {
        "hcp_signal": round(hcp_signal, 4),
        "entity_resolution": round(entity_resolution, 4),
        "source_verification": round(source_verification, 4),
        "medical_density": round(medical_density, 4),
        "taxonomy_coherence": round(taxonomy_coherence, 4),
    }

    # Weighted ensemble
    overall = sum(WEIGHTS[k] * component_scores[k] for k in WEIGHTS)
    overall = round(min(1.0, max(0.0, overall)), 4)

    # Tier routing
    if overall >= settings.confidence_auto_approve:
        tier = "auto_approve"
    elif overall >= settings.confidence_opus_review:
        tier = "opus_review"
    else:
        tier = "human_review"

    log.info("confidence_scorer.done", url=url, overall=overall, tier=tier, components=component_scores)

    return {
        "overall_confidence": overall,
        "component_scores": component_scores,
        "classification_tier": tier,
    }
