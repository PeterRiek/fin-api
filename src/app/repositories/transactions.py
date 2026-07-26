from collections import defaultdict
from datetime import datetime

from app.models import (
    Account,
    Category,
    Contribution,
    Person,
    SpaceUser,
    Transaction,
    TransactionCategory,
)
from app.repositories.base import BaseRepository
from app.schemas import (
    CategoryOut,
    ContributionDetailOut,
    TransactionCreate,
    TransactionDetailOut,
    TransactionOut,
)


class TransactionRepository(BaseRepository):
    def _to_details(self, s, transactions: list[Transaction]) -> list[TransactionDetailOut]:
        if not transactions:
            return []
        transaction_ids = [t.id for t in transactions]

        contribution_rows = (
            s.query(Contribution, Person.name)
            .join(Account, Contribution.account_id == Account.id)
            .join(Person, Account.person_id == Person.id)
            .filter(Contribution.transaction_id.in_(transaction_ids))
            .all()
        )
        contributions_by_transaction: dict[int, list[ContributionDetailOut]] = (
            defaultdict(list)
        )
        for contribution, person_name in contribution_rows:
            contributions_by_transaction[contribution.transaction_id].append(
                ContributionDetailOut(
                    account_id=contribution.account_id,
                    person_name=person_name,
                    real_amount=contribution.real_amount,
                    liability_amount=contribution.liability_amount,
                )
            )

        category_rows = (
            s.query(TransactionCategory.transaction_id, Category)
            .join(Category, Category.id == TransactionCategory.category_id)
            .filter(TransactionCategory.transaction_id.in_(transaction_ids))
            .all()
        )
        categories_by_transaction: dict[int, list[CategoryOut]] = defaultdict(list)
        for transaction_id, category in category_rows:
            categories_by_transaction[transaction_id].append(
                CategoryOut.model_validate(category)
            )

        return [
            TransactionDetailOut(
                id=t.id,
                space_id=t.space_id,
                title=t.title,
                description=t.description,
                date=t.date,
                type=t.type,
                linked_transaction_id=t.linked_transaction_id,
                created_at=t.created_at,
                contributions=contributions_by_transaction.get(t.id, []),
                categories=categories_by_transaction.get(t.id, []),
            )
            for t in transactions
        ]

    def insert(self, data: TransactionCreate) -> TransactionOut:
        with self.session() as s:
            transaction = Transaction(
                space_id=data.space_id,
                title=data.title,
                description=data.description,
                date=data.date,
                type=data.type,
                created_at=datetime.now(),
            )
            s.add(transaction)
            s.flush()
            return TransactionOut.model_validate(transaction)

    def get(self, transaction_id: int) -> TransactionOut | None:
        with self.session() as s:
            row = s.query(Transaction).filter_by(id=transaction_id).first()
            return TransactionOut.model_validate(row) if row else None

    def get_all(self) -> list[TransactionOut]:
        with self.session() as s:
            rows = s.query(Transaction).all()
            return [TransactionOut.model_validate(r) for r in rows]

    def get_by_space(self, space_id: int) -> list[TransactionDetailOut]:
        with self.session() as s:
            rows = s.query(Transaction).filter_by(space_id=space_id).all()
            return self._to_details(s, rows)

    def get_by_account(self, account_id: int) -> list[TransactionDetailOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    Contribution,
                    Transaction.id == Contribution.transaction_id,
                )
                .filter(Contribution.account_id == account_id)
                .all()
            )
            return self._to_details(s, rows)

    def get_by_person(
        self, person_id: int, user_id: int
    ) -> list[TransactionDetailOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    Contribution,
                    Transaction.id == Contribution.transaction_id,
                )
                .join(Account, Contribution.account_id == Account.id)
                .join(SpaceUser, Transaction.space_id == SpaceUser.space_id)
                .filter(Account.person_id == person_id, SpaceUser.user_id == user_id)
                .all()
            )
            return self._to_details(s, rows)

    def update(
        self, transaction_id: int, data: TransactionCreate
    ) -> TransactionOut | None:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=transaction_id).first()
            if not transaction:
                return None
            transaction.space_id = data.space_id
            transaction.title = data.title
            transaction.description = data.description
            transaction.date = data.date
            transaction.type = data.type
            return TransactionOut.model_validate(transaction)

    def delete(self, transaction_id: int) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=transaction_id).first()
            if not transaction:
                return False
            linked_id = transaction.linked_transaction_id
            s.delete(transaction)
            if linked_id is not None:
                linked = s.query(Transaction).filter_by(id=linked_id).first()
                if linked:
                    s.delete(linked)
            return True
