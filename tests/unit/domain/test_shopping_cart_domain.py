# tests/unit/domain/test_shopping_cart_domain.py
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.aggregates import CartStatus, ShoppingCart
from app.domain.events import CartItemAdded, CartItemRemoved, CheckoutInitiated
from app.domain.exceptions import (
    CartAlreadyCheckedOutException,
    CartItemNotFoundException,
    CurrencyMismatchException,
    EmptyCartCheckoutException,
    InvalidPriceException,
    InvalidQuantityException,
)
from app.domain.value_objects import CustomerId, Money, ProductId, Quantity


def test_add_item_when_unit_price_is_zero_throws_invalid_price_exception():
    # Arrange
    cart = ShoppingCart.create(CustomerId.new())

    # Act & Assert
    with pytest.raises(InvalidPriceException) as exc_info:
        cart.add_item_to_cart(
            product_id=ProductId.new(),
            unit_price=Money(Decimal("0.00"), "PLN"),
            quantity=Quantity(1),
        )

    assert exc_info.value.code == "cart.invalid_price"
    assert exc_info.value.attempted_price == Decimal("0.00")
    assert cart.items == ()


def test_add_item_when_valid_product_provided_adds_item_and_calculates_total():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    product_id = ProductId(uuid4())

    # Act
    cart.add_item_to_cart(product_id, Money(Decimal("120.50"), "PLN"), Quantity(2))

    # Assert
    assert len(cart.items) == 1
    assert cart.calculate_total() == Money(Decimal("241.00"), "PLN")
    assert isinstance(cart.domain_events[-1], CartItemAdded)


def test_add_item_when_same_product_added_twice_merges_quantity_instead_of_duplicating():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    product_id = ProductId(uuid4())
    cart.add_item_to_cart(product_id, Money(Decimal("300.00"), "PLN"), Quantity(1))

    # Act
    cart.add_item_to_cart(product_id, Money(Decimal("300.00"), "PLN"), Quantity(2))

    # Assert
    assert len(cart.items) == 1
    assert cart.items[0].quantity == Quantity(3)
    assert cart.calculate_total() == Money(Decimal("900.00"), "PLN")


def test_add_item_when_merged_quantity_exceeds_max_99_throws_invalid_quantity_exception():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    product_id = ProductId(uuid4())
    cart.add_item_to_cart(product_id, Money(Decimal("10.00"), "PLN"), Quantity(90))

    # Act & Assert
    with pytest.raises(InvalidQuantityException) as exc_info:
        cart.add_item_to_cart(product_id, Money(Decimal("10.00"), "PLN"), Quantity(10))

    assert exc_info.value.code == "cart.invalid_quantity"
    assert exc_info.value.attempted_quantity == 100


def test_remove_item_when_product_exists_removes_line_and_records_event():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    product_id = ProductId(uuid4())
    cart.add_item_to_cart(product_id, Money(Decimal("50.00"), "PLN"), Quantity(1))

    # Act
    cart.remove_item_from_cart(product_id)

    # Assert
    assert len(cart.items) == 0
    assert isinstance(cart.domain_events[-1], CartItemRemoved)


def test_remove_item_when_product_missing_throws_cart_item_not_found_exception():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    missing_product_id = ProductId(uuid4())

    # Act & Assert
    with pytest.raises(CartItemNotFoundException) as exc_info:
        cart.remove_item_from_cart(missing_product_id)

    assert exc_info.value.code == "cart.item_not_found"
    assert exc_info.value.cart_id == cart.id.value
    assert exc_info.value.product_id == missing_product_id.value


def test_initiate_checkout_when_cart_is_empty_throws_empty_cart_checkout_exception():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))

    # Act & Assert
    with pytest.raises(EmptyCartCheckoutException) as exc_info:
        cart.initiate_checkout()

    assert exc_info.value.code == "cart.empty_checkout"
    assert exc_info.value.cart_id == cart.id.value


def test_initiate_checkout_when_cart_has_items_transitions_status_and_blocks_mutations():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    cart.add_item_to_cart(ProductId(uuid4()), Money(Decimal("180.00"), "PLN"), Quantity(1))

    # Act
    cart.initiate_checkout()

    # Assert
    assert cart.status == CartStatus.CHECKED_OUT
    assert isinstance(cart.domain_events[-1], CheckoutInitiated)

    with pytest.raises(CartAlreadyCheckedOutException) as exc_info:
        cart.add_item_to_cart(ProductId(uuid4()), Money(Decimal("20.00"), "PLN"), Quantity(1))

    assert exc_info.value.code == "cart.already_checked_out"
    assert exc_info.value.cart_id == cart.id.value

def test_add_item_when_currency_differs_from_existing_items_throws_and_leaves_cart_unchanged():
    # Arrange
    cart = ShoppingCart.create(CustomerId(uuid4()))
    cart.add_item_to_cart(ProductId(uuid4()), Money(Decimal("10.00"), "EUR"), Quantity(1))
    events_before = len(cart.domain_events)

    # Act & Assert
    with pytest.raises(CurrencyMismatchException) as exc_info:
        cart.add_item_to_cart(ProductId(uuid4()), Money(Decimal("10.00"), "PLN"), Quantity(1))

    assert exc_info.value.code == "money.currency_mismatch"
    assert exc_info.value.expected_currency == "EUR"
    assert exc_info.value.actual_currency == "PLN"
    assert len(cart.items) == 1
    assert len(cart.domain_events) == events_before


def test_calculate_total_when_cart_is_empty_returns_zero_money():
    cart = ShoppingCart.create(CustomerId.new())

    assert cart.calculate_total() == Money(Decimal("0.00"), "PLN")


def test_initiate_checkout_records_event_with_lines_and_total():
    # Arrange
    cart = ShoppingCart.create(CustomerId.new())
    first, second = ProductId.new(), ProductId.new()
    cart.add_item_to_cart(first, Money(Decimal("100.00"), "PLN"), Quantity(2))
    cart.add_item_to_cart(second, Money(Decimal("49.99"), "PLN"), Quantity(1))

    # Act
    cart.initiate_checkout()

    # Assert
    event = cart.domain_events[-1]
    assert isinstance(event, CheckoutInitiated)
    assert event.cart_id == cart.id.value
    assert event.customer_id == cart.customer_id.value
    assert event.total_amount == Decimal("249.99")
    assert event.currency == "PLN"
    assert {(l.product_id, l.quantity, l.unit_price) for l in event.items} == {
        (first.value, 2, Decimal("100.00")),
        (second.value, 1, Decimal("49.99")),
    }


def test_remove_item_when_cart_checked_out_throws_already_checked_out():
    # Arrange
    cart = ShoppingCart.create(CustomerId.new())
    product_id = ProductId.new()
    cart.add_item_to_cart(product_id, Money(Decimal("10.00"), "PLN"), Quantity(1))
    cart.initiate_checkout()

    # Act & Assert
    with pytest.raises(CartAlreadyCheckedOutException):
        cart.remove_item_from_cart(product_id)

    assert len(cart.items) == 1
