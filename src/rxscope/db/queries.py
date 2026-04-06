"""Typed query functions for RxScope database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from rxscope.db import get_connection


def upsert_url(url: str, platform: str) -> str:
    """Insert a URL or return existing ID."""
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO urls (url, platform)
            VALUES (%s, %s)
            ON CONFLICT (url) DO UPDATE SET updated_at = NOW()
            RETURNING id
            """,
            (url, platform),
        ).fetchone()
        conn.commit()
        return str(row[0])


def mark_scraped(url_id: str, http_status: int, content_hash: bytes, title: str, word_count: int):
    """Update URL after successful scrape."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE urls SET
                scrape_status = 'scraped',
                last_scraped_at = NOW(),
                http_status = %s,
                content_hash = %s,
                title = %s,
                word_count = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (http_status, content_hash, title, word_count, url_id),
        )
        conn.commit()


def insert_classification(
    url_id: str,
    pipeline_version: str,
    is_hcp: bool,
    hcp_confidence: float,
    overall_confidence: float,
    source_type: str,
    attribution_entity: str,
    component_scores: dict,
    classification_tier: str,
) -> str:
    """Insert a new classification record, marking previous as non-current."""
    import json

    with get_connection() as conn:
        # Mark old classifications as non-current
        conn.execute(
            "UPDATE classifications SET is_current = FALSE WHERE url_id = %s AND is_current = TRUE",
            (url_id,),
        )
        row = conn.execute(
            """
            INSERT INTO classifications (
                url_id, pipeline_version, is_hcp_content, hcp_confidence,
                overall_confidence, source_type, attribution_entity,
                component_scores, classification_tier
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                url_id,
                pipeline_version,
                is_hcp,
                hcp_confidence,
                overall_confidence,
                source_type,
                attribution_entity,
                json.dumps(component_scores),
                classification_tier,
            ),
        ).fetchone()
        conn.commit()
        return str(row[0])


def get_whitelist_entries(min_confidence: float = 0.7, limit: int = 10000) -> list[dict]:
    """Fetch current whitelist entries for export."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                u.url,
                split_part(u.url, '/', 3) AS source_domain,
                u.document_type AS content_type,
                string_agg(DISTINCT t.code, '; ')
                    FILTER (WHERE t.taxonomy_system IN ('mesh', 'iab'))
                    AS detected_medical_categories,
                c.attribution_entity AS detected_entity_associations,
                c.overall_confidence AS confidence_score,
                c.audience_type,
                c.source_type
            FROM urls u
            JOIN classifications c ON c.url_id = u.id AND c.is_current = TRUE AND c.on_whitelist = TRUE
            LEFT JOIN classification_taxonomy_tags t ON t.classification_id = c.id
            WHERE c.overall_confidence >= %s
            GROUP BY u.id, u.url, u.document_type,
                     c.attribution_entity, c.overall_confidence,
                     c.audience_type, c.source_type, c.id
            ORDER BY c.overall_confidence DESC
            LIMIT %s
            """,
            (min_confidence, limit),
        ).fetchall()

        columns = [
            "url", "source_domain", "content_type",
            "detected_medical_categories", "detected_entity_associations",
            "confidence_score", "audience_type", "source_type",
        ]
        return [dict(zip(columns, row)) for row in rows]


def get_pending_reviews(limit: int = 50) -> list[dict]:
    """Fetch URLs pending human review."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT u.url, c.overall_confidence, c.component_scores, c.source_type, c.id
            FROM classifications c
            JOIN urls u ON u.id = c.url_id
            WHERE c.review_status = 'pending' AND c.classification_tier = 'human_review'
            ORDER BY c.overall_confidence DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "url": r[0],
                "confidence": r[1],
                "component_scores": r[2],
                "source_type": r[3],
                "classification_id": str(r[4]),
            }
            for r in rows
        ]
