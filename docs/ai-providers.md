# AI providers

The API talks to any OpenAI-compatible endpoint. Which one, with which key and models, is decided
only by environment variables, so switching providers (or handing the app to a client who brings
their own) never needs a code change.

All calls go through `AIClient` (`api/app/ai/client.py`), which:

- refuses calls once today's estimated spend reaches `AI_DAILY_BUDGET_USD`;
- retries on the fallback account when the primary fails with a bad key, missing permission,
  throttling, a connection error or a server error (a bad request is not retried: it would fail
  the same way);
- records every call in the `ai_calls` table with tokens, estimated cost, duration and error,
  shown on `/status`.

Copy one block into `.env`, restart the API (`docker compose up -d api`), then press **Run AI
check** on http://localhost:3000/status.

## Azure AI Foundry (Azure for Students credits)

```bash
AI_BASE_URL=https://<resource>.openai.azure.com/openai/v1/
AI_API_KEY=<key 1 from the resource's Keys and Endpoint page>
AI_CHAT_MODEL=gpt-5-mini
AI_EMBEDDING_MODEL=text-embedding-3-small
```

- After `make deploy`, `make azure-env` prints the first two lines for the account Terraform
  created.
- On Azure, model names are deployment names. Terraform names each deployment after its model,
  so the same `.env` works on OpenAI. Deploy models yourself with exactly these names.
- The v1 endpoint needs no `api-version`.
- Student subscriptions may only get quota for a few models (gpt-5-mini, text-embedding-3-small).
  Check before planning around another model (`docs/deploy-azure.md`, step 2).
- Claude models on Foundry need a pay-as-you-go subscription with Marketplace access; student
  credits cannot use them.

## OpenAI

```bash
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-...
AI_CHAT_MODEL=gpt-5-mini
AI_EMBEDDING_MODEL=text-embedding-3-small
```

## Tokens from the organisers, or another provider

If the provider is OpenAI-compatible (OpenRouter, Mistral, Groq, Together, Google's OpenAI
endpoint `https://generativelanguage.googleapis.com/v1beta/openai/` and many more), set its base
URL, key and model names, and its prices:

```bash
AI_PRICE_INPUT_PER_MTOK=...
AI_PRICE_OUTPUT_PER_MTOK=...
AI_PRICE_EMBEDDING_PER_MTOK=...
```

Two things to check first:

- **Embeddings:** some providers have none (Groq, Anthropic). Keep embeddings on a provider that
  has them, or skip retrieval; the starter only embeds in the AI check and in features you add.
- **Structured output:** `AIClient.complete` sends a JSON Schema (`response_format`). Run the
  AI check: if it fails with a schema error, the provider does not support it.

For Anthropic's Claude API, add a Claude path inside `AIClient` with the official `anthropic`
SDK and its structured outputs, keeping the same budget check and `ai_calls` record. The rest of
the app does not change.

## Local models, no credits

[Ollama](https://ollama.com) or LM Studio on your laptop:

```bash
AI_BASE_URL=http://host.docker.internal:11434/v1   # from Docker; http://localhost:11434/v1 natively
AI_API_KEY=ollama                                    # any non-empty value
AI_CHAT_MODEL=qwen3:8b
AI_EMBEDDING_MODEL=nomic-embed-text
AI_EMBEDDING_DIMENSIONS=768
AI_PRICE_INPUT_PER_MTOK=0
AI_PRICE_OUTPUT_PER_MTOK=0
AI_PRICE_EMBEDDING_PER_MTOK=0
```

Good for wiring and offline work; expect weaker extraction than hosted models. The embedding size
differs from the default (768 instead of 1536), so vector columns must use the same number. On
Linux, start Ollama with `OLLAMA_HOST=0.0.0.0 ollama serve` so the API container can reach it.

## A second account as fallback

Each teammate can activate Azure for Students ($100 each). Create the same two deployments in a
teammate's subscription (commands in `docs/deploy-azure.md`, step 5) and set:

```bash
AI_FALLBACK_BASE_URL=https://<their-resource>.openai.azure.com/openai/v1/
AI_FALLBACK_API_KEY=<their key>
```

When the first account runs out of credit or is throttled, calls move to the second. `/status`
shows which account answered each call.

## Model notes

- GPT-5-family models reject `temperature` and `max_tokens`; `AIClient` sends neither.
- Azure's structured output (strict mode) requires every field and rejects `pattern`, `format`,
  `minLength`, `minimum`, `minItems`: keep Pydantic schemas plain and validate after parsing.
- Prices in `.env.example` are for gpt-5-mini and text-embedding-3-small (October 2026); update
  them when you change models, or the spend shown on `/status` and the daily budget are wrong.
