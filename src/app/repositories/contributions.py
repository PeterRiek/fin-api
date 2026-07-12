from app.models import Account, Contribution, Person
from app.repositories.base import BaseRepository
from app.schemas import ContributionCreate, ContributionDetailOut, ContributionOut


class ContributionRepository(BaseRepository):
    def insert(self, data: ContributionCreate) -> ContributionOut:
        with self.session() as s:
            contribution = Contribution(
                account_id=data.account_id,
                transaction_id=data.transaction_id,
                real_amount=data.real_amount,
                liability_amount=data.liability_amount,
            )
            s.add(contribution)
            s.flush()
            return ContributionOut.model_validate(contribution)

    def get(self, account_id: int, transaction_id: int) -> ContributionOut | None:
        with self.session() as s:
            row = (
                s.query(Contribution)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            return ContributionOut.model_validate(row) if row else None

    def get_all(self) -> list[ContributionOut]:
        with self.session() as s:
            rows = s.query(Contribution).all()
            return [ContributionOut.model_validate(r) for r in rows]

    def get_by_transaction(self, transaction_id: int) -> list[ContributionOut]:
        with self.session() as s:
            rows = (
                s.query(Contribution).filter_by(transaction_id=transaction_id).all()
            )
            return [ContributionOut.model_validate(r) for r in rows]

    def get_details_by_transaction(
        self, transaction_id: int
    ) -> list[ContributionDetailOut]:
        with self.session() as s:
            rows = (
                s.query(Contribution, Person.name)
                .join(Account, Contribution.account_id == Account.id)
                .join(Person, Account.person_id == Person.id)
                .filter(Contribution.transaction_id == transaction_id)
                .all()
            )
            return [
                ContributionDetailOut(
                    account_id=contribution.account_id,
                    person_name=person_name,
                    real_amount=contribution.real_amount,
                    liability_amount=contribution.liability_amount,
                )
                for contribution, person_name in rows
            ]

    def update(
        self, account_id: int, transaction_id: int, data: ContributionCreate
    ) -> ContributionOut | None:
        with self.session() as s:
            contribution = (
                s.query(Contribution)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            if not contribution:
                return None
            contribution.real_amount = data.real_amount
            contribution.liability_amount = data.liability_amount
            return ContributionOut.model_validate(contribution)

    def delete(self, account_id: int, transaction_id: int) -> bool:
        with self.session() as s:
            contribution = (
                s.query(Contribution)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            if not contribution:
                return False
            s.delete(contribution)
            return True
