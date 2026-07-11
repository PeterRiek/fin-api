from app.models import Account, AccountTransaction, Person
from app.repositories.base import BaseRepository
from app.schemas import ContributionCreate, ContributionDetailOut, ContributionOut


class ContributionRepository(BaseRepository):
    def insert(self, data: ContributionCreate) -> ContributionOut:
        with self.session() as s:
            account_transaction = AccountTransaction(
                account_id=data.account_id,
                transaction_id=data.transaction_id,
                amount_requested=data.amount_requested,
                amount_paid=data.amount_paid,
                is_initial=data.is_initial,
            )
            s.add(account_transaction)
            s.flush()
            return ContributionOut.model_validate(account_transaction)

    def get(self, account_id: int, transaction_id: int) -> ContributionOut | None:
        with self.session() as s:
            row = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            return ContributionOut.model_validate(row) if row else None

    def get_all(self) -> list[ContributionOut]:
        with self.session() as s:
            rows = s.query(AccountTransaction).all()
            return [ContributionOut.model_validate(r) for r in rows]

    def get_by_transaction(self, transaction_id: int) -> list[ContributionOut]:
        with self.session() as s:
            rows = (
                s.query(AccountTransaction)
                .filter_by(transaction_id=transaction_id)
                .all()
            )
            return [ContributionOut.model_validate(r) for r in rows]

    def get_details_by_transaction(
        self, transaction_id: int
    ) -> list[ContributionDetailOut]:
        with self.session() as s:
            rows = (
                s.query(AccountTransaction, Person.name)
                .join(Account, AccountTransaction.account_id == Account.id)
                .join(Person, Account.person_id == Person.id)
                .filter(AccountTransaction.transaction_id == transaction_id)
                .all()
            )
            return [
                ContributionDetailOut(
                    account_id=contribution.account_id,
                    person_name=person_name,
                    amount_requested=contribution.amount_requested,
                    amount_paid=contribution.amount_paid,
                    is_initial=contribution.is_initial,
                )
                for contribution, person_name in rows
            ]

    def update(
        self, account_id: int, transaction_id: int, data: ContributionCreate
    ) -> ContributionOut | None:
        with self.session() as s:
            account_transaction = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            if not account_transaction:
                return None
            account_transaction.amount_requested = data.amount_requested
            account_transaction.amount_paid = data.amount_paid
            account_transaction.is_initial = data.is_initial
            return ContributionOut.model_validate(account_transaction)

    def delete(self, account_id: int, transaction_id: int) -> bool:
        with self.session() as s:
            account_transaction = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            if not account_transaction:
                return False
            s.delete(account_transaction)
            return True
