from datetime import datetime

from sqlalchemy import func

from app.models import (
    Account,
    Category,
    Contribution,
    Person,
    PersonSpace,
    SpaceUser,
    Transaction,
    TransactionCategory,
    TransactionType,
)
from app.repositories.base import BaseRepository
from app.schemas import (
    AccountBalanceOut,
    AccountCreate,
    AccountOut,
    CategoryOut,
    ContributionDetailOut,
    SimpleTransactionCreate,
    TransactionDetailOut,
    TransactionOut,
    TransferCreate,
    TransferOut,
)


class AccountRepository(BaseRepository):
    def insert(self, data: AccountCreate) -> AccountOut:
        with self.session() as s:
            account = Account(
                name=data.name,
                person_id=data.person_id,
                created_at=datetime.now(),
            )
            s.add(account)
            s.flush()
            return AccountOut.model_validate(account)

    def get(self, account_id: int) -> AccountOut | None:
        with self.session() as s:
            row = s.query(Account).filter_by(id=account_id).first()
            return AccountOut.model_validate(row) if row else None

    def get_all(self) -> list[AccountOut]:
        with self.session() as s:
            rows = s.query(Account).all()
            return [AccountOut.model_validate(r) for r in rows]

    def get_by_person(self, person_id: int) -> list[AccountOut]:
        with self.session() as s:
            rows = s.query(Account).filter_by(person_id=person_id).all()
            return [AccountOut.model_validate(r) for r in rows]

    def get_by_user(self, user_id: int) -> list[AccountOut]:
        with self.session() as s:
            rows = (
                s.query(Account)
                .join(Person, Account.person_id == Person.id)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .join(SpaceUser, PersonSpace.space_id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )
            return [AccountOut.model_validate(r) for r in rows]

    def update(self, account_id: int, data: AccountCreate) -> AccountOut | None:
        with self.session() as s:
            account = s.query(Account).filter_by(id=account_id).first()
            if not account:
                return None
            account.name = data.name
            account.person_id = data.person_id
            return AccountOut.model_validate(account)

    def delete(self, account_id: int) -> bool:
        with self.session() as s:
            account = s.query(Account).filter_by(id=account_id).first()
            if not account:
                return False
            s.delete(account)
            return True

    def get_balance(self, account_id: int) -> AccountBalanceOut:
        with self.session() as s:
            balance = (
                s.query(func.coalesce(func.sum(Contribution.real_amount), 0.0))
                .filter(Contribution.account_id == account_id)
                .scalar()
            )
            return AccountBalanceOut(account_id=account_id, balance=round(balance, 2))

    def create_transaction(
        self, account_id: int, data: SimpleTransactionCreate
    ) -> TransactionDetailOut:
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

            # A solo transaction has no split, so it carries no liability
            # shift; only the sign of the real cash movement depends on type.
            real_amount = (
                data.amount if data.type == TransactionType.INCOME else -data.amount
            )
            s.add(
                Contribution(
                    account_id=account_id,
                    transaction_id=transaction.id,
                    real_amount=real_amount,
                    liability_amount=0.0,
                )
            )
            if data.category_id is not None:
                s.add(
                    TransactionCategory(
                        transaction_id=transaction.id, category_id=data.category_id
                    )
                )
            s.flush()

            person_name = (
                s.query(Person.name)
                .join(Account, Account.person_id == Person.id)
                .filter(Account.id == account_id)
                .scalar()
            )
            categories = (
                s.query(Category)
                .join(
                    TransactionCategory, Category.id == TransactionCategory.category_id
                )
                .filter(TransactionCategory.transaction_id == transaction.id)
                .all()
            )
            return TransactionDetailOut(
                id=transaction.id,
                space_id=transaction.space_id,
                title=transaction.title,
                description=transaction.description,
                date=transaction.date,
                type=transaction.type,
                linked_transaction_id=transaction.linked_transaction_id,
                created_at=transaction.created_at,
                contributions=[
                    ContributionDetailOut(
                        account_id=account_id,
                        person_name=person_name,
                        real_amount=real_amount,
                        liability_amount=0.0,
                    )
                ],
                categories=[CategoryOut.model_validate(c) for c in categories],
            )

    def create_transfer(
        self, from_account_id: int, data: TransferCreate
    ) -> TransferOut:
        with self.session() as s:
            now = datetime.now()
            out_transaction = Transaction(
                space_id=data.space_id,
                title=data.title,
                description=data.description,
                date=data.date,
                type=TransactionType.EXPENSE,
                created_at=now,
            )
            in_transaction = Transaction(
                space_id=data.space_id,
                title=data.title,
                description=data.description,
                date=data.date,
                type=TransactionType.INCOME,
                created_at=now,
            )
            s.add_all([out_transaction, in_transaction])
            s.flush()

            out_transaction.linked_transaction_id = in_transaction.id
            in_transaction.linked_transaction_id = out_transaction.id

            # Real cash always moves in full on both legs (a transfer, by
            # definition, physically moves money). debt_shift independently
            # controls the liability effect: 0 for a plain move-my-own-money
            # transfer, or the full amount for a debt settlement, moving
            # credit from the receiver to the sender.
            debt_shift = data.amount if data.affects_balance else 0.0

            s.add_all(
                [
                    Contribution(
                        account_id=from_account_id,
                        transaction_id=out_transaction.id,
                        real_amount=-data.amount,
                        liability_amount=debt_shift,
                    ),
                    Contribution(
                        account_id=data.to_account_id,
                        transaction_id=in_transaction.id,
                        real_amount=data.amount,
                        liability_amount=-debt_shift,
                    ),
                ]
            )
            s.flush()

            return TransferOut(
                out_transaction=TransactionOut.model_validate(out_transaction),
                in_transaction=TransactionOut.model_validate(in_transaction),
            )
