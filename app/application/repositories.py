from typing import Protocol
from app.domain.aggregates import ShoppingCart
from app.domain.value_objects import CartId


class ShoppingCartRepository(Protocol):
    def get_by_id(self, cart_id: CartId) -> ShoppingCart | None: ...
    def save(self, cart: ShoppingCart) -> None: ...