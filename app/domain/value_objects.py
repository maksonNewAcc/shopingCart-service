"""Value Objects and strongly typed identifiers.

Spec: docs/architecture/aggregates-and-invariants.md, sections 2 and 3. Validation lives in
__post_init__ so it runs on every construction path (HTTP, dataclasses.replace, repository load).
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Self, final
from uuid import UUID, uuid4
from app.domain.exceptions import (
    CurrencyMismatchException,
    InvalidCurrencyException,
    InvalidMoneyException,
    InvalidQuantityException,
)

_CENT = Decimal("0.01")


# --- Strongly typed identifiers ---------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class CartId:
    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())


@final
@dataclass(frozen=True, slots=True)
class CustomerId:
    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())


@final
@dataclass(frozen=True, slots=True)
class ProductId:
    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())


# --- Value Objects ----------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise InvalidQuantityException(self.value)
        if not (1 <= self.value <= 99):
            raise InvalidQuantityException(self.value)

    def increase(self, by: "Quantity") -> "Quantity":
        return Quantity(self.value + by.value)


@final
@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise InvalidMoneyException(self.amount)
        if self.amount < 0:
            raise InvalidMoneyException(self.amount)
        if (
            not isinstance(self.currency, str)
            or len(self.currency) != 3
            or not (self.currency.isascii() and self.currency.isalpha())
        ):
            raise InvalidCurrencyException(self.currency)
        object.__setattr__(self, "currency", self.currency.upper())
        object.__setattr__(self, "amount", self.amount.quantize(_CENT, rounding=ROUND_HALF_EVEN))

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchException(self.currency, other.currency)
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, qty: Quantity) -> "Money":
        return Money(self.amount * qty.value, self.currency)
