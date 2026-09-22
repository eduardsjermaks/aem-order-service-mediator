from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Mediator:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], Callable[[Any], Any]] = {}
        self._subscribers: dict[type[Any], list[Callable[[Any], None]]] = {}

    def register(self, message_type: type[Any], handler: Callable[[Any], Any]) -> None:
        self._handlers[message_type] = handler

    def send(self, message: Any) -> Any:
        return self._handlers[type(message)](message)

    def subscribe(self, event_type: type[Any], subscriber: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(subscriber)

    def publish(self, event: Any) -> None:
        for subscriber in self._subscribers.get(type(event), []):
            subscriber(event)