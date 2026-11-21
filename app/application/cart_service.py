from decimal import Decimal
from uuid import UUID
from app.application.dtos import CartItemDto, ShoppingCartSummaryDto
from app.application.repositories import ShoppingCartRepository
from app.domain.aggregates import ShoppingCart
from app.domain.exceptions import CartNotFoundException, EmptyCartCheckoutException
from app.domain.value_objects import CartId, CustomerId, Money, ProductId, Quantity


class ShoppingCartApplicationService:
    def __init__(self, repository: ShoppingCartRepository) -> None:
        self._repository = repository

    def create_cart(self, customer_id: UUID) -> ShoppingCartSummaryDto:
        cart = ShoppingCart.create(CustomerId(customer_id))
        self._repository.save(cart)
        return self._to_dto(cart)

    def get_cart_summary(self, cart_id: UUID) -> ShoppingCartSummaryDto:
        cart = self._get_existing_cart(cart_id)
        return self._to_dto(cart)

    def add_item_to_cart(
        self,
        cart_id: UUID,
        product_id: UUID,
        unit_price: Decimal,
        quantity: int,
        currency: str = "PLN",
    ) -> ShoppingCartSummaryDto:
        cart = self._get_existing_cart(cart_id)
        cart.add_item_to_cart(
            product_id=ProductId(product_id),
            unit_price=Money(unit_price, currency),
            quantity=Quantity(quantity),
        )
        self._repository.save(cart)
        return self._to_dto(cart)

    def remove_item_from_cart(self, cart_id: UUID, product_id: UUID) -> ShoppingCartSummaryDto:
        cart = self._get_existing_cart(cart_id)
        cart.remove_item_from_cart(ProductId(product_id))
        self._repository.save(cart)
        return self._to_dto(cart)

    def initiate_checkout(self, cart_id: UUID) -> ShoppingCartSummaryDto:
        cart = self._get_existing_cart(cart_id)
        cart.initiate_checkout()
        self._repository.save(cart)
        return self._to_dto(cart)

    def _get_existing_cart(self, cart_id: UUID) -> ShoppingCart:
        cart = self._repository.get_by_id(CartId(cart_id))
        if cart is None:
            raise CartNotFoundException(cart_id)
        return cart

    @staticmethod
    def _to_dto(cart: ShoppingCart) -> ShoppingCartSummaryDto:
        try:
            total = cart.calculate_total()
            total_amount = total.amount
            currency = total.currency
        except EmptyCartCheckoutException:
            total_amount = Decimal("0.00")
            currency = "PLN"

        return ShoppingCartSummaryDto(
            cart_id=cart.id.value,
            customer_id=cart.customer_id.value,
            status=cart.status.value,
            items=tuple(
                CartItemDto(
                    product_id=i.product_id.value,
                    unit_price=i.unit_price.amount,
                    quantity=i.quantity.value,
                    subtotal=i.subtotal.amount,
                )
                for i in cart.items
            ),
            order_total=total_amount,
            currency=currency,
        )