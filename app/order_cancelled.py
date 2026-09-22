from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderCancelled:
    order_id: int
    customer_email: str
    occurred_at: datetime


@dataclass(frozen=True)
class AuditRecord:
    order_id: int
    action: str
    at: datetime


@dataclass(frozen=True)
class Notification:
    order_id: int
    type: str
    recipient: str
    message: str
    at: datetime


class AuditRepository:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def create(self, record: AuditRecord) -> AuditRecord:
        self._records.append(record)
        return record

    def list_for_order(self, order_id: int) -> list[AuditRecord]:
        return [record for record in self._records if record.order_id == order_id]


class NotificationRepository:
    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def create(self, notification: Notification) -> Notification:
        self._notifications.append(notification)
        return notification

    def list_for_order(self, order_id: int) -> list[Notification]:
        return [
            notification
            for notification in self._notifications
            if notification.order_id == order_id
        ]


class AuditSubscriber:
    def __init__(self, get_repository: Callable[[], AuditRepository]) -> None:
        self._get_repository = get_repository

    def __call__(self, event: OrderCancelled) -> None:
        self._get_repository().create(
            AuditRecord(
                order_id=event.order_id,
                action="order_cancelled",
                at=event.occurred_at,
            )
        )


class NotificationSubscriber:
    def __init__(self, get_repository: Callable[[], NotificationRepository]) -> None:
        self._get_repository = get_repository

    def __call__(self, event: OrderCancelled) -> None:
        self._get_repository().create(
            Notification(
                order_id=event.order_id,
                type="order_cancelled",
                recipient=event.customer_email,
                message=f"Order {event.order_id} was cancelled",
                at=event.occurred_at,
            )
        )