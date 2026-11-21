from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class AuditBase(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None
    is_deleted: bool = Field(default=False)


class Product(AuditBase, table=True):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0


class ShoppingCartTable(AuditBase, table=True):
    __tablename__ = "shopping_carts"
    customer_id: UUID = Field(index=True)
    status: str = Field(default="ACTIVE")


class CartItemTable(AuditBase, table=True):
    __tablename__ = "cart_items"
    cart_id: UUID = Field(foreign_key="shopping_carts.id", index=True)
    product_id: UUID = Field(index=True)
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = Field(default="PLN", max_length=3)
    quantity: int