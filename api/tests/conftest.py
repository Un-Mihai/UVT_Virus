import asyncio
import base64
import json
import os
import struct
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import httpx2
import jwt
import pytest
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.auth import TokenVerifier
from app.config import Settings
from app.main import create_app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/app_test"
)
SETTINGS: dict[str, Any] = {
    "database_url": TEST_DATABASE_URL,
    "ai_base_url": "https://primary.test/v1",
    "ai_api_key": "primary-key",
    "ai_fallback_base_url": "https://fallback.test/v1",
    "ai_fallback_api_key": "fallback-key",
    "ai_chat_model": "chat-test",
    "ai_embedding_model": "embed-test",
    "ai_embedding_dimensions": 8,
    "ai_daily_budget_usd": "5",
    "ai_price_input_per_mtok": "0.25",
    "ai_price_output_per_mtok": "2.00",
    "ai_price_embedding_per_mtok": "0.02",
}
ISSUER = "http://keycloak.test/realms/app"
SIGNING_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StaticKeys:
    """The realm's public key, as Keycloak's JWKS endpoint would serve it."""

    def __init__(self) -> None:
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(SIGNING_KEY.public_key()))
        self.key = jwt.PyJWK(jwk | {"kid": "test-key", "alg": "RS256", "use": "sig"})

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        return self.key


def make_token(key: rsa.RSAPrivateKey = SIGNING_KEY, **overrides: Any) -> str:
    """A Keycloak-shaped access token for the demo reviewer; overrides replace claims."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "aud": "api",
        "sub": "user-1",
        "preferred_username": "reviewer",
        "email": "reviewer@example.com",
        "name": "Demo Reviewer",
        "realm_access": {"roles": ["reviewer"]},
        "iat": now,
        "exp": now + 300,
    }
    return jwt.encode(claims | overrides, key, algorithm="RS256", headers={"kid": "test-key"})


class FakeProvider:
    """Answers OpenAI-style requests; `failures` maps a host to the HTTP status it returns."""

    def __init__(
        self,
        failures: dict[str, int] | None = None,
        answer: str = '{"ready": true}',
        finish_reason: str = "stop",
    ) -> None:
        self.failures = failures or {}
        self.answer = answer
        self.finish_reason = finish_reason
        self.hosts: list[str] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.hosts.append(request.url.host)
        if status := self.failures.get(request.url.host):
            return httpx2.Response(status, json={"error": {"message": f"fake {status}"}})
        body = json.loads(request.content)
        if request.url.path.endswith("/chat/completions"):
            completion = chat_completion(body["model"], self.answer, self.finish_reason)
            return httpx2.Response(200, json=completion)
        if request.url.path.endswith("/embeddings"):
            return httpx2.Response(200, json=embeddings(body))
        return httpx2.Response(404)


def chat_completion(model: str, content: str, finish_reason: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content, "refusal": None},
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
    }


def embeddings(body: dict[str, Any]) -> dict[str, Any]:
    vector = [0.5] * body["dimensions"]
    encoded: str | list[float] = vector
    if body.get("encoding_format") == "base64":
        encoded = base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode()
    return {
        "object": "list",
        "model": body["model"],
        "data": [{"object": "embedding", "index": 0, "embedding": encoded}],
        "usage": {"prompt_tokens": 2, "total_tokens": 2},
    }


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    config = Config(Path(__file__).parents[1] / "alembic.ini")
    config.attributes["database_url"] = TEST_DATABASE_URL
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def empty_tables() -> None:
    async def truncate() -> None:
        engine = create_async_engine(TEST_DATABASE_URL)
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE ai_calls RESTART IDENTITY"))
        await engine.dispose()

    asyncio.run(truncate())


type MakeClient = Callable[..., TestClient]


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
    """Builds the app with test settings (overridable), a fake AI provider and, unless
    `token=None`, a signed-in reviewer's token on every request."""
    with ExitStack() as stack:

        def make(
            provider: FakeProvider | None = None, token: str | None = "default", **overrides: Any
        ) -> TestClient:
            settings = Settings(_env_file=None, **(SETTINGS | overrides))
            transport = httpx2.MockTransport(provider or FakeProvider())
            auth = TokenVerifier(ISSUER, "api", keys=StaticKeys())
            app = create_app(settings, ai_http=httpx2.AsyncClient(transport=transport), auth=auth)
            if token == "default":
                token = make_token()
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return stack.enter_context(TestClient(app, headers=headers))

        yield make
