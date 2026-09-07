from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_and_get_product() -> None:
    payload = {
        "code": "PROD-TERM-001",
        "name": "Term Life Plan",
        "category": "Protection",
        "is_active": True,
    }

    create_response = client.post("/api/products", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["code"] == payload["code"]

    get_response = client.get(f"/api/products/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Term Life Plan"


def test_list_update_and_delete_product() -> None:
    create_response = client.post(
        "/api/products",
        json={"code": "PROD-ULIP-001", "name": "ULIP Growth", "category": "Investment", "is_active": True},
    )
    product_id = create_response.json()["id"]

    list_response = client.get("/api/products")
    assert list_response.status_code == 200
    assert any(item["id"] == product_id for item in list_response.json())

    update_response = client.patch(
        f"/api/products/{product_id}",
        json={"name": "ULIP Growth Plus", "is_active": False},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "ULIP Growth Plus"
    assert updated["is_active"] is False

    delete_response = client.delete(f"/api/products/{product_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/products/{product_id}")
    assert get_deleted.status_code == 404


def test_unique_product_code_conflict() -> None:
    payload = {"code": "PROD-DUP-001", "name": "Duplicate Product", "category": "Test", "is_active": True}

    first = client.post("/api/products", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/products", json=payload)
    assert duplicate.status_code == 409
    assert "unique" in duplicate.json()["detail"]
