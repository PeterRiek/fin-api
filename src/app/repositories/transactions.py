from datetime import datetime

from app.models import Account, AccountTransaction, SpaceUser, Transaction
from app.repositories.base import BaseRepository
from app.schemas import TransactionCreate, TransactionOut


class TransactionRepository(BaseRepository):
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

    def get_by_space(self, space_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = s.query(Transaction).filter_by(space_id=space_id).all()
            return [TransactionOut.model_validate(r) for r in rows]

    def get_by_account(self, account_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    AccountTransaction,
                    Transaction.id == AccountTransaction.transaction_id,
                )
                .filter(AccountTransaction.account_id == account_id)
                .all()
            )
            return [TransactionOut.model_validate(r) for r in rows]

    def get_by_person(self, person_id: int, user_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    AccountTransaction,
                    Transaction.id == AccountTransaction.transaction_id,
                )
                .join(Account, AccountTransaction.account_id == Account.id)
                .join(SpaceUser, Transaction.space_id == SpaceUser.space_id)
                .filter(Account.person_id == person_id, SpaceUser.user_id == user_id)
                .all()
            )
            return [TransactionOut.model_validate(r) for r in rows]

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
