"""Classifier agent — MiniMax M2.7 (Anthropic-compatible) for medical content classification."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from rxscope.config import settings
from rxscope.pipeline import RxScopeState

log = structlog.get_logger()

SYSTEM_PROMPT = """\
You are a medical content classification system for pharmaceutical ad-tech.
Your job is to analyze a document and determine:

1. Whether this content is oriented toward Healthcare Professionals (HCP) vs consumers.
2. What medical subject headings (MeSH codes) apply.
3. What IAB 3.1 content categories apply.
4. What type of source produced this content.

Respond in this exact JSON format (no markdown, no extra text):
{
  "hcp_signal": <float 0-1, probability content targets HCPs>,
  "mesh_codes": ["<MeSH tree number>", ...],
  "iab_categories": ["<IAB 3.1 code>", ...],
  "content_source_type": "<one of: pharma_manufacturer, medical_school, trade_association, recognized_physician, healthcare_executive, biotech, device_manufacturer, medical_institution, unknown>",
  "detected_entities": [
    {"text": "<entity text>", "type": "<drug|physician|organization|disease|procedure|device>"}
  ],
  "reasoning": "<brief explanation of classification>"
}
"""


def _build_classification_prompt(state: RxScopeState) -> str:
    """Construct the classification prompt with document context."""
    text = state.get("clean_text", "")
    # Truncate to ~3000 tokens (~12,000 chars) to control cost
    if len(text) > 12000:
        text = text[:12000] + "\n\n[TRUNCATED — full document is longer]"

    return (
        f"URL: {state.get('url', 'unknown')}\n"
        f"Title: {state.get('title', 'unknown')}\n"
        f"Author: {state.get('author', 'unknown')}\n"
        f"Document Type: {state.get('document_type', 'unknown')}\n"
        f"\n--- DOCUMENT TEXT ---\n{text}"
    )


def classifier_agent(state: RxScopeState) -> dict:
    """Classify medical content using Claude Sonnet + structured output."""
    url = state.get("url", "")
    log.info("classifier.start", url=url)

    if not settings.minimax_api_key:
        log.warning("classifier.no_api_key", msg="Returning placeholder classification")
        return {
            "mesh_codes": [],
            "iab_categories": [],
            "hcp_signal": 0.0,
            "content_source_type": "unknown",
            "detected_entities": [],
        }

    llm = ChatAnthropic(
        model=settings.minimax_model,
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
        max_tokens=2048,
        temperature=0,
    )

    prompt = _build_classification_prompt(state)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # MiniMax M2.7 returns content blocks (thinking + text) via Anthropic SDK.
    # Extract the text block containing the JSON.
    import json

    raw = response.content
    text_content = ""
    if isinstance(raw, list):
        # Content blocks: [{"type": "thinking", ...}, {"type": "text", "text": "..."}]
        for block in raw:
            if hasattr(block, "type") and block.type == "text":
                text_content = block.text
                break
            elif isinstance(block, dict) and block.get("type") == "text":
                text_content = block.get("text", "")
                break
        if not text_content:
            # Fallback: grab any string from blocks
            for block in raw:
                t = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
                if t:
                    text_content = t
                    break
    elif isinstance(raw, str):
        text_content = raw

    # Strip markdown fences if model wraps in ```json ... ```
    text_content = text_content.strip()
    if text_content.startswith("```"):
        text_content = text_content.split("\n", 1)[-1]
    if text_content.endswith("```"):
        text_content = text_content.rsplit("```", 1)[0]
    text_content = text_content.strip()

    try:
        result = json.loads(text_content)
    except (json.JSONDecodeError, TypeError):
        log.error("classifier.parse_error", url=url, raw=str(response.content)[:500])
        return {
            "mesh_codes": [],
            "iab_categories": [],
            "hcp_signal": 0.0,
            "content_source_type": "unknown",
            "detected_entities": [],
        }

    log.info(
        "classifier.done",
        url=url,
        hcp_signal=result.get("hcp_signal"),
        source_type=result.get("content_source_type"),
        entity_count=len(result.get("detected_entities", [])),
    )

    return {
        "mesh_codes": result.get("mesh_codes", []),
        "iab_categories": result.get("iab_categories", []),
        "hcp_signal": float(result.get("hcp_signal", 0.0)),
        "content_source_type": result.get("content_source_type", "unknown"),
        "detected_entities": result.get("detected_entities", []),
    }
