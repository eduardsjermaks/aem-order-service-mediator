from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Mediator:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], Callable[[Any], Any]] = {}

    def register(self, message_type: type[Any], handler: Callable[[Any], Any]) -> None:
        self._handlers[message_type] = handler

    def send(self, message: Any) -> Any:
        return self._handlers[type(message)](message)