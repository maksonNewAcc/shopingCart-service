from decimal import Decimal
from sqlmodel import Session
from app.domain.value_objects import Money, ProductId
from app.infrastructure.models import Product

# The product table has no currency column yet; all catalog prices are in PLN.
CATALOG_CURRENCY = "PLN"


class PostgresProductCatalog:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_unit_price(self, product_id: ProductId) -> Money | None:
        product = self._session.get(Product, product_id.value)
        if product is None or product.is_deleted:
            return None
        return Money(Decimal(str(product.price)), CATALOG_CURRENCY)
