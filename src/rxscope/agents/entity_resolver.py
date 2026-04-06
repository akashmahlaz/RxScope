"""Entity Resolver agent — verifies drugs, physicians, organizations against federal APIs."""

from __future__ import annotations

import structlog
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from rxscope.config import settings
from rxscope.pipeline import RxScopeState

log = structlog.get_logger()

_HTTP_TIMEOUT = 15.0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _query_npi(first_name: str, last_name: str) -> list[dict]:
    """Query the CMS NPI Registry for physician verification."""
    params = {"version": "2.1", "first_name": first_name, "last_name": last_name, "limit": 5}
    resp = httpx.get(f"{settings.npi_api_base}/", params=params, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return [
        {
            "npi": r.get("number"),
            "name": f"{first_name} {last_name}",
            "specialty": (r.get("taxonomies", [{}])[0].get("desc", "") if r.get("taxonomies") else ""),
            "org": (
                r.get("basic", {}).get("organization_name", "")
                or f"{r.get('basic', {}).get('first_name', '')} {r.get('basic', {}).get('last_name', '')}"
            ),
        }
        for r in results
    ]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _query_rxnorm(drug_name: str) -> dict | None:
    """Query RxNorm for drug name resolution."""
    params = {"name": drug_name, "search": 1}
    resp = httpx.get(f"{settings.rxnorm_api_base}/rxcui.json", params=params, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    id_group = data.get("idGroup", {})
    rxnorm_ids = id_group.get("rxnormId", [])
    if not rxnorm_ids:
        return None
    return {
        "name": drug_name,
        "rxnorm_cui": rxnorm_ids[0],
        "brand_names": [],
        "generic_name": drug_name,
    }


def entity_resolver_agent(state: RxScopeState) -> dict:
    """Resolve detected entities against NPI, RxNorm, and curated lists."""
    url = state.get("url", "")
    entities = state.get("detected_entities", [])
    log.info("entity_resolver.start", url=url, entity_count=len(entities))

    resolved_drugs: list[dict] = []
    verified_physicians: list[dict] = []
    verified_organizations: list[dict] = []
    icd10_codes: list[str] = []

    for entity in entities:
        etype = entity.get("type", "")
        text = entity.get("text", "")

        if etype == "drug":
            try:
                result = _query_rxnorm(text)
                if result:
                    resolved_drugs.append(result)
            except Exception:
                log.warning("entity_resolver.rxnorm_fail", drug=text)

        elif etype == "physician":
            parts = text.strip().split()
            if len(parts) >= 2:
                try:
                    results = _query_npi(parts[0], parts[-1])
                    if results:
                        verified_physicians.append(results[0])
                except Exception:
                    log.warning("entity_resolver.npi_fail", name=text)

        elif etype == "organization":
            # Placeholder — will check against curated org database
            verified_organizations.append({"name": text, "type": "unverified", "verified_source": None})

    log.info(
        "entity_resolver.done",
        url=url,
        drugs=len(resolved_drugs),
        physicians=len(verified_physicians),
        orgs=len(verified_organizations),
    )

    return {
        "resolved_drugs": resolved_drugs,
        "verified_physicians": verified_physicians,
        "verified_organizations": verified_organizations,
        "icd10_codes": icd10_codes,
        "snomed_codes": [],
    }
