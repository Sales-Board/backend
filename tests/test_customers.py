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


def test_create_and_get_customer() -> None:
    payload = {
        "external_customer_id": "CUST-001",
        "first_name": "Asha",
        "last_name": "Rao",
        "email": "asha@example.com",
        "phone": "+910000000001",
    }

    create_response = client.post("/api/customers", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["external_customer_id"] == payload["external_customer_id"]
    assert created["id"] > 0

    get_response = client.get(f"/api/customers/{created['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["first_name"] == "Asha"


def test_list_update_and_delete_customer() -> None:
    create_response = client.post(
        "/api/customers",
        json={"external_customer_id": "CUST-002", "first_name": "Vikram"},
    )
    customer_id = create_response.json()["id"]

    list_response = client.get("/api/customers")
    assert list_response.status_code == 200
    assert any(item["id"] == customer_id for item in list_response.json())

    update_response = client.patch(f"/api/customers/{customer_id}", json={"last_name": "Singh"})
    assert update_response.status_code == 200
    assert update_response.json()["last_name"] == "Singh"

    delete_response = client.delete(f"/api/customers/{customer_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/customers/{customer_id}")
    assert get_deleted.status_code == 404


def test_unique_external_customer_id_conflict() -> None:
    payload = {"external_customer_id": "CUST-003", "first_name": "Meera"}

    first = client.post("/api/customers", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/customers", json=payload)
    assert duplicate.status_code == 409
    assert "unique" in duplicate.json()["detail"]
