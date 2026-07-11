from datetime import datetime

from app.models import Category
from app.repositories.base import BaseRepository
from app.schemas import CategoryCreate, CategoryOut


class CategoryRepository(BaseRepository):
    def insert(self, data: CategoryCreate) -> CategoryOut:
        with self.session() as s:
            category = Category(
                name=data.name,
                created_at=datetime.now(),
            )
            s.add(category)
            s.flush()
            return CategoryOut.model_validate(category)

    def get(self, category_id: int) -> CategoryOut | None:
        with self.session() as s:
            row = s.query(Category).filter_by(id=category_id).first()
            return CategoryOut.model_validate(row) if row else None

    def get_all(self) -> list[CategoryOut]:
        with self.session() as s:
            rows = s.query(Category).all()
            return [CategoryOut.model_validate(r) for r in rows]

    def update(self, category_id: int, data: CategoryCreate) -> CategoryOut | None:
        with self.session() as s:
            category = s.query(Category).filter_by(id=category_id).first()
            if not category:
                return None
            category.name = data.name
            return CategoryOut.model_validate(category)

    def delete(self, category_id: int) -> bool:
        with self.session() as s:
            category = s.query(Category).filter_by(id=category_id).first()
            if not category:
                return False
            s.delete(category)
            return True
