from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
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

    # Which account block is the primary one (app/ai/providers.py): "openai" reads AI_BASE_URL and
    # AI_API_KEY, "azure" reads AZURE_AI_*, "bedrock" reads BEDROCK_*.
    ai_provider: Literal["openai", "azure", "bedrock"] = "openai"

    # Any OpenAI-compatible endpoint: Azure AI Foundry, OpenAI, OpenRouter, Ollama, LM Studio...
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: SecretStr | None = None
    # AI_PROVIDER=azure: the Foundry resource's v1 endpoint and key.
    azure_ai_base_url: str | None = None
    azure_ai_api_key: SecretStr | None = None
    # AI_PROVIDER=bedrock: Bedrock's OpenAI-compatible endpoint, an API key and the model id
    # (used instead of AI_CHAT_MODEL). Bedrock has no embeddings endpoint there.
    bedrock_base_url: str | None = None
    bedrock_api_key: SecretStr | None = None
    bedrock_model: str | None = None
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

    # Findings each role sees: its own scope's findings at or above this confidence.
    client_confidence_threshold: Decimal = Decimal("0.85")
    reviewer_confidence_threshold: Decimal = Decimal("0.55")

    # HMAC key for personal identifiers (CNP): documents are compared by hash, never plaintext.
    # Changing it makes stored hashes incomparable with new ones; re-upload after a change.
    personal_data_hash_key: SecretStr = SecretStr("local-development-only-hash-key-change-me")

    max_upload_mb: int = 25
    # Parallel AI calls within one verification run.
    verification_concurrency: int = 4
    # Characters of regulation and document text sent with each compliance rule.
    compliance_context_chars: int = 60_000

    # OCR for pages without a text layer (app/ocr/registry.py): "tesseract" or "none".
    ocr_engine: Literal["tesseract", "none"] = "tesseract"
    # Tesseract language packs, best first; the Docker image installs Romanian and English.
    ocr_languages: str = "ron+eng"
    # Render resolution for OCR; 300 suits scans, lower is faster but misses small print.
    ocr_dpi: int = 300
    # Pages read at once; Tesseract uses a CPU core per page.
    ocr_concurrency: int = 2
    ocr_timeout_seconds: float = 120

    @field_validator("personal_data_hash_key")
    @classmethod
    def _hash_key_not_empty(cls, key: SecretStr) -> SecretStr:
        if not key.get_secret_value():
            raise ValueError("PERSONAL_DATA_HASH_KEY is empty: set a key or remove the line.")
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()
