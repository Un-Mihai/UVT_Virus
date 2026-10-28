import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

import httpx2
import openai
from openai import AsyncOpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletionMessageParam, ParsedChatCompletion
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.models import AiCall

# Errors that another account may not have: bad or expired key, exhausted credit,
# throttling, outages. Anything else (a bad request) would fail the same way there.
FAILOVER_ERRORS = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.InternalServerError,
)
MILLION = Decimal(1_000_000)


class AINotConfiguredError(RuntimeError):
    pass


class BudgetExceededError(RuntimeError):
    pass


class AIResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class Provider:
    name: str
    client: AsyncOpenAI


class AIClient:
    """The only place the app talks to an AI provider.

    Every call is checked against the daily budget and recorded in ai_calls with its
    token counts and estimated cost.
    """

    def __init__(
        self,
        settings: Settings,
        sessions: async_sessionmaker[AsyncSession],
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self._sessions = sessions
        self.providers: list[Provider] = []
        accounts = [
            ("primary", settings.ai_base_url, settings.ai_api_key),
            ("fallback", settings.ai_fallback_base_url, settings.ai_fallback_api_key),
        ]
        for name, base_url, api_key in accounts:
            if base_url and api_key:
                client = AsyncOpenAI(
                    base_url=base_url,
                    api_key=api_key.get_secret_value(),
                    timeout=settings.ai_timeout_seconds,
                    http_client=http_client,
                )
                self.providers.append(Provider(name, client))

    async def close(self) -> None:
        for provider in self.providers:
            await provider.client.close()

    async def complete[T: BaseModel](
        self,
        *,
        purpose: str,
        messages: Sequence[ChatCompletionMessageParam],
        schema: type[T],
    ) -> T:
        """Chat completion whose answer is validated against `schema` (JSON Schema mode)."""
        model = self.settings.ai_chat_model

        async def request(client: AsyncOpenAI) -> ParsedChatCompletion[T]:
            return await client.chat.completions.parse(
                model=model, messages=list(messages), response_format=schema
            )

        def tokens(completion: ParsedChatCompletion[T]) -> tuple[int, int]:
            usage = completion.usage
            return (usage.prompt_tokens, usage.completion_tokens) if usage else (0, 0)

        completion = await self._run(
            purpose,
            model,
            request,
            tokens,
            self.settings.ai_price_input_per_mtok,
            self.settings.ai_price_output_per_mtok,
        )
        message = completion.choices[0].message
        if message.parsed is None:
            raise AIResponseError(message.refusal or "The model returned no structured answer.")
        return message.parsed

    async def embed(self, *, purpose: str, texts: Sequence[str]) -> list[list[float]]:
        model = self.settings.ai_embedding_model

        async def request(client: AsyncOpenAI) -> CreateEmbeddingResponse:
            return await client.embeddings.create(
                model=model, input=list(texts), dimensions=self.settings.ai_embedding_dimensions
            )

        response = await self._run(
            purpose,
            model,
            request,
            lambda response: (response.usage.prompt_tokens, 0),
            self.settings.ai_price_embedding_per_mtok,
            Decimal(0),
        )
        return [item.embedding for item in response.data]

    async def spent_today(self) -> Decimal:
        async with self._sessions() as session:
            total = await session.scalar(
                select(func.coalesce(func.sum(AiCall.cost_usd), 0)).where(
                    AiCall.created_at >= func.date_trunc("day", func.now())
                )
            )
        return Decimal(total or 0)

    async def _run[R](
        self,
        purpose: str,
        model: str,
        request: Callable[[AsyncOpenAI], Awaitable[R]],
        tokens: Callable[[R], tuple[int, int]],
        input_price: Decimal,
        output_price: Decimal,
    ) -> R:
        if not self.providers:
            raise AINotConfiguredError("Set AI_BASE_URL and AI_API_KEY to call an AI provider.")
        budget = self.settings.ai_daily_budget_usd
        # shortcut: checked before the call, so parallel calls can overshoot by a few calls;
        # fine for a daily cap, use a row lock if the budget must be exact.
        if await self.spent_today() >= budget:
            raise BudgetExceededError(
                f"Today's AI budget of ${budget} is used up. Raise AI_DAILY_BUDGET_USD to continue."
            )

        def cost(used: tuple[int, int]) -> Decimal:
            return (used[0] * input_price + used[1] * output_price) / MILLION

        for provider in self.providers:
            started = time.perf_counter()
            try:
                response = await request(provider.client)
            except openai.APIError as error:
                failure = f"{type(error).__name__}: {error.message}"
                await self._record(
                    purpose, provider.name, model, (0, 0), Decimal(0), started, failure
                )
                if isinstance(error, FAILOVER_ERRORS) and provider is not self.providers[-1]:
                    continue
                raise
            except (openai.LengthFinishReasonError, openai.ContentFilterFinishReasonError) as error:
                # The provider answered, and billed, but the answer was cut off or filtered.
                usage = error.completion.usage if error.completion else None
                used = (usage.prompt_tokens, usage.completion_tokens) if usage else (0, 0)
                failure = type(error).__name__
                await self._record(
                    purpose, provider.name, model, used, cost(used), started, failure
                )
                raise AIResponseError(
                    f"The model's answer was cut off or filtered ({failure})."
                ) from error
            except ValidationError as error:
                # The token counts are lost with the unparsable answer; the call is still logged.
                failure = "ValidationError: the answer did not match the schema"
                await self._record(
                    purpose, provider.name, model, (0, 0), Decimal(0), started, failure
                )
                raise AIResponseError(
                    "The model's answer did not match the expected structure."
                ) from error
            used = tokens(response)
            await self._record(purpose, provider.name, model, used, cost(used), started, None)
            return response
        raise AssertionError("unreachable: the last provider re-raises its error")

    async def _record(
        self,
        purpose: str,
        provider: str,
        model: str,
        used: tuple[int, int],
        cost: Decimal,
        started: float,
        error: str | None,
    ) -> None:
        async with self._sessions() as session:
            session.add(
                AiCall(
                    purpose=purpose,
                    provider=provider,
                    model=model,
                    input_tokens=used[0],
                    output_tokens=used[1],
                    cost_usd=cost,
                    duration_ms=round((time.perf_counter() - started) * 1000),
                    error=error,
                )
            )
            await session.commit()
