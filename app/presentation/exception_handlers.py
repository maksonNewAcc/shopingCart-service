from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.exceptions import DomainException


def register_exception_handlers(app: FastAPI) -> None:
    # Spec: every domain rule violation is mapped in one place to HTTP 422.
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": str(exc)},
        )
