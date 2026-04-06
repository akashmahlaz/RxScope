# RxScope
## AI-Based Medical Content Identification System

Production-grade AI pipeline for classifying medically relevant, HCP-oriented content across document-hosting platforms, producing pharma ad-targeting whitelists.

### Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Copy environment config
cp .env.example .env
# Edit .env with your credentials

# 3. Run database migrations
rxscope db migrate

# 4. Process URLs
rxscope pipeline run --input urls.txt

# 5. Export whitelist
rxscope export --format xlsx --output whitelist.xlsx
```

### Project Structure

```
src/rxscope/
├── agents/          # LangGraph agent implementations
│   ├── extractor.py     # Content extraction from HTML/PDF/PPT
│   ├── classifier.py    # Claude + scispaCy classification
│   ├── entity_resolver.py  # NPI, RxNorm, FDA verification
│   ├── confidence.py    # Ensemble confidence scoring
│   └── db_writer.py     # PostgreSQL write + audit
├── db/              # Database layer
│   ├── schema.sql       # Full DDL
│   ├── connection.py    # Connection pool management
│   └── queries.py       # Typed query functions
├── pipeline/        # LangGraph pipeline orchestration
│   ├── state.py         # RxScopeState definition
│   └── graph.py         # StateGraph wiring
├── scraper/         # Web scraping layer
│   └── lightpanda.py    # Lightpanda CDP integration
├── export/          # Whitelist export
│   └── whitelist.py     # CSV/XLSX export per client spec
├── config.py        # Pydantic settings
└── cli.py           # Click CLI entry point
```

### Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full pre-build architecture document.
