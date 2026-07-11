from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repositories import (
    AccountRepository,
    CategoryRepository,
    ContributionRepository,
    PersonRepository,
    PersonSpaceRepository,
    SpaceRepository,
    SpaceUserRepository,
    TransactionCategoryRepository,
    TransactionRepository,
    UserRepository,
)


class Database:
    def __init__(self, connection_string) -> None:
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)

        self.users = UserRepository(session_factory)
        self.persons = PersonRepository(session_factory)
        self.accounts = AccountRepository(session_factory)
        self.spaces = SpaceRepository(session_factory)
        self.space_users = SpaceUserRepository(session_factory)
        self.person_spaces = PersonSpaceRepository(session_factory)
        self.transactions = TransactionRepository(session_factory)
        self.contributions = ContributionRepository(session_factory)
        self.categories = CategoryRepository(session_factory)
        self.transaction_categories = TransactionCategoryRepository(session_factory)
