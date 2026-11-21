from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class CreateCartRequest(BaseModel):
    customer_id: UUID


class AddCartItemRequest(BaseModel):
    product_id: UUID
    unit_price: Decimal
    quantity: int
    currency: str = "PLN"