"""Lightpanda / Puppeteer-based scraper using CDP protocol."""

from __future__ import annotations

import structlog
import httpx

from rxscope.config import settings

log = structlog.get_logger()


async def scrape_url(url: str) -> dict:
    """Scrape a URL and return raw HTML + status.

    In production this connects to Lightpanda via CDP (WebSocket on port 9222).
    For Phase 0 / testing, we use plain httpx as a simple fallback.
    """
    log.info("scraper.fetch", url=url)

    headers = {"User-Agent": settings.scrape_user_agent}

    if settings.proxy_url:
        transport = httpx.AsyncHTTPTransport(proxy=settings.proxy_url)
        client = httpx.AsyncClient(transport=transport, headers=headers, follow_redirects=True, timeout=30)
    else:
        client = httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30)

    try:
        async with client:
            resp = await client.get(url)
            log.info("scraper.done", url=url, status=resp.status_code, size=len(resp.text))
            return {
                "raw_html": resp.text,
                "http_status": resp.status_code,
                "headers": dict(resp.headers),
            }
    except httpx.HTTPError as exc:
        log.error("scraper.error", url=url, error=str(exc))
        return {
            "raw_html": "",
            "http_status": 0,
            "headers": {},
        }
