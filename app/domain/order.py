from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field, field_validator


class CancellationNotAllowedError(Exception):
    pass


class Order(BaseModel):
    id: int = Field(gt=0)
    customer_email: EmailStr
    amount: float = Field(gt=0)
    status: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_confirmed(self) -> bool:
        return self.status == "confirmed"

    @property
    def can_cancel(self) -> bool:
        return self.status in {"new", "pending", "confirmed"}

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"new", "pending", "confirmed", "paid", "shipped", "cancelled"}
        if normalized not in allowed:
            raise ValueError(
                "status must be one of: new, pending, confirmed, paid, shipped, cancelled"
            )
        return normalized

    def validate_email_change(self, new_email: str) -> None:
        """Validate that email can be changed. Raises ValueError if change is not allowed."""
        if self.is_confirmed and new_email != self.customer_email:
            raise ValueError(
                "customer_email cannot be changed after an order is confirmed"
            )

    def cancel(self) -> None:
        if not self.can_cancel:
            raise CancellationNotAllowedError
        self.status = "cancelled"

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
