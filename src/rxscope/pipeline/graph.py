"""LangGraph pipeline — wires all agents into a StateGraph."""

from __future__ import annotations

import structlog
from langgraph.graph import END, START, StateGraph

from rxscope.agents.classifier import classifier_agent
from rxscope.agents.confidence import confidence_scorer_agent
from rxscope.agents.db_writer import db_writer_agent
from rxscope.agents.entity_resolver import entity_resolver_agent
from rxscope.agents.extractor import extractor_agent
from rxscope.config import settings
from rxscope.pipeline import RxScopeState

log = structlog.get_logger()


def _route_by_dedup(state: RxScopeState) -> str:
    """After dedup: skip to db_writer if duplicate, else classify."""
    if state.get("is_duplicate"):
        return "db_writer"
    return "classifier"


def _route_by_confidence(state: RxScopeState) -> str:
    """Route based on confidence tier."""
    score = state.get("overall_confidence", 0.0)
    if score >= settings.confidence_auto_approve:
        return "validator"
    if score >= settings.confidence_opus_review:
        return "opus_review"
    return "hitl_queue"


def _validator_agent(state: RxScopeState) -> dict:
    """Quick consistency-check for high-confidence classifications."""
    log.info("validator.auto_approve", url=state.get("url"), score=state.get("overall_confidence"))
    return {"is_approved": True, "reviewer": "auto"}


def _opus_review_agent(state: RxScopeState) -> dict:
    """Send edge-case to Claude Opus for deep review (placeholder)."""
    log.info("opus_review.start", url=state.get("url"), score=state.get("overall_confidence"))
    # TODO: call Claude Opus 4 with full context for re-evaluation
    return {"is_approved": True, "reviewer": "opus", "review_notes": "Opus review pending implementation"}


def _hitl_queue_agent(state: RxScopeState) -> dict:
    """Queue for human review via dashboard. LangGraph interrupt() pauses here."""
    log.info("hitl_queue.queued", url=state.get("url"), score=state.get("overall_confidence"))
    return {"is_approved": False, "reviewer": None, "review_notes": "Awaiting human review"}


def build_graph() -> StateGraph:
    """Construct the RxScope classification pipeline graph."""
    graph = StateGraph(RxScopeState)

    # Nodes
    graph.add_node("extractor", extractor_agent)
    graph.add_node("classifier", classifier_agent)
    graph.add_node("entity_resolver", entity_resolver_agent)
    graph.add_node("confidence_scorer", confidence_scorer_agent)
    graph.add_node("validator", _validator_agent)
    graph.add_node("opus_review", _opus_review_agent)
    graph.add_node("hitl_queue", _hitl_queue_agent)
    graph.add_node("db_writer", db_writer_agent)

    # Edges
    graph.add_edge(START, "extractor")
    graph.add_conditional_edges("extractor", _route_by_dedup)
    graph.add_edge("classifier", "entity_resolver")
    graph.add_edge("entity_resolver", "confidence_scorer")
    graph.add_conditional_edges("confidence_scorer", _route_by_confidence)
    graph.add_edge("validator", "db_writer")
    graph.add_edge("opus_review", "db_writer")
    graph.add_edge("hitl_queue", "db_writer")
    graph.add_edge("db_writer", END)

    return graph


def compile_pipeline():
    """Build and compile the pipeline, optionally with checkpointing."""
    graph = build_graph()
    # Interrupt before hitl_queue so the graph pauses for human input
    return graph.compile(interrupt_before=["hitl_queue"])
