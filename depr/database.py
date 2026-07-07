from app.models import Base, Transaction, Account, Category, Person, Contribution
from app.schemas import AccountResponse, CategoryResponse, PersonResponse, TransactionCreate, TransactionResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


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

    # --- Accounts ---

    def insert_account(self, name: str) -> int:
        with self.session() as s:
            account = Account(name=name)
            s.add(account)
            s.flush()
            assert account.id is not None
            return account.id

    def get_account(self, id: int) -> AccountResponse | None:
        with self.session() as s:
            row = s.query(Account).filter_by(id=id).first()
            return AccountResponse.model_validate(row) if row else None

    def get_accounts(self) -> list[AccountResponse]:
        with self.session() as s:
            rows = s.query(Account).all()
            return [AccountResponse.model_validate(r) for r in rows]

    def update_account(self, id: int, name: str) -> bool:
        with self.session() as s:
            account = s.query(Account).filter_by(id=id).first()
            if not account:
                return False
            account.name = name
            return True

    def delete_account(self, id: int) -> bool:
        with self.session() as s:
            account = s.query(Account).filter_by(id=id).first()
            if not account:
                return False
            s.delete(account)
            return True

    # --- Categories ---

    def insert_category(self, name: str) -> int:
        with self.session() as s:
            category = Category(name=name)
            s.add(category)
            s.flush()
            assert category.id is not None
            return category.id

    def get_category(self, id: int) -> CategoryResponse | None:
        with self.session() as s:
            row = s.query(Category).filter_by(id=id).first()
            return CategoryResponse.model_validate(row) if row else None

    def get_categories(self) -> list[CategoryResponse]:
        with self.session() as s:
            rows = s.query(Category).all()
            return [CategoryResponse.model_validate(r) for r in rows]

    def update_category(self, id: int, name: str) -> bool:
        with self.session() as s:
            category = s.query(Category).filter_by(id=id).first()
            if not category:
                return False
            category.name = name
            return True

    def delete_category(self, id: int) -> bool:
        with self.session() as s:
            category = s.query(Category).filter_by(id=id).first()
            if not category:
                return False
            s.delete(category)
            return True

    # --- Persons ---

    def insert_person(self, name: str) -> int:
        with self.session() as s:
            person = Person(name=name)
            s.add(person)
            s.flush()
            assert person.id is not None
            return person.id

    def get_person(self, id: int) -> PersonResponse | None:
        with self.session() as s:
            row = s.query(Person).filter_by(id=id).first()
            return PersonResponse.model_validate(row) if row else None

    def get_persons(self) -> list[PersonResponse]:
        with self.session() as s:
            rows = s.query(Person).all()
            return [PersonResponse.model_validate(r) for r in rows]

    def update_person(self, id: int, name: str) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=id).first()
            if not person:
                return False
            person.name = name
            return True

    def delete_person(self, id: int) -> bool:
        with self.session() as s:
            person = s.query(Person).filter_by(id=id).first()
            if not person:
                return False
            s.delete(person)
            return True

    # --- Transactions ---

    def insert_transaction(self, data: TransactionCreate) -> int:
        with self.session() as s:
            account = s.query(Account).filter_by(name=data.account).first()
            if not account:
                account = Account(name=data.account)
                s.add(account)

            categories = []
            for cat_name in data.categories:
                cat = s.query(Category).filter_by(name=cat_name).first()
                if not cat:
                    cat = Category(name=cat_name)
                    s.add(cat)
                categories.append(cat)

            contributions = []
            for c in data.contributions:
                person = s.query(Person).filter_by(name=c.person).first()
                if not person:
                    person = Person(name=c.person)
                    s.add(person)
                contributions.append(
                    Contribution(
                        person=person, amount=c.amount, amount_paid=c.amount_paid
                    )
                )

            transaction = Transaction(
                title=data.title,
                description=data.description,
                date=data.date,
                amount=data.amount,
                account=account,
                categories=categories,
                contributions=contributions,
            )
            s.add(transaction)
            s.flush()
            assert transaction.id is not None
            return transaction.id

    def get_transaction(self, id: int) -> TransactionResponse | None:
        with self.session() as s:
            row = s.query(Transaction).filter_by(id=id).first()
            return TransactionResponse.model_validate(row) if row else None

    def get_transactions(self) -> list[TransactionResponse]:
        with self.session() as s:
            rows = s.query(Transaction).all()
            return [TransactionResponse.model_validate(r) for r in rows]

    def update_transaction(self, id: int, data: TransactionCreate) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=id).first()
            if not transaction:
                return False

            account = s.query(Account).filter_by(name=data.account).first()
            if not account:
                account = Account(name=data.account)
                s.add(account)

            categories = []
            for cat_name in data.categories:
                cat = s.query(Category).filter_by(name=cat_name).first()
                if not cat:
                    cat = Category(name=cat_name)
                    s.add(cat)
                categories.append(cat)

            # Replace contributions (cascade delete-orphan handles old ones)
            new_contributions = []
            for c in data.contributions:
                person = s.query(Person).filter_by(name=c.person).first()
                if not person:
                    person = Person(name=c.person)
                    s.add(person)
                new_contributions.append(
                    Contribution(
                        person=person, amount=c.amount, amount_paid=c.amount_paid
                    )
                )

            transaction.title = data.title
            transaction.description = data.description
            transaction.date = data.date
            transaction.amount = data.amount
            transaction.account = account
            transaction.categories = categories
            transaction.contributions = new_contributions
            return True

    def delete_transaction(self, id: int) -> bool:
        with self.session() as s:
            transaction = s.query(Transaction).filter_by(id=id).first()
            if not transaction:
                return False
            s.delete(transaction)
            return True
