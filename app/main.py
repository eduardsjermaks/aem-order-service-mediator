from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.domain.order import CancellationNotAllowedError, Order
from app.repository import OrderRepository

app = FastAPI(title="AEM Order Service")
app.state.order_repository = OrderRepository()


class OrderCreateRequest(BaseModel):
    customer_email: EmailStr
    amount: float = Field(gt=0)
    status: str = Field(min_length=1)


class OrderUpdateRequest(BaseModel):
    customer_email: EmailStr
    amount: float = Field(gt=0)
    status: str = Field(min_length=1)


class OrderResponse(BaseModel):
    id: int
    customer_email: EmailStr
    amount: float
    status: str
    created_at: str


def get_order_or_404(repository: OrderRepository, order_id: int) -> Order:
    try:
        return repository.get(order_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        ) from exc


def order_to_response(order: Order) -> OrderResponse:
    """Convert an Order domain object to an OrderResponse."""
    return OrderResponse(
        id=order.id,
        customer_email=order.customer_email,
        amount=order.amount,
        status=order.status,
        created_at=order.created_at.isoformat(),
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreateRequest) -> Any:
    repository: OrderRepository = app.state.order_repository
    next_id = len(repository.list()) + 1
    order = Order(
        id=next_id,
        customer_email=payload.customer_email,
        amount=payload.amount,
        status=payload.status,
    )
    order.touch()
    created = repository.create(order)
    return order_to_response(created)


@app.get("/orders", response_model=list[OrderResponse])
def list_orders(status: str | None = Query(default=None)) -> Any:
    repository: OrderRepository = app.state.order_repository
    orders = repository.list()
    if status is not None:
        normalized = status.strip().lower()
        orders = [order for order in orders if order.status.lower() == normalized]
    return [order_to_response(order) for order in orders]


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int) -> Any:
    repository: OrderRepository = app.state.order_repository
    order = get_order_or_404(repository, order_id)
    return order_to_response(order)


@app.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, payload: OrderUpdateRequest) -> Any:
    repository: OrderRepository = app.state.order_repository
    order = get_order_or_404(repository, order_id)

    try:
        order.validate_email_change(payload.customer_email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    updated = Order(
        id=order.id,
        customer_email=payload.customer_email,
        amount=payload.amount,
        status=payload.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
    updated.touch()
    repository.update(order_id, updated)
    return order_to_response(updated)


@app.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int) -> Any:
    repository: OrderRepository = app.state.order_repository
    order = get_order_or_404(repository, order_id)

    try:
        order.cancel()
    except CancellationNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order can only be cancelled from NEW, PENDING, or CONFIRMED status",
        ) from exc

    order.touch()
    repository.update(order_id, order)
    return order_to_response(order)
