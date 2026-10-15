from datetime import timedelta
from app.security import create_access_token

def test_signup_login_and_me(client):
    response = client.post("/api/v1/auth/signup", json={"name": "Test User", "email": "test@example.com", "password": "Strongpass1!"})
    assert response.status_code == 201 and "password_hash" not in response.text
    token = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Strongpass1!"}).json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "bad"}).status_code == 401

def test_logout_revokes_and_expired_invalid_tokens(client):
    token = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/customers/me", headers=headers).status_code == 401
    expired, _, _ = create_access_token(1, timedelta(seconds=-1))
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401

def test_refresh_rotates_and_revokes_old_token(client):
    token = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    rotated = client.post("/api/v1/auth/refresh", headers=headers)
    assert rotated.status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + rotated.json()["access_token"]}).status_code == 200

def test_forgot_password_and_single_use_reset(client, capsys):
    response = client.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
    assert response.status_code == 200 and "token" not in response.text.lower()
    token = capsys.readouterr().out.strip().split("token=", 1)[1]
    payload = {"token": token, "new_password": "ChangedPassword123!"}
    assert client.post("/api/v1/auth/reset-password", json=payload).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json=payload).status_code == 400
    assert client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "ChangedPassword123!"}).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json={"token": "not-a-real-reset-token-at-all", "new_password": "ChangedPassword123!"}).status_code == 400

def test_reset_password_token_expiry(client):
    from app.config import settings
    previous = settings.reset_token_minutes
    settings.reset_token_minutes = -1
    try:
        client.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
    finally:
        settings.reset_token_minutes = previous



