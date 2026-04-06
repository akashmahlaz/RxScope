"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/rxscope"
    database_pool_size: int = 10

    # Anthropic
    anthropic_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "rxscope"
    langsmith_tracing: bool = True

    # Medical APIs
    umls_api_key: str = ""
    npi_api_base: str = "https://npiregistry.cms.hhs.gov/api"
    rxnorm_api_base: str = "https://rxnav.nlm.nih.gov/REST"
    openfda_api_base: str = "https://api.fda.gov"

    # Scraping
    lightpanda_ws: str = "ws://127.0.0.1:9222"
    proxy_url: str = ""
    scrape_rate_limit: float = 2.0
    scrape_user_agent: str = "RxScopeBot/1.0 (+https://rxnetwork.com/bot)"

    # Cloudflare R2
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "rxscope-content"

    # Application
    log_level: str = "INFO"
    confidence_auto_approve: float = 0.80
    confidence_opus_review: float = 0.60
    export_format: str = "xlsx"


settings = Settings()
