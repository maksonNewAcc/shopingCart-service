# tests/unit/domain/test_value_objects.py
# Spec: docs/architecture/aggregates-and-invariants.md, sections 2 and 3.
import dataclasses
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.exceptions import (
    CurrencyMismatchException,
    InvalidCurrencyException,
    InvalidMoneyException,
    InvalidQuantityException,
)
from app.domain.value_objects import CartId, CustomerId, Money, ProductId, Quantity


# --- Money -------------------------------------------------------------------

@pytest.mark.parametrize("invalid_amount", [19.99, 10, True, "19.99"])
def test_money_when_amount_is_not_decimal_throws_invalid_money_exception(invalid_amount: object):
    with pytest.raises(InvalidMoneyException) as exc_info:
        Money(invalid_amount, "PLN")  # type: ignore[arg-type]

    assert exc_info.value.code == "money.invalid_amount"


@pytest.mark.parametrize("invalid_amount", [Decimal("-0.01"), Decimal("-19.99"), Decimal("NaN"), Decimal("Infinity")])
def test_money_when_amount_is_negative_or_not_finite_throws_invalid_money_exception(invalid_amount: Decimal):
    with pytest.raises(InvalidMoneyException):
        Money(invalid_amount, "PLN")


def test_money_when_amount_is_zero_is_valid():
    assert Money(Decimal("0"), "PLN").amount == Decimal("0.00")


@pytest.mark.parametrize("invalid_currency", ["zl", "PLN1", "", "P1N", 985])
def test_money_when_currency_is_not_three_letters_throws_invalid_currency_exception(invalid_currency: object):
    with pytest.raises(InvalidCurrencyException) as exc_info:
        Money(Decimal("1.00"), invalid_currency)  # type: ignore[arg-type]

    assert exc_info.value.code == "money.invalid_currency"


def test_money_normalises_currency_to_upper_case():
    assert Money(Decimal("1.00"), "pln") == Money(Decimal("1.00"), "PLN")


@pytest.mark.parametrize(
    ("raw", "rounded"),
    [(Decimal("0.125"), Decimal("0.12")), (Decimal("0.135"), Decimal("0.14")), (Decimal("7"), Decimal("7.00"))],
)
def test_money_rounds_amount_to_cents_with_half_even(raw: Decimal, rounded: Decimal):
    money = Money(raw, "PLN")

    assert money.amount == rounded
    assert money.amount.as_tuple().exponent == -2


def test_money_add_when_same_currency_returns_new_sum():
    a = Money(Decimal("10.50"), "PLN")
    b = Money(Decimal("0.25"), "PLN")

    result = a.add(b)

    assert result == Money(Decimal("10.75"), "PLN")
    assert result is not a and result is not b


def test_money_add_when_currencies_differ_throws_currency_mismatch_exception():
    with pytest.raises(CurrencyMismatchException) as exc_info:
        Money(Decimal("1.00"), "PLN").add(Money(Decimal("1.00"), "EUR"))

    assert exc_info.value.code == "money.currency_mismatch"
    assert exc_info.value.expected_currency == "PLN"
    assert exc_info.value.actual_currency == "EUR"


def test_money_multiply_by_quantity_returns_line_total():
    assert Money(Decimal("120.50"), "PLN").multiply(Quantity(2)) == Money(Decimal("241.00"), "PLN")


# --- Quantity ----------------------------------------------------------------

@pytest.mark.parametrize("invalid_quantity", [0, -5, 100])
def test_quantity_when_out_of_range_throws_invalid_quantity_exception(invalid_quantity: int):
    with pytest.raises(InvalidQuantityException) as exc_info:
        Quantity(invalid_quantity)

    assert exc_info.value.code == "cart.invalid_quantity"
    assert exc_info.value.attempted_quantity == invalid_quantity


@pytest.mark.parametrize("invalid_quantity", [True, False, 1.0, "2"])
def test_quantity_when_bool_or_not_int_throws_invalid_quantity_exception(invalid_quantity: object):
    with pytest.raises(InvalidQuantityException):
        Quantity(invalid_quantity)  # type: ignore[arg-type]


def test_quantity_increase_returns_new_quantity():
    assert Quantity(2).increase(Quantity(3)) == Quantity(5)


def test_quantity_increase_beyond_99_throws_invalid_quantity_exception():
    with pytest.raises(InvalidQuantityException) as exc_info:
        Quantity(98).increase(Quantity(5))

    assert exc_info.value.attempted_quantity == 103


# --- Immutability and strongly typed identifiers -----------------------------

@pytest.mark.parametrize(
    "value_object",
    [Money(Decimal("1.00"), "PLN"), Quantity(1), CartId.new(), CustomerId.new(), ProductId.new()],
)
def test_value_objects_are_frozen_and_slotted(value_object: object):
    assert not hasattr(value_object, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(value_object, dataclasses.fields(value_object)[0].name, None)


def test_ids_new_generates_distinct_uuids():
    assert CartId.new() != CartId.new()


def test_ids_of_different_types_are_never_equal_for_same_uuid():
    raw = uuid4()

    assert CustomerId(raw) != ProductId(raw)
    assert CartId(raw) != CustomerId(raw)
    assert CartId(raw) == CartId(raw)
