import time

from cryptography.hazmat.primitives.asymmetric import rsa

from tests.conftest import MakeClient, make_token


def test_api_returns_the_signed_in_user(make_client: MakeClient) -> None:
    response = make_client().get("/api/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-1",
        "username": "reviewer",
        "email": "reviewer@example.com",
        "name": "Demo Reviewer",
        "roles": ["reviewer"],
    }


def test_api_routes_need_a_token(make_client: MakeClient) -> None:
    client = make_client(token=None)

    assert client.get("/api/me").status_code == 401
    assert client.get("/api/ai/usage").status_code == 401
    assert client.post("/api/ai/check").headers["www-authenticate"] == "Bearer"


def test_health_stays_public(make_client: MakeClient) -> None:
    client = make_client(token=None)

    assert client.get("/health").status_code == 200
    assert client.get("/health/live").status_code == 200


def test_rejects_expired_tokens(make_client: MakeClient) -> None:
    expired = make_token(exp=int(time.time()) - 60)

    response = make_client(token=expired).get("/api/me")

    assert response.status_code == 401
    assert "expired" in response.json()["detail"]


def test_rejects_tokens_for_another_audience_or_issuer(make_client: MakeClient) -> None:
    assert make_client(token=make_token(aud="account")).get("/api/me").status_code == 401
    assert (
        make_client(token=make_token(iss="https://evil.test/realms/app")).get("/api/me").status_code
        == 401
    )


def test_rejects_tokens_signed_with_another_key(make_client: MakeClient) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    response = make_client(token=make_token(key=other_key)).get("/api/me")

    assert response.status_code == 401
    assert "Signature" in response.json()["detail"]
