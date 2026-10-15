import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from scripts.seed_data import seed

@pytest.fixture()
def client():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    TestingSession=sessionmaker(bind=engine,autoflush=False,autocommit=False,expire_on_commit=False)
    Base.metadata.create_all(engine)
    with TestingSession() as db:seed(db)
    def override_db():
        db=TestingSession()
        try:yield db
        finally:db.close()
    app.dependency_overrides[get_db]=override_db
    with TestClient(app) as c:yield c
    app.dependency_overrides.clear();Base.metadata.drop_all(engine);engine.dispose()

@pytest.fixture()
def alice_token(client):
    r=client.post("/api/v1/auth/login",json={"email":"alice@example.com","password":"Password123!"})
    return r.json()["access_token"]
