from decimal import Decimal
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every setting comes from an environment variable of the same name (case-insensitive).

    The repo-root .env is read when running outside Docker; real environment variables win.
    """

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"

    # Sign-in (Keycloak). Tokens must come from this issuer and name this audience.
    auth_issuer: str = "http://localhost:8080/realms/app"
    auth_audience: str = "api"
    # Where to fetch the signing keys; defaults to the issuer's. Inside Docker the issuer's public
    # address is not reachable, so compose.yaml points this at http://keycloak:8080.
    auth_jwks_url: str | None = None

    # Any OpenAI-compatible endpoint: Azure AI Foundry, OpenAI, OpenRouter, Ollama, LM Studio...
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: SecretStr | None = None
    # Second account, used when the first one fails with auth, quota, throttling or outage errors.
    ai_fallback_base_url: str | None = None
    ai_fallback_api_key: SecretStr | None = None

    # On Azure these are deployment names, so keep them identical in every account.
    ai_chat_model: str = "gpt-5-mini"
    ai_embedding_model: str = "text-embedding-3-small"
    ai_embedding_dimensions: int = 1536

    ai_timeout_seconds: float = 120
    ai_daily_budget_usd: Decimal = Decimal("5")
    # USD per 1M tokens, used for the spend estimate and the daily budget.
    ai_price_input_per_mtok: Decimal = Decimal("0.25")
    ai_price_output_per_mtok: Decimal = Decimal("2.00")
    ai_price_embedding_per_mtok: Decimal = Decimal("0.02")


@lru_cache
def get_settings() -> Settings:
    return Settings()
