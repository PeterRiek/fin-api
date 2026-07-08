from datetime import datetime
from app.models import (
    Base,
    PersonSpace,
    User,
    SpaceUser,
    Space,
    Transaction,
    AccountTransaction,
    Account,
    Person,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.schemas import (
    PersonSpaceCreate,
    PersonSpaceOut,
    UserCreate,
    UserOut,
    PersonCreate,
    PersonOut,
    AccountCreate,
    AccountOut,
    SpaceCreate,
    SpaceOut,
    SpaceUserCreate,
    SpaceUserOut,
    TransactionCreate,
    TransactionOut,
    AccountTransactionCreate,
    AccountTransactionOut,
)


hash_password = lambda password: password  # Placeholder for actual hashing function


class Database:
    def __init__(self, connection_string) -> None:
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session(self):
        s = self.Session()
        try:
            yield s
            s.commit()
        except:
            s.rollback()
            raise
        finally:
            s.close()

    # ---------- User ----------

    def insert_user(self, data: UserCreate) -> UserOut:
        with self.session() as s:
            user = User(
                username=data.username,
                email=data.email,
                password_hash=hash_password(data.password),  # hash before storing
                created_at=datetime.now(),
            )
            s.add(user)
            s.flush()
            return UserOut.model_validate(user)  # built while session is still open

    def get_user(self, user_id: int) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(id=user_id).first()
            return UserOut.model_validate(row) if row else None

    def get_users(self) -> list[UserOut]:
        with self.session() as s:
            rows = s.query(User).all()
            return [UserOut.model_validate(r) for r in rows]

    def update_user(self, user_id: int, data: UserCreate) -> bool:
        with self.session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            user.username = data.username
            user.email = data.email
            user.password_hash = hash_password(data.password)
            return True

    def delete_user(self, user_id: int) -> bool:
        with self.session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            s.delete(user)
            return True

    # ---------- Person ----------

    def insert_person(self, data: PersonCreate) -> PersonOut:
        with self.session() as s:
            person = Person(
                name=data.name,
                created_at=datetime.now(),
            )
            s.add(person)
            s.flush()
            return PersonOut.model_validate(person)

    def get_person(self, person_id: int) -> PersonOut | None:
        with self.session() as s:
            row = s.query(Person).filter_by(id=person_id).first()
            return PersonOut.model_validate(row) if row else None

    def get_persons(self) -> list[PersonOut]:
        with self.session() as s:
            rows = s.query(Person).all()
            return [PersonOut.model_validate(r) for r in rows]

    def update_person(self, person_id: int, data: PersonCreate) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return False
            person.name = data.name
            return True

    def delete_person(self, person_id: int) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return False
            s.delete(person)
            return True

    # ---------- Account ----------

    def insert_account(self, data: AccountCreate) -> AccountOut:
        with self.session() as s:
            account = Account(
                name=data.name,
                person_id=data.person_id,
                created_at=datetime.now(),
            )
            s.add(account)
            s.flush()
            return AccountOut.model_validate(account)

    def get_account(self, account_id: int) -> AccountOut | None:
        with self.session() as s:
            row = s.query(Account).filter_by(id=account_id).first()
            return AccountOut.model_validate(row) if row else None

    def get_accounts(self) -> list[AccountOut]:
        with self.session() as s:
            rows = s.query(Account).all()
            return [AccountOut.model_validate(r) for r in rows]

    def update_account(self, account_id: int, data: AccountCreate) -> bool:
        with self.session() as s:
            account = s.query(Account).filter_by(id=account_id).first()
            if not account:
                return False
            account.name = data.name
            account.person_id = data.person_id
            return True

    def delete_account(self, account_id: int) -> bool:
        with self.session() as s:
            account = s.query(Account).filter_by(id=account_id).first()
            if not account:
                return False
            s.delete(account)
            return True

    # ---------- Space ----------

    def insert_space(self, data: SpaceCreate) -> SpaceOut:
        with self.session() as s:
            space = Space(
                name=data.name,
                description=data.description,
                created_at=datetime.now(),
            )
            s.add(space)
            s.flush()
            return SpaceOut.model_validate(space)

    def get_space(self, space_id: int) -> SpaceOut | None:
        with self.session() as s:
            row = s.query(Space).filter_by(id=space_id).first()
            return SpaceOut.model_validate(row) if row else None

    def get_spaces(self) -> list[SpaceOut]:
        with self.session() as s:
            rows = s.query(Space).all()
            return [SpaceOut.model_validate(r) for r in rows]

    def update_space(self, space_id: int, data: SpaceCreate) -> bool:
        with self.session() as s:
            space = s.query(Space).filter_by(id=space_id).first()
            if not space:
                return False
            space.name = data.name
            space.description = data.description if data.description else ""
            return True

    def delete_space(self, space_id: int) -> bool:
        with self.session() as s:
            space = s.query(Space).filter_by(id=space_id).first()
            if not space:
                return False
            s.delete(space)
            return True

    # ---------- SpaceUser ----------

    def insert_space_user(self, data: SpaceUserCreate) -> SpaceUserOut:
        with self.session() as s:
            space_user = SpaceUser(
                space_id=data.space_id,
                user_id=data.user_id,
                is_owner=data.is_owner,
            )
            s.add(space_user)
            s.flush()
            return SpaceUserOut.model_validate(space_user)

    def get_space_user(self, space_user_id: int) -> SpaceUserOut | None:
        with self.session() as s:
            row = s.query(SpaceUser).filter_by(id=space_user_id).first()
            return SpaceUserOut.model_validate(row) if row else None

    def get_space_users(self) -> list[SpaceUserOut]:
        with self.session() as s:
            rows = s.query(SpaceUser).all()
            return [SpaceUserOut.model_validate(r) for r in rows]

    def update_space_user(self, space_user_id: int, data: SpaceUserCreate) -> bool:
        with self.session() as s:
            space_user = s.query(SpaceUser).filter_by(id=space_user_id).first()
            if not space_user:
                return False
            space_user.space_id = data.space_id
            space_user.user_id = data.user_id
            space_user.is_owner = data.is_owner
            return True

    def delete_space_user(self, space_user_id: int) -> bool:
        with self.session() as s:
            space_user = s.query(SpaceUser).filter_by(id=space_user_id).first()
            if not space_user:
                return False
            s.delete(space_user)
            return True

    # ---------- Transaction ----------

    def insert_transaction(self, data: TransactionCreate) -> TransactionOut:
        with self.session() as s:
            transaction = Transaction(
                space_id=data.space_id,
                title=data.title,
                description=data.description,
                date=data.date,
                created_at=datetime.now(),
            )
            s.add(transaction)
            s.flush()
            return TransactionOut.model_validate(transaction)

    def get_transaction(self, transaction_id: int) -> TransactionOut | None:
        with self.session() as s:
            row = s.query(Transaction).filter_by(id=transaction_id).first()
            return TransactionOut.model_validate(row) if row else None

    def get_transactions(self) -> list[TransactionOut]:
        with self.session() as s:
            rows = s.query(Transaction).all()
            return [TransactionOut.model_validate(r) for r in rows]

    def update_transaction(self, transaction_id: int, data: TransactionCreate) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=transaction_id).first()
            if not transaction:
                return False
            transaction.space_id = data.space_id
            transaction.title = data.title
            transaction.description = data.description
            transaction.date = data.date
            return True

    def delete_transaction(self, transaction_id: int) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=transaction_id).first()
            if not transaction:
                return False
            s.delete(transaction)
            return True

    # ---------- AccountTransaction ----------

    def insert_account_transaction(
        self, data: AccountTransactionCreate
    ) -> AccountTransactionOut:
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
            return AccountTransactionOut.model_validate(account_transaction)

    def get_account_transaction(
        self, account_id: int, transaction_id: int
    ) -> AccountTransactionOut | None:
        with self.session() as s:
            row = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            return AccountTransactionOut.model_validate(row) if row else None

    def get_account_transactions(self) -> list[AccountTransactionOut]:
        with self.session() as s:
            rows = s.query(AccountTransaction).all()
            return [AccountTransactionOut.model_validate(r) for r in rows]

    def update_account_transaction(
        self, account_id: int, transaction_id: int, data: AccountTransactionCreate
    ) -> bool:
        with self.session() as s:
            account_transaction = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            if not account_transaction:
                return False
            account_transaction.amount_requested = data.amount_requested
            account_transaction.amount_paid = data.amount_paid
            account_transaction.is_initial = data.is_initial
            return True

    def delete_account_transaction(self, account_id: int, transaction_id: int) -> bool:
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

    # ---------- PersonSpace ----------

    def insert_person_space(self, data: PersonSpaceCreate) -> PersonSpaceOut:
        with self.session() as s:
            person_space = PersonSpace(
                person_id=data.person_id,
                space_id=data.space_id,
            )
            s.add(person_space)
            s.flush()
            return PersonSpaceOut.model_validate(person_space)

    def get_person_space(self, person_id: int, space_id: int) -> PersonSpaceOut | None:
        with self.session() as s:
            row = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            return PersonSpaceOut.model_validate(row) if row else None

    def get_person_spaces(self) -> list[PersonSpaceOut]:
        with self.session() as s:
            rows = s.query(PersonSpace).all()
            return [PersonSpaceOut.model_validate(r) for r in rows]

    def update_person_space(
        self, person_id: int, space_id: int, data: PersonSpaceCreate
    ) -> bool:
        with self.session() as s:
            person_space = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            if not person_space:
                return False
            person_space.person_id = data.person_id
            person_space.space_id = data.space_id
            return True

    def delete_person_space(self, person_id: int, space_id: int) -> bool:
        with self.session() as s:
            person_space = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            if not person_space:
                return False
            s.delete(person_space)
            return True
