"""DB Writer agent — persists classification results to PostgreSQL."""

from __future__ import annotations

import structlog

from rxscope.pipeline import RxScopeState

log = structlog.get_logger()

_PIPELINE_VERSION = "0.1.0"


def db_writer_agent(state: RxScopeState) -> dict:
    """Write classification results to PostgreSQL."""
    from rxscope.db.queries import insert_classification, mark_scraped, upsert_url

    url = state.get("url", "")
    is_dup = state.get("is_duplicate", False)
    confidence = state.get("overall_confidence", 0.0)
    tier = state.get("classification_tier", "unknown")
    hcp_signal = state.get("hcp_signal", 0.0)

    if is_dup:
        log.info("db_writer.skip_duplicate", url=url, duplicate_of=state.get("duplicate_of_url"))
        return {"whitelist_entry": None}

    try:
        # 1. Upsert the URL
        platform = state.get("source_platform", "unknown")
        url_id = upsert_url(url, platform)

        # 2. Mark as scraped
        content_hash = (state.get("content_hash") or "").encode("utf-8")
        mark_scraped(
            url_id,
            http_status=200,
            content_hash=content_hash,
            title=state.get("title", ""),
            word_count=len((state.get("clean_text") or "").split()),
        )

        # 3. Insert classification
        is_hcp = hcp_signal >= 0.5
        source_type = state.get("content_source_type", "unknown")
        drugs = state.get("resolved_drugs", [])
        physicians = state.get("verified_physicians", [])
        orgs = state.get("verified_organizations", [])
        attribution = "; ".join(
            [d.get("name", "") for d in drugs]
            + [p.get("name", "") for p in physicians]
            + [o.get("name", "") for o in orgs]
        )
        component_scores = state.get("component_scores", {})

        classification_id = insert_classification(
            url_id=url_id,
            pipeline_version=_PIPELINE_VERSION,
            is_hcp=is_hcp,
            hcp_confidence=hcp_signal,
            overall_confidence=confidence,
            source_type=source_type,
            attribution_entity=attribution,
            component_scores=component_scores,
            classification_tier=tier,
        )

        log.info("db_writer.persisted", url=url, url_id=url_id, classification_id=classification_id)
    except Exception as exc:
        log.error("db_writer.persist_failed", url=url, error=str(exc))

    # Build whitelist entry if approved
    whitelist_entry = None
    is_approved = state.get("is_approved", False)
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

    return {"whitelist_entry": whitelist_entry}
