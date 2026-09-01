from __future__ import annotations

from typing import Dict, List

from app.domain.order import Order


class OrderRepository:
    """Minimal synchronous in-memory repository for Order objects."""

    def __init__(self) -> None:
        self._orders: Dict[int, Order] = {}

    def create(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    def get(self, order_id: int) -> Order:
        return self._orders[order_id]

    def list(self) -> List[Order]:
        return list(self._orders.values())

    def update(self, order_id: int, order: Order) -> Order:
        if order_id not in self._orders:
            raise KeyError(order_id)
        self._orders[order_id] = order
        return order
