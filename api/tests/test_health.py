from tests.conftest import MakeClient


def test_health_reports_database_and_pgvector(make_client: MakeClient) -> None:
    response = make_client().get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "ok"
    assert body["pgvector"]


def test_liveness_does_not_need_the_database(make_client: MakeClient) -> None:
    client = make_client(database_url="postgresql+asyncpg://nobody:wrong@127.0.0.1:1/none")

    assert client.get("/health/live").status_code == 200
    assert client.get("/health").status_code == 503
