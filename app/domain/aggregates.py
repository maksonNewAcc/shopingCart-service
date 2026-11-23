from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import final
from app.domain.events import (
    CartItemAdded,
    CartItemRemoved,
    CheckoutInitiated,
    CheckoutLine,
    DomainEvent,
)
from app.domain.exceptions import (
    CartAlreadyCheckedOutException,
    CartItemNotFoundException,
    CurrencyMismatchException,
    EmptyCartCheckoutException,
    InvalidPriceException,
)
from app.domain.value_objects import CartId, CustomerId, Money, ProductId, Quantity

# Currency reported for the total of a cart that has no items yet.
DEFAULT_CURRENCY = "PLN"


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"


@final
@dataclass(frozen=True, slots=True)
class CartItem:
    """Internal entity of ShoppingCart, identified inside the aggregate by ProductId."""

    product_id: ProductId
    unit_price: Money
    quantity: Quantity

    def __post_init__(self) -> None:
        # Money allows zero (totals); a sellable cart line does not.
        if self.unit_price.amount <= 0:
            raise InvalidPriceException(self.unit_price.amount, self.unit_price.currency)

    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass
class ShoppingCart:
    id: CartId
    customer_id: CustomerId
    _status: CartStatus = field(default=CartStatus.ACTIVE, repr=False)
    _items: dict[ProductId, CartItem] = field(default_factory=dict, repr=False)
    _domain_events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, customer_id: CustomerId) -> "ShoppingCart":
        return cls(id=CartId.new(), customer_id=customer_id)

    @property
    def status(self) -> CartStatus:
        return self._status

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(self._items.values())

    @property
    def domain_events(self) -> tuple[DomainEvent, ...]:
        return tuple(self._domain_events)

    def add_item_to_cart(self, product_id: ProductId, unit_price: Money, quantity: Quantity) -> None:
        self._ensure_active()
        self._ensure_same_currency(unit_price)
        existing = self._items.get(product_id)
        new_quantity = existing.quantity.increase(quantity) if existing else quantity
        self._items[product_id] = CartItem(product_id, unit_price, new_quantity)

        self._domain_events.append(
            CartItemAdded(
                cart_id=self.id.value,
                product_id=product_id.value,
                quantity=quantity.value,
                unit_price=unit_price.amount,
            )
        )

    def remove_item_from_cart(self, product_id: ProductId) -> None:
        self._ensure_active()
        if product_id not in self._items:
            raise CartItemNotFoundException(self.id.value, product_id.value)
        del self._items[product_id]
        self._domain_events.append(
            CartItemRemoved(cart_id=self.id.value, product_id=product_id.value)
        )

    def initiate_checkout(self) -> None:
        self._ensure_active()
        if not self._items:
            raise EmptyCartCheckoutException(self.id.value)
        total = self.calculate_total()  # may raise; state is changed only after it succeeds
        self._status = CartStatus.CHECKED_OUT
        self._domain_events.append(
            CheckoutInitiated(
                cart_id=self.id.value,
                customer_id=self.customer_id.value,
                items=tuple(
                    CheckoutLine(
                        product_id=i.product_id.value,
                        quantity=i.quantity.value,
                        unit_price=i.unit_price.amount,
                    )
                    for i in self._items.values()
                ),
                total_amount=total.amount,
                currency=total.currency,
            )
        )

    def calculate_total(self) -> Money:
        items = iter(self._items.values())
        first = next(items, None)
        if first is None:
            return Money(Decimal("0"), DEFAULT_CURRENCY)
        total = first.subtotal
        for item in items:
            total = total.add(item.subtotal)
        return total

    def _ensure_same_currency(self, unit_price: Money) -> None:
        existing = next(iter(self._items.values()), None)
        if existing is not None and existing.unit_price.currency != unit_price.currency:
            raise CurrencyMismatchException(existing.unit_price.currency, unit_price.currency)

    def _ensure_active(self) -> None:
        if self._status != CartStatus.ACTIVE:
            raise CartAlreadyCheckedOutException(self.id.value)
