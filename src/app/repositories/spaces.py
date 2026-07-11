from datetime import datetime

from sqlalchemy import func

from app.models import (
    Account,
    AccountTransaction,
    Person,
    PersonSpace,
    Space,
    SpaceUser,
    Transaction,
)
from app.repositories.base import BaseRepository
from app.schemas import PersonBalanceOut, SpaceCreate, SpaceOut, SpaceSummaryOut


class SpaceRepository(BaseRepository):
    def insert(self, data: SpaceCreate) -> SpaceOut:
        with self.session() as s:
            space = Space(
                name=data.name,
                description=data.description,
                created_at=datetime.now(),
            )
            s.add(space)
            s.flush()
            return SpaceOut.model_validate(space)

    def get(self, space_id: int) -> SpaceOut | None:
        with self.session() as s:
            row = s.query(Space).filter_by(id=space_id).first()
            return SpaceOut.model_validate(row) if row else None

    def get_all(self) -> list[SpaceOut]:
        with self.session() as s:
            rows = s.query(Space).all()
            return [SpaceOut.model_validate(r) for r in rows]

    def get_by_user(self, user_id: int) -> list[SpaceOut]:
        with self.session() as s:
            rows = (
                s.query(Space)
                .join(SpaceUser, Space.id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )

            return [SpaceOut.model_validate(r) for r in rows]

    def get_summaries_by_user(self, user_id: int) -> list[SpaceSummaryOut]:
        with self.session() as s:
            spaces = (
                s.query(Space)
                .join(SpaceUser, Space.id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )
            summaries = []
            for space in spaces:
                member_count = s.query(SpaceUser).filter_by(space_id=space.id).count()
                transaction_count = (
                    s.query(Transaction).filter_by(space_id=space.id).count()
                )
                summaries.append(
                    SpaceSummaryOut(
                        id=space.id,
                        name=space.name,
                        description=space.description,
                        created_at=space.created_at,
                        member_count=member_count,
                        transaction_count=transaction_count,
                    )
                )
            return summaries

    def get_person_balances(self, space_id: int) -> list[PersonBalanceOut]:
        with self.session() as s:
            persons = (
                s.query(Person)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .filter(PersonSpace.space_id == space_id)
                .all()
            )
            balances = []
            for person in persons:
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
                    .filter(
                        Account.person_id == person.id, Transaction.space_id == space_id
                    )
                    .scalar()
                )
                balances.append(
                    PersonBalanceOut(
                        person_id=person.id,
                        name=person.name,
                        net_balance=round(net_balance, 2),
                    )
                )
            return balances

    def update(self, space_id: int, data: SpaceCreate) -> SpaceOut | None:
        with self.session() as s:
            space = s.query(Space).filter_by(id=space_id).first()
            if not space:
                return None
            space.name = data.name
            space.description = data.description if data.description else ""
            return SpaceOut.model_validate(space)

    def delete(self, space_id: int) -> bool:
        with self.session() as s:
            space = s.query(Space).filter_by(id=space_id).first()
            if not space:
                return False
            s.delete(space)
            return True
