from datetime import datetime
from app.models import (
    Base,
    Category,
    PersonSpace,
    User,
    SpaceUser,
    Space,
    Transaction,
    AccountTransaction,
    Account,
    Person,
    TransactionCategory,
)

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.security import hash_password, verify_password
from app.schemas import (
    PersonSpaceCreate,
    PersonSpaceOut,
    UserCreate,
    UserOut,
    PersonCreate,
    PersonOut,
    PersonSummaryOut,
    AccountCreate,
    AccountOut,
    SpaceCreate,
    SpaceOut,
    SpaceSummaryOut,
    SpaceUserCreate,
    SpaceUserOut,
    TransactionCreate,
    TransactionOut,
    ContributionCreate,
    ContributionOut,
    ContributionDetailOut,
    PersonBalanceOut,
    CategoryCreate,
    CategoryOut,
    TransactionCategoryCreate,
    TransactionCategoryOut,
)


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

    def get_user_by_username(self, username: str) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(username=username).first()
            return UserOut.model_validate(row) if row else None

    def authenticate_user(self, username: str, password: str) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(username=username).first()
            if row is None or not verify_password(password, row.password_hash):
                return None
            return UserOut.model_validate(row)

    def get_users(self) -> list[UserOut]:
        with self.session() as s:
            rows = s.query(User).all()
            return [UserOut.model_validate(r) for r in rows]

    def get_users_by_space(self, space_id: int) -> list[UserOut]:
        with self.session() as s:
            rows = (
                s.query(User)
                .join(SpaceUser, User.id == SpaceUser.user_id)
                .filter(SpaceUser.space_id == space_id)
                .all()
            )
            return [UserOut.model_validate(r) for r in rows]

    def update_user(self, user_id: int, data: UserCreate) -> UserCreate | None:
        with self.session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return None
            user.username = data.username
            user.email = data.email
            user.password_hash = hash_password(data.password)
            return UserCreate.model_validate(user)

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

    def get_persons_by_space(self, space_id: int) -> list[PersonOut]:
        with self.session() as s:
            rows = (
                s.query(Person)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .filter(PersonSpace.space_id == space_id)
                .all()
            )
            return [PersonOut.model_validate(r) for r in rows]

    def get_persons_by_user(self, user_id: int) -> list[PersonOut]:
        with self.session() as s:
            rows = (
                s.query(Person)
                .join(PersonSpace, Person.id == PersonSpace.person_id)
                .join(SpaceUser, PersonSpace.space_id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )
            return [PersonOut.model_validate(r) for r in rows]

    def update_person(self, person_id: int, data: PersonCreate) -> PersonOut | None:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return None
            person.name = data.name
            return PersonOut.model_validate(person)

    def delete_person(self, person_id: int) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=person_id).first()
            if not person:
                return False
            s.delete(person)
            return True

    def get_person_summary(self, person_id: int) -> PersonSummaryOut | None:
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
                .filter(Account.person_id == person_id)
                .scalar()
            )
            accounts = s.query(Account).filter_by(person_id=person_id).all()
            transaction_count = (
                s.query(AccountTransaction)
                .join(Account, AccountTransaction.account_id == Account.id)
                .filter(Account.person_id == person_id)
                .count()
            )
            return PersonSummaryOut(
                person_id=person.id,
                name=person.name,
                net_balance=round(net_balance, 2),
                accounts=[AccountOut.model_validate(a) for a in accounts],
                transaction_count=transaction_count,
            )

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

    def get_accounts_by_person(self, person_id: int) -> list[AccountOut]:
        with self.session() as s:
            rows = s.query(Account).filter_by(person_id=person_id).all()
            return [AccountOut.model_validate(r) for r in rows]

    def get_accounts_by_user(self, user_id: int) -> list[AccountOut]:
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

    def update_account(self, account_id: int, data: AccountCreate) -> AccountOut | None:
        with self.session() as s:
            account = s.query(Account).filter_by(id=account_id).first()
            if not account:
                return None
            account.name = data.name
            account.person_id = data.person_id
            return AccountOut.model_validate(account)

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

    def get_spaces_by_user(self, user_id: int) -> list[SpaceOut]:
        with self.session() as s:
            rows = (
                s.query(Space)
                .join(SpaceUser, Space.id == SpaceUser.space_id)
                .filter(SpaceUser.user_id == user_id)
                .all()
            )

            return [SpaceOut.model_validate(r) for r in rows]

    def get_space_summaries_by_user(self, user_id: int) -> list[SpaceSummaryOut]:
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

    def get_person_balances_by_space(self, space_id: int) -> list[PersonBalanceOut]:
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

    def update_space(self, space_id: int, data: SpaceCreate) -> SpaceOut | None:
        with self.session() as s:
            space = s.query(Space).filter_by(id=space_id).first()
            if not space:
                return None
            space.name = data.name
            space.description = data.description if data.description else ""
            return SpaceOut.model_validate(space)

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

    def update_space_user(
        self, space_user_id: int, data: SpaceUserCreate
    ) -> SpaceUserOut | None:
        with self.session() as s:
            space_user = s.query(SpaceUser).filter_by(id=space_user_id).first()
            if not space_user:
                return None
            space_user.space_id = data.space_id
            space_user.user_id = data.user_id
            space_user.is_owner = data.is_owner
            return SpaceUserOut.model_validate(space_user)

    def delete_space_user(self, space_id: int, user_id: int) -> bool:
        with self.session() as s:
            space_user = (
                s.query(SpaceUser).filter_by(space_id=space_id, user_id=user_id).first()
            )
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

    def get_transactions_by_space(self, space_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = s.query(Transaction).filter_by(space_id=space_id).all()
            return [TransactionOut.model_validate(r) for r in rows]

    def get_transactions_by_account(self, account_id: int) -> list[TransactionOut]:
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

    def get_transactions_by_person(self, person_id: int) -> list[TransactionOut]:
        with self.session() as s:
            rows = (
                s.query(Transaction)
                .join(
                    AccountTransaction,
                    Transaction.id == AccountTransaction.transaction_id,
                )
                .join(Account, AccountTransaction.account_id == Account.id)
                .filter(Account.person_id == person_id)
                .all()
            )
            return [TransactionOut.model_validate(r) for r in rows]

    def update_transaction(
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
            return TransactionOut.model_validate(transaction)

    def delete_transaction(self, transaction_id: int) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=transaction_id).first()
            if not transaction:
                return False
            s.delete(transaction)
            return True

    # ---------- AccountTransaction (Contribution) ----------

    def insert_account_transaction(self, data: ContributionCreate) -> ContributionOut:
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

    def get_account_transaction(
        self, account_id: int, transaction_id: int
    ) -> ContributionOut | None:
        with self.session() as s:
            row = (
                s.query(AccountTransaction)
                .filter_by(account_id=account_id, transaction_id=transaction_id)
                .first()
            )
            return ContributionOut.model_validate(row) if row else None

    def get_account_transactions(self) -> list[ContributionOut]:
        with self.session() as s:
            rows = s.query(AccountTransaction).all()
            return [ContributionOut.model_validate(r) for r in rows]

    def get_account_transactions_by_transaction(
        self, transaction_id: int
    ) -> list[ContributionOut]:
        with self.session() as s:
            rows = (
                s.query(AccountTransaction)
                .filter_by(transaction_id=transaction_id)
                .all()
            )
            return [ContributionOut.model_validate(r) for r in rows]

    def get_contribution_details_by_transaction(
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

    def update_account_transaction(
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
    ) -> PersonSpaceOut | None:
        with self.session() as s:
            person_space = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            if not person_space:
                return None
            person_space.person_id = data.person_id
            person_space.space_id = data.space_id
            return PersonSpaceOut.model_validate(person_space)

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

    # ---------- Category ----------

    def insert_category(self, data: CategoryCreate) -> CategoryOut:
        with self.session() as s:
            category = Category(
                name=data.name,
                created_at=datetime.now(),
            )
            s.add(category)
            s.flush()
            return CategoryOut.model_validate(category)

    def get_category(self, category_id: int) -> CategoryOut | None:
        with self.session() as s:
            row = s.query(Category).filter_by(id=category_id).first()
            return CategoryOut.model_validate(row) if row else None

    def get_categories(self) -> list[CategoryOut]:
        with self.session() as s:
            rows = s.query(Category).all()
            return [CategoryOut.model_validate(r) for r in rows]

    def update_category(
        self, category_id: int, data: CategoryCreate
    ) -> CategoryOut | None:
        with self.session() as s:
            category = s.query(Category).filter_by(id=category_id).first()
            if not category:
                return None
            category.name = data.name
            return CategoryOut.model_validate(category)

    def delete_category(self, category_id: int) -> bool:
        with self.session() as s:
            category = s.query(Category).filter_by(id=category_id).first()
            if not category:
                return False
            s.delete(category)
            return True

    # ---------- TransactionCategory ----------

    def insert_transaction_category(
        self, data: TransactionCategoryCreate
    ) -> TransactionCategoryOut:
        with self.session() as s:
            transaction_category = TransactionCategory(
                transaction_id=data.transaction_id,
                category_id=data.category_id,
            )
            s.add(transaction_category)
            s.flush()
            return TransactionCategoryOut.model_validate(transaction_category)

    def get_transaction_category(
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

    def delete_transaction_category(self, transaction_id: int, category_id: int) -> bool:
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
