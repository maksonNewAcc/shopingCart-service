# tests/unit/application/test_shopping_cart_service.py
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.cart_service import ShoppingCartApplicationService
from app.domain.aggregates import ShoppingCart
from app.domain.exceptions import CartNotFoundException, EmptyCartCheckoutException
from app.domain.value_objects import CustomerId, Money, ProductId, Quantity


def test_create_cart_when_valid_customer_id_creates_and_saves_cart():
    # Arrange
    repo = MagicMock()
    sut = ShoppingCartApplicationService(repo)
    customer_id = uuid4()

    # Act
    result = sut.create_cart(customer_id)

    # Assert
    assert result.customer_id == customer_id
    assert result.items == ()
    assert result.order_total == Decimal("0.00")
    repo.save.assert_called_once()


def test_add_item_when_cart_exists_updates_cart_and_calls_save():
    # Arrange
    existing_cart = ShoppingCart.create(CustomerId(uuid4()))
    repo = MagicMock()
    repo.get_by_id.return_value = existing_cart
    sut = ShoppingCartApplicationService(repo)

    # Act
    result = sut.add_item_to_cart(
        cart_id=existing_cart.id.value,
        product_id=uuid4(),
        unit_price=Decimal("350.00"),
        quantity=2,
    )

    # Assert
    assert len(result.items) == 1
    assert result.order_total == Decimal("700.00")
    repo.save.assert_called_once_with(existing_cart)


def test_initiate_checkout_when_cart_does_not_exist_throws_not_found_and_never_saves():
    # Arrange
    missing_cart_id = uuid4()
    repo = MagicMock()
    repo.get_by_id.return_value = None
    sut = ShoppingCartApplicationService(repo)

    # Act & Assert
    with pytest.raises(CartNotFoundException) as exc_info:
        sut.initiate_checkout(missing_cart_id)

    assert exc_info.value.code == "cart.not_found"
    assert exc_info.value.cart_id == missing_cart_id
    repo.save.assert_not_called()


def test_initiate_checkout_when_domain_rule_violated_propagates_and_never_saves():
    # Arrange
    empty_cart = ShoppingCart.create(CustomerId(uuid4()))
    repo = MagicMock()
    repo.get_by_id.return_value = empty_cart
    sut = ShoppingCartApplicationService(repo)

    # Act & Assert
    with pytest.raises(EmptyCartCheckoutException) as exc_info:
        sut.initiate_checkout(empty_cart.id.value)

    assert exc_info.value.code == "cart.empty_checkout"
    repo.save.assert_not_called()


def test_remove_item_when_cart_exists_removes_product_and_saves():
    # Arrange
    product_id = uuid4()
    existing_cart = ShoppingCart.create(CustomerId(uuid4()))
    existing_cart.add_item_to_cart(ProductId(product_id), Money(Decimal("45.00"), "PLN"), Quantity(1))

    repo = MagicMock()
    repo.get_by_id.return_value = existing_cart
    sut = ShoppingCartApplicationService(repo)

    # Act
    result = sut.remove_item_from_cart(existing_cart.id.value, product_id)

    # Assert
    assert len(result.items) == 0
    assert result.order_total == Decimal("0.00")
    repo.save.assert_called_once_with(existing_cart)