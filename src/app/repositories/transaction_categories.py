from app.models import Category, Transaction, TransactionCategory
from app.repositories.base import BaseRepository
from app.schemas import (
    CategoryOut,
    TransactionCategoryCreate,
    TransactionCategoryOut,
    TransactionOut,
)


class TransactionCategoryRepository(BaseRepository):
    def insert(self, data: TransactionCategoryCreate) -> TransactionCategoryOut:
        with self.session() as s:
            transaction_category = TransactionCategory(
                transaction_id=data.transaction_id,
                category_id=data.category_id,
            )
            s.add(transaction_category)
            s.flush()
            return TransactionCategoryOut.model_validate(transaction_category)

    def get(
        self, transaction_id: int, category_id: int
    ) -> TransactionCategoryOut | None:
        with self.session() as s:
            row = (
                s.query(TransactionCategory)
                .filter_by(transaction_id=transaction_id, category_id=category_id)
                .first()
            )
            return TransactionCategoryOut.model_validate(row) if row else None

    def get_categories_by_transaction(self, transaction_id: int) -> list[CategoryOut]:
        with self.session() as s:
            rows = (
                s.query(Category)
                .join(
                    TransactionCategory, Category.id == TransactionCategory.category_id
                )
                .filter(TransactionCategory.transaction_id == transaction_id)
                .all()
            )
            return [CategoryOut.model_validate(r) for r in rows]

    def get_transactions_by_category(self, category_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    TransactionCategory,
                    Transaction.id == TransactionCategory.transaction_id,
                )
                .filter(TransactionCategory.category_id == category_id)
                .all()
            )
            return [TransactionOut.model_validate(r) for r in rows]

    def delete(self, transaction_id: int, category_id: int) -> bool:
        with self.session() as s:
            transaction_category = (
                s.query(TransactionCategory)
                .filter_by(transaction_id=transaction_id, category_id=category_id)
                .first()
            )
            if not transaction_category:
                return False
            s.delete(transaction_category)
            return True
