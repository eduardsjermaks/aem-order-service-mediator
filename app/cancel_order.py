from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.order import Order
from app.order_cancelled import OrderCancelled
from app.repository import OrderRepository


@dataclass(frozen=True)
class CancelOrder:
    order_id: int


class CancelOrderHandler:
    def __init__(
        self,
        get_repository: Callable[[], OrderRepository],
        publish: Callable[[OrderCancelled], None],
    ) -> None:
        self._get_repository = get_repository
        self._publish = publish

    def __call__(self, command: CancelOrder) -> Order:
        repository = self._get_repository()
        order = repository.get(command.order_id)
        order.cancel()
        order.touch()
        updated = repository.update(command.order_id, order)
        self._publish(
            OrderCancelled(
                order_id=updated.id,
                customer_email=str(updated.customer_email),
                occurred_at=datetime.now(timezone.utc),
            )
        )
        return updated