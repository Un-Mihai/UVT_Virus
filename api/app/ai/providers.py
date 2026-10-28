"""Which AI accounts exist, from settings alone. AIClient turns each Account into a client.

Adding a provider is one resolver function plus one entry in PRIMARY_RESOLVERS.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import SecretStr

from app.config import Settings


@dataclass(frozen=True)
class Account:
    name: str
    base_url: str
    api_key: SecretStr
    chat_model: str
    embeddings: bool


def _account(
    name: str, base_url: str | None, api_key: SecretStr | None, chat_model: str, embeddings: bool
) -> Account | None:
    if not (base_url and api_key):
        return None
    return Account(name, base_url, api_key, chat_model, embeddings)


def _openai(settings: Settings) -> Account | None:
    return _account(
        "primary", settings.ai_base_url, settings.ai_api_key, settings.ai_chat_model, True
    )


def _azure(settings: Settings) -> Account | None:
    return _account(
        "azure",
        settings.azure_ai_base_url,
        settings.azure_ai_api_key,
        settings.ai_chat_model,
        True,
    )


def _bedrock(settings: Settings) -> Account | None:
    return _account(
        "bedrock",
        settings.bedrock_base_url,
        settings.bedrock_api_key,
        settings.bedrock_model or settings.ai_chat_model,
        False,
    )


PRIMARY_RESOLVERS: dict[str, Callable[[Settings], Account | None]] = {
    "openai": _openai,
    "azure": _azure,
    "bedrock": _bedrock,
}


def resolve_accounts(settings: Settings) -> list[Account]:
    """The selected primary account, then the generic fallback account, skipping unset ones."""
    fallback = _account(
        "fallback",
        settings.ai_fallback_base_url,
        settings.ai_fallback_api_key,
        settings.ai_chat_model,
        True,
    )
    primary = PRIMARY_RESOLVERS[settings.ai_provider](settings)
    return [account for account in (primary, fallback) if account]
