from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    def list(self, db: Session, skip: int = 0, limit: int = 100) -> list[Product]:
        stmt = select(Product).order_by(Product.id).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, product_id: int) -> Product | None:
        return db.get(Product, product_id)

    def create(self, db: Session, payload: ProductCreate) -> Product:
        product = Product(**payload.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def update(self, db: Session, product: Product, payload: ProductUpdate) -> Product:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def delete(self, db: Session, product: Product) -> None:
        db.delete(product)
        db.commit()
