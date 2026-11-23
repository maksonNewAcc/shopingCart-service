from abc import ABC
from decimal import Decimal
from typing import final
from uuid import UUID


class DomainException(Exception, ABC):
    def __init__(self, code: str, message: str) -> None:
        if type(self) is DomainException:
            raise TypeError("DomainException is abstract and cannot be instantiated directly.")
        self.code = code
        super().__init__(message)


# --- Value objects ---------------------------------------------------------


@final
class InvalidMoneyException(DomainException):
    def __init__(self, attempted_amount: object) -> None:
        self.attempted_amount = attempted_amount
        super().__init__(
            code="money.invalid_amount",
            message=f"Money amount must be a finite, non-negative Decimal, but was {attempted_amount!r}.",
        )


@final
class InvalidCurrencyException(DomainException):
    def __init__(self, attempted_currency: object) -> None:
        self.attempted_currency = attempted_currency
        super().__init__(
            code="money.invalid_currency",
            message=f"Currency must be a 3-letter ISO 4217 code, but was {attempted_currency!r}.",
        )


@final
class CurrencyMismatchException(DomainException):
    def __init__(self, expected_currency: str, actual_currency: str) -> None:
        self.expected_currency = expected_currency
        self.actual_currency = actual_currency
        super().__init__(
            code="money.currency_mismatch",
            message=f"Cannot combine {expected_currency} with {actual_currency}.",
        )


@final
class InvalidQuantityException(DomainException):
    def __init__(self, attempted_quantity: object) -> None:
        self.attempted_quantity = attempted_quantity
        super().__init__(
            code="cart.invalid_quantity",
            message=f"Item quantity must be an integer between 1 and 99, but was {attempted_quantity!r}.",
        )


# --- ShoppingCart aggregate ------------------------------------------------


@final
class InvalidPriceException(DomainException):
    def __init__(self, attempted_price: Decimal, currency: str) -> None:
        self.attempted_price = attempted_price
        self.currency = currency
        super().__init__(
            code="cart.invalid_price",
            message=f"Unit price must be greater than zero, but was {attempted_price} {currency}.",
        )


@final
class CartAlreadyCheckedOutException(DomainException):
    def __init__(self, cart_id: UUID) -> None:
        self.cart_id = cart_id
        super().__init__(
            code="cart.already_checked_out",
            message=f"ShoppingCart {cart_id} is already checked out and cannot be modified.",
        )


@final
class EmptyCartCheckoutException(DomainException):
    def __init__(self, cart_id: UUID) -> None:
        self.cart_id = cart_id
        super().__init__(
            code="cart.empty_checkout",
            message=f"Cannot initiate checkout on empty ShoppingCart {cart_id}.",
        )


@final
class CartItemNotFoundException(DomainException):
    def __init__(self, cart_id: UUID, product_id: UUID) -> None:
        self.cart_id = cart_id
        self.product_id = product_id
        super().__init__(
            code="cart.item_not_found",
            message=f"Product {product_id} was not found in ShoppingCart {cart_id}.",
        )


@final
class CartNotFoundException(DomainException):
    def __init__(self, cart_id: UUID) -> None:
        self.cart_id = cart_id
        super().__init__(
            code="cart.not_found",
            message=f"ShoppingCart {cart_id} was not found.",
        )


@final
class ProductNotFoundException(DomainException):
    def __init__(self, product_id: UUID) -> None:
        self.product_id = product_id
        super().__init__(
            code="cart.product_not_found",
            message=f"Product {product_id} was not found in the product catalog.",
        )
