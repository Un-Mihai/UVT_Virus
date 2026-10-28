import asyncio
import base64
import json
import os
import struct
import time
from collections.abc import Callable, Iterator, Mapping
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
from app.models import Base
from app.ocr import EngineStatus, OcrError, RecognizedPage, RecognizedWord

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
    # Tests never need the Tesseract binary; OCR tests inject FakeOcrEngine.
    "ocr_engine": "none",
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


class FakeOcrEngine:
    """Reads every page as the given lines, word by word, each with `confidence`."""

    name = "fake"

    def __init__(
        self, lines: list[str] | None = None, confidence: float = 0.9, fail: bool = False
    ) -> None:
        self.lines = lines or ["Synthetic scanned page"]
        self.confidence = confidence
        self.fail = fail
        self.calls = 0

    async def recognize(self, png: bytes, dpi: int) -> RecognizedPage:
        self.calls += 1
        if self.fail:
            raise OcrError("fake engine failure")
        pixel = dpi / 72  # boxes in pixels, as a real engine returns them
        words = []
        for row, line in enumerate(self.lines):
            top, left = (90 + 14 * row) * pixel, 72 * pixel
            for word in line.split():
                width = 6 * len(word) * pixel
                words.append(
                    RecognizedWord(word, left, top, left + width, top + 11 * pixel, self.confidence)
                )
                left += width + 3 * pixel
        return RecognizedPage("\n".join(self.lines), words)

    async def probe(self) -> EngineStatus:
        return EngineStatus(self.name, True, "fake 1.0", ["eng", "ron"], None)


def run_sql(statement: str, **params: Any) -> list[Any]:
    """Runs SQL on the test database, for setting up states the API cannot reach directly."""

    async def execute() -> list[Any]:
        engine = create_async_engine(TEST_DATABASE_URL)
        async with engine.begin() as connection:
            result = await connection.execute(text(statement), params)
            rows = list(result.all()) if result.returns_rows else []
        await engine.dispose()
        return rows

    return asyncio.run(execute())


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


type Answer = str | Callable[[dict[str, Any]], str]


class FakeProvider:
    """Answers OpenAI-style requests; `failures` maps a host to the HTTP status it returns.

    `answers` maps a structured-output schema name (PageFacts, ComplianceVerdict) to the JSON
    to return, or to a function of the request body; other chat requests get `answer`.
    """

    def __init__(
        self,
        failures: dict[str, int] | None = None,
        answer: str = '{"ready": true}',
        finish_reason: str = "stop",
        answers: Mapping[str, Answer] | None = None,
    ) -> None:
        self.failures = failures or {}
        self.answer = answer
        self.finish_reason = finish_reason
        self.answers = answers or {}
        self.hosts: list[str] = []
        self.bodies: list[dict[str, Any]] = []

    def schema_requests(self, name: str) -> list[dict[str, Any]]:
        return [body for body in self.bodies if schema_name(body) == name]

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.hosts.append(request.url.host)
        if status := self.failures.get(request.url.host):
            return httpx2.Response(status, json={"error": {"message": f"fake {status}"}})
        body = json.loads(request.content)
        self.bodies.append(body)
        if request.url.path.endswith("/chat/completions"):
            answer = self.answers.get(schema_name(body) or "", self.answer)
            content = answer(body) if callable(answer) else answer
            completion = chat_completion(body["model"], content, self.finish_reason)
            return httpx2.Response(200, json=completion)
        if request.url.path.endswith("/embeddings"):
            return httpx2.Response(200, json=embeddings(body))
        return httpx2.Response(404)


def schema_name(body: dict[str, Any]) -> str | None:
    name: str | None = body.get("response_format", {}).get("json_schema", {}).get("name")
    return name


def prompt_of(body: dict[str, Any]) -> str:
    """The user message of a chat request."""
    content: str = body["messages"][-1]["content"]
    return content


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
            tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
            await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        await engine.dispose()

    asyncio.run(truncate())


DEMO_USERS = {
    "client": ("user-client", "client"),
    "client-2": ("user-client-2", "client"),
    "reviewer": ("user-1", "reviewer"),
    "admin": ("user-admin", "admin"),
}


def token_for(user: str) -> str:
    """A token for a demo user: client, client-2 (another applicant), reviewer or admin."""
    subject, role = DEMO_USERS[user]
    return make_token(
        sub=subject, preferred_username=user, email=None, name=None, realm_access={"roles": [role]}
    )


def as_user(client: TestClient, user: str) -> TestClient:
    """The same app, now calling as another demo user."""
    client.headers["Authorization"] = f"Bearer {token_for(user)}"
    return client


type MakeClient = Callable[..., TestClient]


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
    """Builds the app with test settings (overridable), a fake AI provider and, unless
    `token=None`, a signed-in reviewer's token on every request."""
    with ExitStack() as stack:

        def make(
            provider: FakeProvider | None = None,
            token: str | None = "default",
            ocr: FakeOcrEngine | None = None,
            **overrides: Any,
        ) -> TestClient:
            settings = Settings(_env_file=None, **(SETTINGS | overrides))
            transport = httpx2.MockTransport(provider or FakeProvider())
            auth = TokenVerifier(ISSUER, "api", keys=StaticKeys())
            app = create_app(
                settings, ai_http=httpx2.AsyncClient(transport=transport), auth=auth, ocr=ocr
            )
            if token == "default":
                token = make_token()
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return stack.enter_context(TestClient(app, headers=headers))

        yield make
