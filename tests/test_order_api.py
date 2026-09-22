from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.order_cancelled import AuditRepository, NotificationRepository
from app.repository import OrderRepository

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repository() -> None:
    app.state.order_repository = OrderRepository()
    app.state.audit_repository = AuditRepository()
    app.state.notification_repository = NotificationRepository()


def test_create_order_returns_201_and_order_payload() -> None:
    response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "pending",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload == {
        "id": 1,
        "customer_email": "customer@example.com",
        "amount": 49.99,
        "status": "pending",
        "created_at": payload["created_at"],
    }
    datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))


def test_get_order_returns_saved_order() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "pending",
        },
    )

    response = client.get(f"/orders/{create_response.json()['id']}")

    assert response.status_code == 200
    assert response.json() == create_response.json()


def test_get_missing_order_returns_404() -> None:
    response = client.get("/orders/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order with id 999 not found"}


def test_create_order_rejects_invalid_email() -> None:
    response = client.post(
        "/orders",
        json={
            "customer_email": "not-an-email",
            "amount": 49.99,
            "status": "pending",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "customer_email"]


def test_list_orders_returns_all_orders() -> None:
    client.post(
        "/orders",
        json={
            "customer_email": "first@example.com",
            "amount": 25.0,
            "status": "pending",
        },
    )
    client.post(
        "/orders",
        json={
            "customer_email": "second@example.com",
            "amount": 75.5,
            "status": "paid",
        },
    )

    response = client.get("/orders")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["customer_email"] == "first@example.com"
    assert response.json()[1]["customer_email"] == "second@example.com"


def test_update_order_returns_updated_order() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "pending",
        },
    )
    order_id = create_response.json()["id"]

    response = client.put(
        f"/orders/{order_id}",
        json={
            "customer_email": "updated@example.com",
            "amount": 99.99,
            "status": "paid",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": order_id,
        "customer_email": "updated@example.com",
        "amount": 99.99,
        "status": "paid",
        "created_at": response.json()["created_at"],
    }


def test_update_missing_order_returns_404() -> None:
    response = client.put(
        "/orders/999",
        json={
            "customer_email": "customer@example.com",
            "amount": 99.99,
            "status": "paid",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Order with id 999 not found"}


def test_cancel_order_returns_cancelled_status() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "pending",
        },
    )
    order_id = create_response.json()["id"]

    response = client.post(f"/orders/{order_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["id"] == order_id

    audit_response = client.get(f"/orders/{order_id}/audit-records")
    notification_response = client.get(f"/orders/{order_id}/notifications")

    assert audit_response.status_code == 200
    assert len(audit_response.json()) == 1
    assert audit_response.json()[0] == {
        "order_id": order_id,
        "action": "order_cancelled",
        "at": audit_response.json()[0]["at"],
    }
    datetime.fromisoformat(audit_response.json()[0]["at"].replace("Z", "+00:00"))
    assert notification_response.status_code == 200
    assert len(notification_response.json()) == 1
    assert notification_response.json()[0] == {
        "order_id": order_id,
        "type": "order_cancelled",
        "recipient": "customer@example.com",
        "message": f"Order {order_id} was cancelled",
        "at": notification_response.json()[0]["at"],
    }
    datetime.fromisoformat(notification_response.json()[0]["at"].replace("Z", "+00:00"))


def test_failed_cancellation_creates_no_effects() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "shipped",
        },
    )
    order_id = create_response.json()["id"]

    assert client.post(f"/orders/{order_id}/cancel").status_code == 400
    assert client.get(f"/orders/{order_id}/audit-records").json() == []
    assert client.get(f"/orders/{order_id}/notifications").json() == []

    assert client.post("/orders/999/cancel").status_code == 404
    assert client.get("/orders/999/audit-records").status_code == 404
    assert client.get("/orders/999/notifications").status_code == 404


def test_repeated_cancellation_creates_no_additional_effects() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "pending",
        },
    )
    order_id = create_response.json()["id"]

    assert client.post(f"/orders/{order_id}/cancel").status_code == 200
    assert client.post(f"/orders/{order_id}/cancel").status_code == 400
    assert len(client.get(f"/orders/{order_id}/audit-records").json()) == 1
    assert len(client.get(f"/orders/{order_id}/notifications").json()) == 1


def test_cancel_missing_order_returns_404() -> None:
    response = client.post("/orders/999/cancel")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order with id 999 not found"}


def test_list_orders_filters_by_status() -> None:
    client.post(
        "/orders",
        json={
            "customer_email": "first@example.com",
            "amount": 25.0,
            "status": "pending",
        },
    )
    client.post(
        "/orders",
        json={
            "customer_email": "second@example.com",
            "amount": 30.0,
            "status": "paid",
        },
    )

    response = client.get("/orders?status=paid")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "paid"


def test_cancel_order_rejects_invalid_status() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "paid",
        },
    )
    order_id = create_response.json()["id"]

    response = client.post(f"/orders/{order_id}/cancel")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Order can only be cancelled from NEW, PENDING, or CONFIRMED status"
    }


def test_update_order_cannot_change_email_after_confirmation() -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "amount": 49.99,
            "status": "confirmed",
        },
    )
    order_id = create_response.json()["id"]

    response = client.put(
        f"/orders/{order_id}",
        json={
            "customer_email": "changed@example.com",
            "amount": 49.99,
            "status": "confirmed",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "customer_email cannot be changed after an order is confirmed"
    }
