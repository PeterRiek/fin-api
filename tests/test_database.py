from datetime import date

import pytest

from app.database import Database
from app.schemas import (
    AccountCreate,
    AccountTransactionCreate,
    PersonCreate,
    PersonSpaceCreate,
    SpaceCreate,
    SpaceUserCreate,
    TransactionCreate,
    UserCreate,
)


@pytest.fixture
def fresh_db() -> Database:
    return Database("sqlite:///:memory:")


# ---------- User ----------


def test_insert_and_get_user(fresh_db: Database):
    user = fresh_db.insert_user(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert user.id is not None
    assert fresh_db.get_user(user.id) == user
    assert fresh_db.get_user_by_username("bob") == user


def test_get_user_missing_returns_none(fresh_db: Database):
    assert fresh_db.get_user(999) is None
    assert fresh_db.get_user_by_username("nobody") is None


def test_authenticate_user(fresh_db: Database):
    fresh_db.insert_user(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert fresh_db.authenticate_user("bob", "secret") is not None
    assert fresh_db.authenticate_user("bob", "wrong") is None
    assert fresh_db.authenticate_user("nobody", "secret") is None


def test_delete_user(fresh_db: Database):
    user = fresh_db.insert_user(
        UserCreate(username="bob", email="bob@example.com", password="secret")
    )
    assert fresh_db.delete_user(user.id) is True
    assert fresh_db.get_user(user.id) is None
    assert fresh_db.delete_user(user.id) is False


# ---------- Person ----------


def test_person_crud(fresh_db: Database):
    person = fresh_db.insert_person(PersonCreate(name="Charlie"))
    assert fresh_db.get_person(person.id) == person

    updated = fresh_db.update_person(person.id, PersonCreate(name="Charles"))
    assert updated
    assert updated.name == "Charles"
    assert fresh_db.update_person(999, PersonCreate(name="x")) is None

    assert fresh_db.delete_person(person.id) is True
    assert fresh_db.get_person(person.id) is None


# ---------- Account ----------


def test_account_crud(fresh_db: Database):
    person = fresh_db.insert_person(PersonCreate(name="Dana"))
    account = fresh_db.insert_account(
        AccountCreate(name="Dana's account", person_id=person.id)
    )
    assert fresh_db.get_account(account.id) == account
    assert fresh_db.get_accounts_by_person(person.id) == [account]

    other_person = fresh_db.insert_person(PersonCreate(name="Eve"))
    updated = fresh_db.update_account(
        account.id, AccountCreate(name="renamed", person_id=other_person.id)
    )
    assert updated
    assert updated.name == "renamed"
    assert updated.person_id == other_person.id

    assert fresh_db.delete_account(account.id) is True
    assert fresh_db.get_account(account.id) is None


# ---------- Space ----------


def test_space_crud(fresh_db: Database):
    space = fresh_db.insert_space(SpaceCreate(name="Trip", description="Ski trip"))
    assert fresh_db.get_space(space.id) == space

    updated = fresh_db.update_space(space.id, SpaceCreate(name="Trip 2026"))
    assert updated
    assert updated.name == "Trip 2026"
    assert updated.description == ""

    assert fresh_db.delete_space(space.id) is True
    assert fresh_db.get_space(space.id) is None


# ---------- Relationship helpers (spaces/persons/accounts/users) ----------


@pytest.fixture
def world(fresh_db: Database):
    """A user in a space, with a person (and their account) also in that space."""
    user = fresh_db.insert_user(
        UserCreate(username="frank", email="frank@example.com", password="secret")
    )
    space = fresh_db.insert_space(SpaceCreate(name="Household"))
    fresh_db.insert_space_user(
        SpaceUserCreate(space_id=space.id, user_id=user.id, is_owner=True)
    )
    person = fresh_db.insert_person(PersonCreate(name="Grace"))
    fresh_db.insert_person_space(
        PersonSpaceCreate(person_id=person.id, space_id=space.id)
    )
    account = fresh_db.insert_account(
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
    assert db.get_spaces_by_user(user.id) == [space]


def test_get_users_by_space(world):
    db, user, space = world["db"], world["user"], world["space"]
    assert db.get_users_by_space(space.id) == [user]


def test_get_persons_by_space_and_by_user(world):
    db, user, space, person = (
        world["db"],
        world["user"],
        world["space"],
        world["person"],
    )
    assert db.get_persons_by_space(space.id) == [person]
    assert db.get_persons_by_user(user.id) == [person]


def test_get_accounts_by_user(world):
    db, user, account = world["db"], world["user"], world["account"]
    assert db.get_accounts_by_user(user.id) == [account]


def test_delete_space_user_and_person_space(world):
    db, user, space, person = (
        world["db"],
        world["user"],
        world["space"],
        world["person"],
    )
    assert db.delete_space_user(space.id, user.id) is True
    assert db.get_users_by_space(space.id) == []
    assert db.delete_space_user(space.id, user.id) is False

    assert db.delete_person_space(person.id, space.id) is True
    assert db.get_persons_by_space(space.id) == []


# ---------- Transaction / AccountTransaction (contributions) ----------


@pytest.fixture
def transaction_world(world):
    db, space, account = world["db"], world["space"], world["account"]
    transaction = db.insert_transaction(
        TransactionCreate(space_id=space.id, title="Groceries", date=date(2026, 1, 1))
    )
    contribution = db.insert_account_transaction(
        AccountTransactionCreate(
            account_id=account.id,
            transaction_id=transaction.id,
            amount_requested=50.0,
            amount_paid=50.0,
            is_initial=True,
        )
    )
    world["transaction"] = transaction
    world["contribution"] = contribution
    return world


def test_transaction_crud(transaction_world):
    db = transaction_world["db"]
    space = transaction_world["space"]
    transaction = transaction_world["transaction"]

    assert db.get_transaction(transaction.id) == transaction
    assert db.get_transactions_by_space(space.id) == [transaction]

    updated = db.update_transaction(
        transaction.id,
        TransactionCreate(
            space_id=space.id, title="Groceries v2", date=date(2026, 1, 2)
        ),
    )
    assert updated.title == "Groceries v2"

    assert db.delete_transaction(transaction.id) is True
    assert db.get_transaction(transaction.id) is None


def test_get_transactions_by_account_and_person(transaction_world):
    db = transaction_world["db"]
    account = transaction_world["account"]
    person = transaction_world["person"]
    transaction = transaction_world["transaction"]

    assert db.get_transactions_by_account(account.id) == [transaction]
    assert db.get_transactions_by_person(person.id) == [transaction]


def test_account_transaction_crud(transaction_world):
    db = transaction_world["db"]
    account = transaction_world["account"]
    transaction = transaction_world["transaction"]
    contribution = transaction_world["contribution"]

    assert db.get_account_transaction(account.id, transaction.id) == contribution
    assert db.get_account_transactions_by_transaction(transaction.id) == [contribution]

    updated = db.update_account_transaction(
        account.id,
        transaction.id,
        AccountTransactionCreate(
            account_id=account.id,
            transaction_id=transaction.id,
            amount_requested=75.0,
            amount_paid=25.0,
            is_initial=False,
        ),
    )
    assert updated.amount_requested == 75.0
    assert updated.amount_paid == 25.0

    assert db.delete_account_transaction(account.id, transaction.id) is True
    assert db.get_account_transaction(account.id, transaction.id) is None
