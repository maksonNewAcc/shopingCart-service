from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), kw_only=True)


@dataclass(frozen=True)
class CartItemAdded(DomainEvent):
    cart_id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CartItemRemoved(DomainEvent):
    cart_id: UUID
    product_id: UUID


@dataclass(frozen=True)
class CheckoutLine:
    product_id: UUID
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CheckoutInitiated(DomainEvent):
    """Hand-off to Payment and Order (Order.source_cart_id, OrderLine per line)."""

    cart_id: UUID
    customer_id: UUID
    items: tuple[CheckoutLine, ...]
    total_amount: Decimal
    currency: str
