import pytest
import mongomock
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app
from scripts.seed_data import seed

@pytest.fixture()
def client(monkeypatch):
    mock_client = mongomock.MongoClient()
    db = mock_client["atelier_test"]
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.logging_middleware.database", db)
    seed(db)
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    mock_client.close()

@pytest.fixture()
def alice_token(client):
    response = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "Password123!"})
    return response.json()["access_token"]

