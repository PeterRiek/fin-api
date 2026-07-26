from datetime import date

import pytest

from app.database import Database
from app.schemas import (
    AccountCreate,
    ContributionCreate,
    ContributionDetailOut,
    PersonCreate,
    PersonSpaceCreate,
    SpaceCreate,
    SpaceUserCreate,
    TransactionCreate,
    TransactionDetailOut,
    UserCreate,
)


@pytest.fixture
def fresh_db() -> Database:
    return Database("sqlite:///:memory:")


# ---------- User ----------


def test_insert_and_get_user(fresh_db: Database):
    user = fresh_db.users.insert(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert user.id is not None
    assert fresh_db.users.get(user.id) == user
    assert fresh_db.users.get_by_username("bob") == user


def test_get_user_missing_returns_none(fresh_db: Database):
    assert fresh_db.users.get(999) is None
    assert fresh_db.users.get_by_username("nobody") is None


def test_authenticate_user(fresh_db: Database):
    fresh_db.users.insert(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert fresh_db.users.authenticate("bob", "secret") is not None
    assert fresh_db.users.authenticate("bob", "wrong") is None
    assert fresh_db.users.authenticate("nobody", "secret") is None


def test_delete_user(fresh_db: Database):
    user = fresh_db.users.insert(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert fresh_db.users.delete(user.id) is True
    assert fresh_db.users.get(user.id) is None
    assert fresh_db.users.delete(user.id) is False


# ---------- Person ----------


def test_person_crud(fresh_db: Database):
    person = fresh_db.persons.insert(PersonCreate(name="Charlie"))
    assert fresh_db.persons.get(person.id) == person

    updated = fresh_db.persons.update(person.id, PersonCreate(name="Charles"))
    assert updated
    assert updated.name == "Charles"
    assert fresh_db.persons.update(999, PersonCreate(name="x")) is None

    assert fresh_db.persons.delete(person.id) is True
    assert fresh_db.persons.get(person.id) is None


# ---------- Account ----------


def test_account_crud(fresh_db: Database):
    person = fresh_db.persons.insert(PersonCreate(name="Dana"))
    account = fresh_db.accounts.insert(
        AccountCreate(name="Dana's account", person_id=person.id)
    )
    assert fresh_db.accounts.get(account.id) == account
    assert fresh_db.accounts.get_by_person(person.id) == [account]

    other_person = fresh_db.persons.insert(PersonCreate(name="Eve"))
    updated = fresh_db.accounts.update(
        account.id, AccountCreate(name="renamed", person_id=other_person.id)
    )
    assert updated
    assert updated.name == "renamed"
    assert updated.person_id == other_person.id

    assert fresh_db.accounts.delete(account.id) is True
    assert fresh_db.accounts.get(account.id) is None


# ---------- Space ----------


def test_space_crud(fresh_db: Database):
    space = fresh_db.spaces.insert(SpaceCreate(name="Trip", description="Ski trip"))
    assert fresh_db.spaces.get(space.id) == space

    updated = fresh_db.spaces.update(space.id, SpaceCreate(name="Trip 2026"))
    assert updated
    assert updated.name == "Trip 2026"
    assert updated.description == ""

    assert fresh_db.spaces.delete(space.id) is True
    assert fresh_db.spaces.get(space.id) is None


# ---------- Relationship helpers (spaces/persons/accounts/users) ----------


@pytest.fixture
def world(fresh_db: Database):
    """A user in a space, with a person (and their account) also in that space."""
    user = fresh_db.users.insert(
        UserCreate(username="frank", email="frank@example.com", password="secret")
    )
    space = fresh_db.spaces.insert(SpaceCreate(name="Household"))
    fresh_db.space_users.insert(
        SpaceUserCreate(space_id=space.id, user_id=user.id, is_owner=True)
    )
    person = fresh_db.persons.insert(PersonCreate(name="Grace"))
    fresh_db.person_spaces.insert(
        PersonSpaceCreate(person_id=person.id, space_id=space.id)
    )
    account = fresh_db.accounts.insert(
        AccountCreate(name="Grace's account", person_id=person.id)
    )
    return {
        "db": fresh_db,
        "user": user,
        "space": space,
        "person": person,
        "account": account,
    }


def test_get_spaces_by_user(world):
    db, user, space = world["db"], world["user"], world["space"]
    assert db.spaces.get_by_user(user.id) == [space]


def test_get_users_by_space(world):
    db, user, space = world["db"], world["user"], world["space"]
    assert db.users.get_by_space(space.id) == [user]


def test_get_persons_by_space_and_by_user(world):
    db, user, space, person = (
        world["db"],
        world["user"],
        world["space"],
        world["person"],
    )
    assert db.persons.get_by_space(space.id) == [person]
    assert db.persons.get_by_user(user.id) == [person]


def test_get_accounts_by_user(world):
    db, user, account = world["db"], world["user"], world["account"]
    assert db.accounts.get_by_user(user.id) == [account]


def test_delete_space_user_and_person_space(world):
    db, user, space, person = (
        world["db"],
        world["user"],
        world["space"],
        world["person"],
    )
    assert db.space_users.delete(space.id, user.id) is True
    assert db.users.get_by_space(space.id) == []
    assert db.space_users.delete(space.id, user.id) is False

    assert db.person_spaces.delete(person.id, space.id) is True
    assert db.persons.get_by_space(space.id) == []


# ---------- Transaction / Contribution ----------


@pytest.fixture
def transaction_world(world):
    db, space, account = world["db"], world["space"], world["account"]
    transaction = db.transactions.insert(
        TransactionCreate(space_id=space.id, title="Groceries", date=date(2026, 1, 1))
    )
    contribution = db.contributions.insert(
        ContributionCreate(
            account_id=account.id,
            transaction_id=transaction.id,
            real_amount=-50.0,
            liability_amount=0.0,
        )
    )
    world["transaction"] = transaction
    world["contribution"] = contribution
    return world


def test_transaction_crud(transaction_world):
    db = transaction_world["db"]
    space = transaction_world["space"]
    person = transaction_world["person"]
    account = transaction_world["account"]
    transaction = transaction_world["transaction"]

    assert db.transactions.get(transaction.id) == transaction
    assert db.transactions.get_by_space(space.id) == [
        TransactionDetailOut(
            **transaction.model_dump(),
            contributions=[
                ContributionDetailOut(
                    account_id=account.id,
                    person_name=person.name,
                    real_amount=-50.0,
                    liability_amount=0.0,
                )
            ],
            categories=[],
        )
    ]

    updated = db.transactions.update(
        transaction.id,
        TransactionCreate(
            space_id=space.id, title="Groceries v2", date=date(2026, 1, 2)
        ),
    )
    assert updated.title == "Groceries v2"

    assert db.transactions.delete(transaction.id) is True
    assert db.transactions.get(transaction.id) is None


def test_get_transactions_by_account_and_person(transaction_world):
    db = transaction_world["db"]
    account = transaction_world["account"]
    person = transaction_world["person"]
    user = transaction_world["user"]
    transaction = transaction_world["transaction"]

    expected = TransactionDetailOut(
        **transaction.model_dump(),
        contributions=[
            ContributionDetailOut(
                account_id=account.id,
                person_name=person.name,
                real_amount=-50.0,
                liability_amount=0.0,
            )
        ],
        categories=[],
    )
    assert db.transactions.get_by_account(account.id) == [expected]
    assert db.transactions.get_by_person(person.id, user.id) == [expected]


def test_account_transaction_crud(transaction_world):
    db = transaction_world["db"]
    account = transaction_world["account"]
    transaction = transaction_world["transaction"]
    contribution = transaction_world["contribution"]

    assert db.contributions.get(account.id, transaction.id) == contribution
    assert db.contributions.get_by_transaction(transaction.id) == [contribution]

    updated = db.contributions.update(
        account.id,
        transaction.id,
        ContributionCreate(
            account_id=account.id,
            transaction_id=transaction.id,
            real_amount=-25.0,
            liability_amount=-50.0,
        ),
    )
    assert updated.real_amount == -25.0
    assert updated.liability_amount == -50.0

    assert db.contributions.delete(account.id, transaction.id) is True
    assert db.contributions.get(account.id, transaction.id) is None
