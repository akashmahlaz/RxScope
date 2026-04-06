"""DB Writer agent — persists classification results to PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from rxscope.pipeline import RxScopeState

log = structlog.get_logger()


def db_writer_agent(state: RxScopeState) -> dict:
    """Write classification results to PostgreSQL.

    This is a placeholder that logs what would be written.
    Real implementation will use psycopg3 connection pool.
    """
    url = state.get("url", "")
    is_dup = state.get("is_duplicate", False)
    is_approved = state.get("is_approved", False)
    confidence = state.get("overall_confidence", 0.0)
    tier = state.get("classification_tier", "unknown")

    if is_dup:
        log.info("db_writer.skip_duplicate", url=url, duplicate_of=state.get("duplicate_of_url"))
        return {"whitelist_entry": None}

    whitelist_entry = None
    if is_approved and confidence >= 0.7:
        whitelist_entry = {
            "url": url,
            "source_domain": url.split("/")[2] if "/" in url else "",
            "content_type": state.get("document_type", ""),
            "detected_medical_categories": "; ".join(
                state.get("mesh_codes", []) + state.get("iab_categories", [])
            ),
            "detected_entity_associations": "; ".join(
                [d.get("name", "") for d in state.get("resolved_drugs", [])]
                + [p.get("name", "") for p in state.get("verified_physicians", [])]
                + [o.get("name", "") for o in state.get("verified_organizations", [])]
            ),
            "confidence_score": confidence,
        }

    log.info(
        "db_writer.done",
        url=url,
        approved=is_approved,
        on_whitelist=whitelist_entry is not None,
        tier=tier,
    )

    # TODO: actual DB writes — INSERT INTO classifications, entities, taxonomy_tags, audit_log
    return {"whitelist_entry": whitelist_entry}
