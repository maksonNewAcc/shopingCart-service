from datetime import datetime, timezone
from sqlmodel import Session, delete, select
from app.domain.aggregates import CartItem, CartStatus, ShoppingCart
from app.domain.value_objects import CartId, CustomerId, Money, ProductId, Quantity
from app.infrastructure.models import CartItemTable, ShoppingCartTable


class PostgresShoppingCartRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, cart_id: CartId) -> ShoppingCart | None:
        cart_row = self._session.get(ShoppingCartTable, cart_id.value)
        if cart_row is None or cart_row.is_deleted:
            return None

        item_rows = self._session.exec(
            select(CartItemTable).where(CartItemTable.cart_id == cart_id.value)
        ).all()

        items = {
            ProductId(row.product_id): CartItem(
                product_id=ProductId(row.product_id),
                unit_price=Money(row.unit_price, row.currency),
                quantity=Quantity(row.quantity),
            )
            for row in item_rows
        }
        return ShoppingCart(
            id=CartId(cart_row.id),
            customer_id=CustomerId(cart_row.customer_id),
            _status=CartStatus(cart_row.status),
            _items=items,
        )

    def save(self, cart: ShoppingCart) -> None:
        cart_row = self._session.get(ShoppingCartTable, cart.id.value)
        if cart_row is None:
            cart_row = ShoppingCartTable(
                id=cart.id.value,
                customer_id=cart.customer_id.value,
                status=cart.status.value,
            )
            self._session.add(cart_row)
        else:
            cart_row.status = cart.status.value
            cart_row.updated_at = datetime.now(timezone.utc)

        self._session.exec(delete(CartItemTable).where(CartItemTable.cart_id == cart.id.value))
        for item in cart.items:
            self._session.add(
                CartItemTable(
                    cart_id=cart.id.value,
                    product_id=item.product_id.value,
                    unit_price=item.unit_price.amount,
                    currency=item.unit_price.currency,
                    quantity=item.quantity.value,
                )
            )
        self._session.commit()