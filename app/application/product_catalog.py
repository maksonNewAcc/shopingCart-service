from typing import Protocol
from app.domain.value_objects import Money, ProductId


class ProductCatalog(Protocol):
    """Product Catalog read model: the only source of truth for item prices in the cart."""

    def get_unit_price(self, product_id: ProductId) -> Money | None: ...
