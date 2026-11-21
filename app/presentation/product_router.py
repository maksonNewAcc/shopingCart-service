from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.infrastructure.database import get_session
from app.infrastructure.models import Product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[Product])
def list_products(session: Session = Depends(get_session)):
    return session.exec(select(Product)).all()


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: UUID, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: Product, session: Session = Depends(get_session)):
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: UUID,
    updated_data: Product,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_data = updated_data.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: UUID, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()
    return {"message": "Product successfully deleted"}