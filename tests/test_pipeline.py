"""Basic tests for the RxScope pipeline."""

from rxscope.pipeline import RxScopeState
from rxscope.agents.extractor import extractor_agent
from rxscope.agents.confidence import confidence_scorer_agent


SAMPLE_HTML = """
<html>
<head><title>Phase 3 Clinical Trial Results for Dupixent</title>
<meta name="author" content="Dr. Sarah Chen, MD">
<meta property="og:description" content="Results from a randomized controlled trial">
</head>
<body>
<h1>Phase 3 Clinical Trial Results for Dupixent (dupilumab)</h1>
<p>This multicenter, double-blind, placebo-controlled study evaluated the efficacy
and safety of dupilumab in adults with moderate-to-severe atopic dermatitis.</p>
<p>Primary endpoint: IGA 0/1 response at Week 16. Results showed statistically
significant improvement (p<0.001) vs placebo. Adverse events were consistent
with the known safety profile.</p>
<p>Author: Dr. Sarah Chen, MD, Department of Dermatology, Johns Hopkins University</p>
</body>
</html>
"""


def test_extractor_produces_required_fields():
    state: RxScopeState = {
        "url": "https://example.com/clinical-trial",
        "raw_html": SAMPLE_HTML,
        "source_platform": "other",
    }
    result = extractor_agent(state)
    assert result["clean_text"]
    assert result["title"] == "Phase 3 Clinical Trial Results for Dupixent"
    assert result["author"] == "Dr. Sarah Chen, MD"
    assert result["word_count"] > 0
    assert result["content_hash"]
    assert result["pipeline_version"] == "0.1.0"
    assert result["is_duplicate"] is False


def test_confidence_scorer_routing():
    state: RxScopeState = {
        "url": "https://example.com/clinical-trial",
        "hcp_signal": 0.95,
        "detected_entities": [
            {"text": "dupilumab", "type": "drug"},
            {"text": "Dr. Sarah Chen", "type": "physician"},
        ],
        "resolved_drugs": [{"name": "dupilumab", "rxnorm_cui": "1876366"}],
        "verified_physicians": [{"npi": "1234567890", "name": "Sarah Chen"}],
        "verified_organizations": [],
        "mesh_codes": ["C17.800.174"],
        "iab_categories": ["IAB7-18"],
        "word_count": 200,
    }
    result = confidence_scorer_agent(state)
    assert 0 <= result["overall_confidence"] <= 1
    assert result["classification_tier"] in ("auto_approve", "opus_review", "human_review")
    # With high hcp_signal + verified entities, should be high confidence
    assert result["overall_confidence"] >= 0.6


def test_confidence_scorer_low_signal():
    state: RxScopeState = {
        "url": "https://example.com/blog-post",
        "hcp_signal": 0.1,
        "detected_entities": [],
        "resolved_drugs": [],
        "verified_physicians": [],
        "verified_organizations": [],
        "mesh_codes": [],
        "iab_categories": [],
        "word_count": 50,
    }
    result = confidence_scorer_agent(state)
    assert result["overall_confidence"] < 0.6
    assert result["classification_tier"] == "human_review"
