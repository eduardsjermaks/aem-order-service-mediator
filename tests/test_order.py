import pytest
from pydantic import ValidationError

from app.domain.order import Order


def test_order_valid_construction() -> None:
    order = Order(
        id=1,
        customer_email="customer@example.com",
        amount=49.99,
        status="pending",
    )

    assert order.id == 1
    assert order.customer_email == "customer@example.com"
    assert order.amount == 49.99
    assert order.status == "pending"
    assert order.created_at is not None
    assert order.updated_at is not None


def test_order_touch_updates_updated_at() -> None:
    order = Order(
        id=1,
        customer_email="customer@example.com",
        amount=49.99,
        status="pending",
    )
    original = order.updated_at

    order.touch()

    assert order.updated_at > original


def test_order_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError, match="customer_email"):
        Order(
            id=1,
            customer_email="not-an-email",
            amount=49.99,
            status="pending",
        )


def test_order_rejects_non_positive_amount() -> None:
    with pytest.raises(ValidationError, match="amount"):
        Order(
            id=1,
            customer_email="customer@example.com",
            amount=0,
            status="pending",
        )
