from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.infrastructure.database import get_session
from app.infrastructure.models import Product

# Product Catalog is a read model in the Shopping Cart context: browse only, no writes.
router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[Product])
def list_products(session: Session = Depends(get_session)):
    return session.exec(select(Product).where(Product.is_deleted == False)).all()  # noqa: E712


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: UUID, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product or product.is_deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
