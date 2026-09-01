from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.domain.order import Order
from app.repository import OrderRepository


@dataclass(frozen=True)
class CancelOrder:
    order_id: int


class CancelOrderHandler:
    def __init__(self, get_repository: Callable[[], OrderRepository]) -> None:
        self._get_repository = get_repository

    def __call__(self, command: CancelOrder) -> Order:
        repository = self._get_repository()
        order = repository.get(command.order_id)
        order.cancel()
        order.touch()
        return repository.update(command.order_id, order)