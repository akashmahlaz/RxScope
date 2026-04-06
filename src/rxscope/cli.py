"""RxScope CLI — entry point for all commands."""

from __future__ import annotations

import asyncio
import sys

import click
import structlog

from rxscope.config import settings

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()


@click.group()
def main():
    """RxScope — AI-Based Medical Content Identification System."""
    pass


# ── Database commands ──


@main.group()
def db():
    """Database management commands."""
    pass


@db.command()
def migrate():
    """Apply database schema to PostgreSQL."""
    from rxscope.db import run_schema

    log.info("db.migrate.start")
    try:
        run_schema()
        log.info("db.migrate.done")
    except Exception as exc:
        log.error("db.migrate.failed", error=str(exc))
        sys.exit(1)


# ── Pipeline commands ──


@main.group()
def pipeline():
    """Classification pipeline commands."""
    pass


@pipeline.command()
@click.option("--url", required=True, help="Single URL to classify")
def run(url: str):
    """Run the classification pipeline on a single URL."""
    asyncio.run(_run_single(url))


async def _run_single(url: str):
    """Scrape and classify a single URL."""
    from rxscope.scraper import scrape_url
    from rxscope.pipeline.graph import compile_pipeline

    log.info("pipeline.start", url=url)

    # 1. Scrape
    result = await scrape_url(url)
    if not result["raw_html"]:
        log.error("pipeline.scrape_failed", url=url)
        return

    # 2. Run through LangGraph pipeline
    app = compile_pipeline()
    initial_state = {
        "url": url,
        "raw_html": result["raw_html"],
        "source_platform": _detect_platform(url),
    }

    final_state = app.invoke(initial_state)

    # 3. Output result
    entry = final_state.get("whitelist_entry")
    if entry:
        log.info("pipeline.whitelist_entry", **entry)
    else:
        log.info("pipeline.no_whitelist_entry", url=url, confidence=final_state.get("overall_confidence"))


@pipeline.command("run-batch")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="File with one URL per line")
@click.option("--output", "output_file", default="whitelist.xlsx", help="Output file path")
@click.option("--format", "fmt", type=click.Choice(["xlsx", "csv"]), default="xlsx")
def run_batch(input_file: str, output_file: str, fmt: str):
    """Run pipeline on a batch of URLs and export whitelist."""
    asyncio.run(_run_batch(input_file, output_file, fmt))


async def _run_batch(input_file: str, output_file: str, fmt: str):
    """Process a batch of URLs."""
    from pathlib import Path

    from rxscope.export import export_whitelist
    from rxscope.pipeline.graph import compile_pipeline
    from rxscope.scraper import scrape_url

    urls = Path(input_file).read_text().strip().splitlines()
    urls = [u.strip() for u in urls if u.strip() and not u.startswith("#")]

    log.info("pipeline.batch.start", url_count=len(urls))

    app = compile_pipeline()
    whitelist_entries: list[dict] = []

    for i, url in enumerate(urls, 1):
        log.info("pipeline.batch.progress", current=i, total=len(urls), url=url)
        try:
            result = await scrape_url(url)
            if not result["raw_html"]:
                continue

            final_state = app.invoke({
                "url": url,
                "raw_html": result["raw_html"],
                "source_platform": _detect_platform(url),
            })

            entry = final_state.get("whitelist_entry")
            if entry:
                whitelist_entries.append(entry)
        except Exception as exc:
            log.error("pipeline.batch.url_error", url=url, error=str(exc))

    log.info("pipeline.batch.done", processed=len(urls), whitelist_count=len(whitelist_entries))

    if whitelist_entries:
        export_whitelist(whitelist_entries, output_file, fmt)


# ── Export commands ──


@main.command()
@click.option("--format", "fmt", type=click.Choice(["xlsx", "csv"]), default="xlsx")
@click.option("--output", default="whitelist.xlsx", help="Output file path")
@click.option("--min-confidence", default=0.7, type=float, help="Minimum confidence threshold")
def export(fmt: str, output: str, min_confidence: float):
    """Export the current whitelist from the database."""
    from rxscope.db.queries import get_whitelist_entries
    from rxscope.export import export_whitelist

    entries = get_whitelist_entries(min_confidence=min_confidence)
    log.info("export.from_db", entries=len(entries))
    if entries:
        export_whitelist(entries, output, fmt)
    else:
        log.warning("export.empty", msg="No whitelist entries found above threshold")


# ── Helpers ──


def _detect_platform(url: str) -> str:
    """Detect source platform from URL domain."""
    url_lower = url.lower()
    if "scribd.com" in url_lower:
        return "scribd"
    if "slideshare" in url_lower:
        return "slideshare"
    if "pubmed" in url_lower or "ncbi.nlm.nih.gov" in url_lower:
        return "pubmed"
    return "other"


if __name__ == "__main__":
    main()
