from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
from app.domain.exceptions import InvalidPriceException, InvalidQuantityException


@dataclass(frozen=True)
class CartId:
    value: UUID


@dataclass(frozen=True)
class CustomerId:
    value: UUID


@dataclass(frozen=True)
class ProductId:
    value: UUID


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if not (1 <= self.value <= 99):
            raise InvalidQuantityException(self.value)

    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "PLN"

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0.00"):
            raise InvalidPriceException(self.amount, self.currency)
        if len(self.currency) != 3 or not self.currency.isupper():
            raise InvalidPriceException(self.amount, self.currency)

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvalidPriceException(self.amount, self.currency)
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, qty: Quantity) -> "Money":
        return Money(self.amount * qty.value, self.currency)