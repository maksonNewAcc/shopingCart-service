from uuid import UUID
from pydantic import BaseModel, StrictInt


class CreateCartRequest(BaseModel):
    customer_id: UUID


class AddCartItemRequest(BaseModel):
    product_id: UUID
    quantity: StrictInt  # rejects true/false and "2"; range is checked by Quantity