from datetime import datetime

from sqlalchemy import func

from app.models import (
    Account,
    AccountTransaction,
    Person,
    PersonSpace,
    SpaceUser,
    Transaction,
)
from app.repositories.base import BaseRepository
from app.schemas import AccountOut, PersonCreate, PersonOut, PersonSummaryOut


class PersonRepository(BaseRepository):
    def insert(self, data: PersonCreate) -> PersonOut:
        with self.session() as s:
            person = Person(
                name=data.name,
                created_at=datetime.now(),
            )
            s.add(person)
            s.flush()
            return PersonOut.model_validate(person)

    def get(self, person_id: int) -> PersonOut | None:
        with self.session() as s:
            row = s.query(Person).filter_by(id=person_id).first()
            return PersonOut.model_validate(row) if row else None

    def get_all(self) -> list[PersonOut]:
        with self.session() as s:
            rows = s.query(Person).all()
            return [PersonOut.model_validate(r) for r in rows]

    def get_by_space(self, space_id: int) -> list[PersonOut]:
        with self.session() as s:
            rows = (
                s.query(Person)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .filter(PersonSpace.space_id == space_id)
                .all()
            )
            return [PersonOut.model_validate(r) for r in rows]

    def get_by_user(self, user_id: int) -> list[PersonOut]:
        with self.session() as s:
            rows = (
                s.query(Person)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .join(SpaceUser, PersonSpace.space_id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )
            return [PersonOut.model_validate(r) for r in rows]

    def update(self, person_id: int, data: PersonCreate) -> PersonOut | None:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return None
            person.name = data.name
            return PersonOut.model_validate(person)

    def delete(self, person_id: int) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return False
            s.delete(person)
            return True

    def get_summary(self, person_id: int, user_id: int) -> PersonSummaryOut | None:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return None
            net_balance = (
                s.query(
                    func.coalesce(
                        func.sum(
                            AccountTransaction.amount_paid
                            - AccountTransaction.amount_requested
                        ),
                        0.0,
                    )
                )
                .join(Account, AccountTransaction.account_id == Account.id)
                .join(
                    Transaction,
                    AccountTransaction.transaction_id == Transaction.id,
                )
                .join(SpaceUser, Transaction.space_id == SpaceUser.space_id)
                .filter(Account.person_id == person_id, SpaceUser.user_id == user_id)
                .scalar()
            )
            accounts = s.query(Account).filter_by(person_id=person_id).all()
            transaction_count = (
                s.query(AccountTransaction)
                .join(Account, AccountTransaction.account_id == Account.id)
                .join(
                    Transaction,
                    AccountTransaction.transaction_id == Transaction.id,
                )
                .join(SpaceUser, Transaction.space_id == SpaceUser.space_id)
                .filter(Account.person_id == person_id, SpaceUser.user_id == user_id)
                .count()
            )
            return PersonSummaryOut(
                person_id=person.id,
                name=person.name,
                net_balance=round(net_balance, 2),
                accounts=[AccountOut.model_validate(a) for a in accounts],
                transaction_count=transaction_count,
            )
