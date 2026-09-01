import pytest

from app.domain.order import Order
from app.repository import OrderRepository


def make_order(**overrides):
    data = {
        "id": 1,
        "customer_email": "customer@example.com",
        "amount": 49.99,
        "status": "pending",
    }
    data.update(overrides)
    return Order(**data)


def test_repository_create_and_get_order() -> None:
    repo = OrderRepository()
    order = make_order(id=1)

    created = repo.create(order)

    assert created == order
    assert repo.get(1) == order


def test_repository_list_returns_all_orders() -> None:
    repo = OrderRepository()
    first = make_order(id=1)
    second = make_order(id=2, customer_email="another@example.com")

    repo.create(first)
    repo.create(second)

    assert repo.list() == [first, second]


def test_repository_update_replaces_order() -> None:
    repo = OrderRepository()
    order = make_order(id=3, status="pending")
    repo.create(order)

    updated = make_order(id=3, status="paid", amount=99.99)
    result = repo.update(3, updated)

    assert result == updated
    assert repo.get(3) == updated


def test_repository_get_unknown_order_raises_key_error() -> None:
    repo = OrderRepository()

    with pytest.raises(KeyError):
        repo.get(404)
