from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CartItemDto:
    product_id: UUID
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


@dataclass(frozen=True)
class ShoppingCartSummaryDto:
    cart_id: UUID
    customer_id: UUID
    status: str
    items: tuple[CartItemDto, ...]
    order_total: Decimal
    currency: str