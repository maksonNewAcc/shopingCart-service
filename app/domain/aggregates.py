from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from app.domain.events import CartItemAdded, CartItemRemoved, CheckoutInitiated, DomainEvent
from app.domain.exceptions import (
    CartAlreadyCheckedOutException,
    CartItemNotFoundException,
    EmptyCartCheckoutException,
)
from app.domain.value_objects import CartId, CustomerId, Money, ProductId, Quantity


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"


@dataclass(frozen=True)
class CartItem:
    product_id: ProductId
    unit_price: Money
    quantity: Quantity

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
        return cls(id=CartId(uuid4()), customer_id=customer_id)

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
        if product_id in self._items:
            existing = self._items[product_id]
            self._items[product_id] = CartItem(
                product_id=product_id,
                unit_price=unit_price,
                quantity=existing.quantity + quantity,
            )
        else:
            self._items[product_id] = CartItem(product_id, unit_price, quantity)

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
        self._status = CartStatus.CHECKED_OUT
        total = self.calculate_total()
        self._domain_events.append(
            CheckoutInitiated(
                cart_id=self.id.value,
                customer_id=self.customer_id.value,
                total_amount=total.amount,
                currency=total.currency,
            )
        )

    def calculate_total(self, currency: str = "PLN") -> Money:
        if not self._items:
            raise EmptyCartCheckoutException(self.id.value)
        iterator = iter(self._items.values())
        total = next(iterator).subtotal
        for item in iterator:
            total = total + item.subtotal
        return total

    def _ensure_active(self) -> None:
        if self._status != CartStatus.ACTIVE:
            raise CartAlreadyCheckedOutException(self.id.value)