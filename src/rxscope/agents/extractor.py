"""Extractor agent — pulls clean text, metadata, and author info from raw HTML."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import structlog
from bs4 import BeautifulSoup

from rxscope.pipeline import RxScopeState

log = structlog.get_logger()


def _detect_document_type(url: str, soup: BeautifulSoup) -> str:
    """Heuristic document-type detection based on URL and page structure."""
    url_lower = url.lower()
    if url_lower.endswith(".pdf") or "/pdf/" in url_lower:
        return "pdf"
    if "slideshare" in url_lower or "/slideshow/" in url_lower:
        return "slide_deck"
    if "pubmed" in url_lower or "ncbi.nlm.nih.gov" in url_lower:
        return "research_article"
    # Check meta tags
    og_type = soup.find("meta", property="og:type")
    if og_type and "article" in (og_type.get("content", "") or "").lower():
        return "article"
    return "html_page"


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract clean body text, stripping nav/footer/script/style."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _extract_meta(soup: BeautifulSoup) -> dict:
    """Pull Open Graph and standard meta tags."""
    meta: dict = {}
    for prop in ("og:title", "og:description", "og:type", "og:site_name", "article:author"):
        tag = soup.find("meta", property=prop)
        if tag:
            meta[prop] = tag.get("content", "")
    for name in ("author", "description", "keywords"):
        tag = soup.find("meta", attrs={"name": name})
        if tag:
            meta[name] = tag.get("content", "")
    return meta


def extractor_agent(state: RxScopeState) -> dict:
    """Extract structured content from raw HTML."""
    url = state["url"]
    raw_html = state.get("raw_html", "")

    log.info("extractor.start", url=url, html_len=len(raw_html))

    soup = BeautifulSoup(raw_html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    clean_text = _extract_text(soup)
    word_count = len(clean_text.split())
    metadata = _extract_meta(soup)
    doc_type = _detect_document_type(url, soup)

    # Author extraction
    author = metadata.get("author") or metadata.get("article:author", "")

    # Content hash for exact dedup
    content_hash = hashlib.sha256(clean_text.encode()).hexdigest()

    # TODO: detect language with fasttext
    language = "en"

    # Simple duplicate check placeholder — real implementation queries DB
    is_duplicate = False

    log.info("extractor.done", url=url, words=word_count, doc_type=doc_type)

    return {
        "clean_text": clean_text,
        "title": title,
        "author": author,
        "author_credentials": None,
        "document_type": doc_type,
        "language": language,
        "word_count": word_count,
        "metadata": metadata,
        "content_hash": content_hash,
        "is_duplicate": is_duplicate,
        "duplicate_of_url": None,
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "0.1.0",
    }
