from dataclasses import asdict
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session
from app.application.cart_service import ShoppingCartApplicationService
from app.infrastructure.database import get_session
from app.infrastructure.postgres_cart_repo import PostgresShoppingCartRepository
from app.presentation.contracts import AddCartItemRequest, CreateCartRequest

router = APIRouter(prefix="/api/carts", tags=["ShoppingCart"])


def get_cart_service(session: Session = Depends(get_session)) -> ShoppingCartApplicationService:
    return ShoppingCartApplicationService(PostgresShoppingCartRepository(session))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_cart(
    payload: CreateCartRequest,
    request: Request,
    response: Response,
    service: ShoppingCartApplicationService = Depends(get_cart_service),
):
    cart_dto = service.create_cart(payload.customer_id)
    response.headers["Location"] = str(request.url_for("get_cart", cart_id=cart_dto.cart_id))
    return asdict(cart_dto)


@router.get("/{cart_id}", name="get_cart")
def get_cart(
    cart_id: UUID,
    service: ShoppingCartApplicationService = Depends(get_cart_service),
):
    return asdict(service.get_cart_summary(cart_id))


@router.post("/{cart_id}/items")
def add_item_to_cart(
    cart_id: UUID,
    payload: AddCartItemRequest,
    service: ShoppingCartApplicationService = Depends(get_cart_service),
):
    dto = service.add_item_to_cart(
        cart_id=cart_id,
        product_id=payload.product_id,
        unit_price=payload.unit_price,
        quantity=payload.quantity,
        currency=payload.currency,
    )
    return asdict(dto)


@router.delete("/{cart_id}/items/{product_id}")
def remove_item_from_cart(
    cart_id: UUID,
    product_id: UUID,
    service: ShoppingCartApplicationService = Depends(get_cart_service),
):
    return asdict(service.remove_item_from_cart(cart_id, product_id))


@router.post("/{cart_id}/checkout")
def initiate_checkout(
    cart_id: UUID,
    service: ShoppingCartApplicationService = Depends(get_cart_service),
):
    return asdict(service.initiate_checkout(cart_id))