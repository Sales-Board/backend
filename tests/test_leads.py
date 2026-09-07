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


def _create_customer(external_id: str = "CUST-L-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Lead Owner"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_get_lead() -> None:
    customer_id = _create_customer("CUST-L-002")

    payload = {
        "customer_id": customer_id,
        "source_channel": "website",
        "source_medium": "organic",
        "status": "new",
        "priority": "high",
    }

    create_response = client.post("/api/leads", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["customer_id"] == customer_id

    get_response = client.get(f"/api/leads/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["source_channel"] == "website"


def test_list_update_and_delete_lead() -> None:
    customer_id = _create_customer("CUST-L-003")

    create_response = client.post(
        "/api/leads",
        json={"customer_id": customer_id, "source_channel": "email", "status": "new", "priority": "medium"},
    )
    lead_id = create_response.json()["id"]

    list_response = client.get(f"/api/leads?customer_id={customer_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == lead_id for item in list_response.json())

    update_response = client.patch(f"/api/leads/{lead_id}", json={"status": "qualified", "priority": "high"})
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "qualified"
    assert updated["priority"] == "high"

    delete_response = client.delete(f"/api/leads/{lead_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/leads/{lead_id}")
    assert get_deleted.status_code == 404


def test_create_lead_with_invalid_customer_fails() -> None:
    response = client.post(
        "/api/leads",
        json={"customer_id": 999999, "source_channel": "website", "status": "new", "priority": "low"},
    )
    assert response.status_code == 400
    assert "customer_id" in response.json()["detail"]
