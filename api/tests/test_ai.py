from tests.conftest import FakeProvider, MakeClient


def test_check_calls_chat_and_embeddings_and_records_cost(make_client: MakeClient) -> None:
    client = make_client()

    check = client.post("/api/ai/check")
    usage = client.get("/api/ai/usage").json()

    assert check.status_code == 200
    assert check.json()["chat_answer"] is True
    assert check.json()["embedding_dimensions"] == 8
    chat, embedding = sorted(usage["recent_calls"], key=lambda call: call["id"])
    assert (chat["model"], chat["input_tokens"], chat["output_tokens"]) == ("chat-test", 12, 5)
    # 12 input tokens at $0.25/M + 5 output tokens at $2/M
    assert chat["cost_usd"] == 0.000013
    assert embedding["model"] == "embed-test"
    assert usage["spent_today_usd"] == 0.000013


def test_failed_account_falls_back_to_the_second_one(make_client: MakeClient) -> None:
    provider = FakeProvider(failures={"primary.test": 401})
    client = make_client(provider)

    response = client.post("/api/ai/check")
    calls = client.get("/api/ai/usage").json()["recent_calls"]

    assert response.status_code == 200
    assert [(call["provider"], call["error"] is None) for call in reversed(calls)] == [
        ("primary", False),
        ("fallback", True),
        ("primary", False),
        ("fallback", True),
    ]


def test_bad_request_is_not_retried_on_the_fallback(make_client: MakeClient) -> None:
    provider = FakeProvider(failures={"primary.test": 400})

    response = make_client(provider).post("/api/ai/check")

    assert response.status_code == 502
    assert provider.hosts == ["primary.test"]


def test_spent_budget_blocks_calls(make_client: MakeClient) -> None:
    provider = FakeProvider()

    response = make_client(provider, ai_daily_budget_usd="0").post("/api/ai/check")

    assert response.status_code == 429
    assert provider.hosts == []


def test_missing_key_is_reported(make_client: MakeClient) -> None:
    client = make_client(ai_api_key=None, ai_fallback_api_key=None)

    assert client.post("/api/ai/check").status_code == 503
    assert client.get("/api/ai/usage").json()["configured"] is False


def test_cut_off_answer_is_logged_with_its_tokens(make_client: MakeClient) -> None:
    client = make_client(FakeProvider(answer='{"ready": tr', finish_reason="length"))

    response = client.post("/api/ai/check")
    (call,) = client.get("/api/ai/usage").json()["recent_calls"]

    assert response.status_code == 502
    assert (call["input_tokens"], call["output_tokens"]) == (12, 5)
    assert call["cost_usd"] == 0.000013
    assert call["error"] == "LengthFinishReasonError"


def test_answer_that_breaks_the_schema_is_logged(make_client: MakeClient) -> None:
    client = make_client(FakeProvider(answer='{"ready": "maybe"}'))

    response = client.post("/api/ai/check")
    (call,) = client.get("/api/ai/usage").json()["recent_calls"]

    assert response.status_code == 502
    assert response.json()["detail"] == "The model's answer did not match the expected structure."
    assert call["error"].startswith("ValidationError")
