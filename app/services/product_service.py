from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> list[Product]:
        return self.repository.list(db, skip=skip, limit=limit)

    def get_product(self, db: Session, product_id: int) -> Product:
        product = self.repository.get(db, product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def create_product(self, db: Session, payload: ProductCreate) -> Product:
        try:
            return self.repository.create(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="product code must be unique",
            ) from exc

    def update_product(self, db: Session, product_id: int, payload: ProductUpdate) -> Product:
        product = self.get_product(db, product_id)
        try:
            return self.repository.update(db, product, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="product code must be unique",
            ) from exc

    def delete_product(self, db: Session, product_id: int) -> None:
        product = self.get_product(db, product_id)
        self.repository.delete(db, product)
