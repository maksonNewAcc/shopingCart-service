from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.exceptions import (
    CartAlreadyCheckedOutException,
    CartItemNotFoundException,
    CartNotFoundException,
    DomainException,
    EmptyCartCheckoutException,
    InvalidPriceException,
    InvalidQuantityException,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CartNotFoundException)
    async def not_found_handler(request: Request, exc: CartNotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"code": exc.code, "message": str(exc), "cartId": str(exc.cart_id)},
        )

    @app.exception_handler(InvalidQuantityException)
    @app.exception_handler(InvalidPriceException)
    async def bad_request_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": str(exc)},
        )

    @app.exception_handler(EmptyCartCheckoutException)
    @app.exception_handler(CartAlreadyCheckedOutException)
    @app.exception_handler(CartItemNotFoundException)
    async def unprocessable_entity_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": str(exc)},
        )

    @app.exception_handler(DomainException)
    async def fallback_domain_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": str(exc)},
        )