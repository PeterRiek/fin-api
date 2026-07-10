from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.schemas import (
    AccountCreate,
    AccountOut,
    AccountTransactionCreate,
    PersonCreate,
    PersonOut,
    PersonSpaceCreate,
    SpaceCreate,
    SpaceOut,
    SpaceUserCreate,
    TransactionCreate,
    TransactionOut,
    UserOut,
)


split_router = APIRouter(prefix="/split", tags=["split"])

db = get_db()


# --- Ownership dependencies ---


def _find_user_space(user_id: int, space_id: int) -> SpaceOut | None:
    spaces = db.get_spaces_by_user(user_id)
    return next((s for s in spaces if s.id == space_id), None)


def get_owned_space(
    space_id: int, current_user: UserOut = Depends(get_current_user)
) -> SpaceOut:
    space = _find_user_space(current_user.id, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


def _find_user_person(user_id: int, person_id: int) -> PersonOut | None:
    persons = db.get_persons_by_user(user_id)
    return next((p for p in persons if p.id == person_id), None)


def get_owned_person(
    person_id: int, current_user: UserOut = Depends(get_current_user)
) -> PersonOut:
    person = _find_user_person(current_user.id, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


def get_owned_account(
    account_id: int, current_user: UserOut = Depends(get_current_user)
) -> AccountOut:
    accounts = db.get_accounts_by_user(current_user.id)
    account = next((a for a in accounts if a.id == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def get_owned_transaction(
    transaction_id: int, current_user: UserOut = Depends(get_current_user)
) -> TransactionOut:
    transaction = db.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not _find_user_space(current_user.id, transaction.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this transaction"
        )
    return transaction


# --- Persons ---


@split_router.get("/persons")
def get_persons(current_user: UserOut = Depends(get_current_user)):
    return db.get_persons_by_user(current_user.id)


@split_router.post("/persons", status_code=201)
def create_person(person_data: PersonCreate, _: UserOut = Depends(get_current_user)):
    person = db.insert_person(person_data)
    return person


@split_router.get("/persons/{person_id}")
def get_person(person: PersonOut = Depends(get_owned_person)):
    return person


@split_router.put("/persons/{person_id}")
def update_person(
    person_data: PersonCreate,
    person: PersonOut = Depends(get_owned_person),
):
    updated_person = db.update_person(person.id, person_data)
    if not updated_person:
        raise HTTPException(status_code=500, detail="Failed to update person")
    return updated_person


@split_router.delete("/persons/{person_id}", status_code=204)
def delete_person(person: PersonOut = Depends(get_owned_person)):
    if db.delete_person(person.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete person")


@split_router.get("/persons/{person_id}/transactions")
def get_person_transactions(person: PersonOut = Depends(get_owned_person)):
    return db.get_transactions_by_person(person.id)


@split_router.get("/persons/{person_id}/accounts")
def get_person_accounts(person: PersonOut = Depends(get_owned_person)):
    return db.get_accounts_by_person(person.id)


# --- Spaces ---


@split_router.get("/spaces")
def get_spaces(current_user: UserOut = Depends(get_current_user)):
    return db.get_spaces_by_user(current_user.id)


@split_router.post("/spaces", status_code=201)
def create_space(
    space_data: SpaceCreate, current_user: UserOut = Depends(get_current_user)
):
    space = db.insert_space(space_data)
    space_user = SpaceUserCreate(
        space_id=space.id, user_id=current_user.id, is_owner=True
    )
    db.insert_space_user(space_user)
    return space


@split_router.get("/spaces/{space_id}")
def get_space(space: SpaceOut = Depends(get_owned_space)):
    return space


@split_router.delete("/spaces/{space_id}", status_code=204)
def delete_space(space: SpaceOut = Depends(get_owned_space)):
    if db.delete_space(space.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete space")


@split_router.put("/spaces/{space_id}")
def update_space(
    space_data: SpaceCreate,
    space: SpaceOut = Depends(get_owned_space),
):
    updated_space = db.update_space(space.id, space_data)
    if not updated_space:
        raise HTTPException(status_code=500, detail="Failed to update space")
    return updated_space


# --- Users in Space ---


@split_router.get("/spaces/{space_id}/users")
def get_space_users(space: SpaceOut = Depends(get_owned_space)):
    return db.get_users_by_space(space.id)


@split_router.post("/spaces/{space_id}/users", status_code=201)
def add_space_user(user_id: int, space: SpaceOut = Depends(get_owned_space)):
    space_user_create = SpaceUserCreate(
        space_id=space.id, user_id=user_id, is_owner=False
    )
    space_user_out = db.insert_space_user(space_user_create)
    if not space_user_out:
        raise HTTPException(status_code=500, detail="Failed to add user to space")
    return space_user_out


@split_router.delete("/spaces/{space_id}/users/{user_id}", status_code=204)
def remove_space_user(user_id: int, space: SpaceOut = Depends(get_owned_space)):
    if db.delete_space_user(space.id, user_id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove user from space")


# --- Persons in Space ---


@split_router.get("/spaces/{space_id}/persons")
def get_space_persons(space: SpaceOut = Depends(get_owned_space)):
    return db.get_persons_by_space(space.id)


@split_router.post("/spaces/{space_id}/persons", status_code=201)
def add_space_person(person_id: int, space: SpaceOut = Depends(get_owned_space)):
    person_space_create = PersonSpaceCreate(space_id=space.id, person_id=person_id)
    person_space_out = db.insert_person_space(person_space_create)
    if not person_space_out:
        raise HTTPException(status_code=500, detail="Failed to add person to space")
    return person_space_out


@split_router.delete("/spaces/{space_id}/persons/{person_id}", status_code=204)
def remove_space_person(person_id: int, space: SpaceOut = Depends(get_owned_space)):
    if db.delete_person_space(space.id, person_id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove person from space")


@split_router.get("/spaces/{space_id}/transactions")
def get_space_transactions(space: SpaceOut = Depends(get_owned_space)):
    return db.get_transactions_by_space(space.id)


# --- Transactions ---


@split_router.get("/transactions/{transaction_id}")
def get_transaction(transaction: TransactionOut = Depends(get_owned_transaction)):
    return transaction


@split_router.post("/transactions", status_code=201)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: UserOut = Depends(get_current_user),
):
    if not _find_user_space(current_user.id, transaction_data.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create transaction in this space"
        )
    return db.insert_transaction(transaction_data)


@split_router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction: TransactionOut = Depends(get_owned_transaction)):
    if db.delete_transaction(transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete transaction")


@split_router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_data: TransactionCreate,
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_transaction = db.update_transaction(transaction.id, transaction_data)
    if not updated_transaction:
        raise HTTPException(status_code=500, detail="Failed to update transaction")
    return updated_transaction


# --- Contributions ---


@split_router.get("/transactions/{transaction_id}/contributions")
def get_transaction_contributions(
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    return db.get_account_transactions_by_transaction(transaction.id)


@split_router.get("/transactions/{transaction_id}/contributions/{account_id}")
def get_contribution(
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    contribution = db.get_account_transaction(account.id, transaction.id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contribution


@split_router.post("/transactions/{transaction_id}/contributions", status_code=201)
def create_contribution(
    contribution_data: AccountTransactionCreate,
    transaction: TransactionOut = Depends(get_owned_transaction),
    current_user: UserOut = Depends(get_current_user),
):
    accounts = db.get_accounts_by_user(current_user.id)
    if not any(a.id == contribution_data.account_id for a in accounts):
        raise HTTPException(
            status_code=403, detail="Not authorized to use this account"
        )
    contribution_data.transaction_id = transaction.id
    return db.insert_account_transaction(contribution_data)


@split_router.put("/transactions/{transaction_id}/contributions/{account_id}")
def update_contribution(
    contribution_data: AccountTransactionCreate,
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_contribution = db.update_account_transaction(
        account.id, transaction.id, contribution_data
    )
    if not updated_contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return updated_contribution


@split_router.delete(
    "/transactions/{transaction_id}/contributions/{account_id}", status_code=204
)
def delete_contribution(
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    if db.delete_account_transaction(account.id, transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove contribution")


# --- Accounts ---


@split_router.get("/accounts")
def get_accounts(current_user: UserOut = Depends(get_current_user)):
    return db.get_accounts_by_user(current_user.id)


@split_router.post("/accounts", status_code=201)
def create_account(
    account_data: AccountCreate, current_user: UserOut = Depends(get_current_user)
):
    if not _find_user_person(current_user.id, account_data.person_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create account for this person"
        )
    return db.insert_account(account_data)


@split_router.get("/accounts/{account_id}")
def get_account(account: AccountOut = Depends(get_owned_account)):
    return account


@split_router.put("/accounts/{account_id}")
def update_account(
    account_data: AccountCreate,
    account: AccountOut = Depends(get_owned_account),
    current_user: UserOut = Depends(get_current_user),
):
    if not _find_user_person(current_user.id, account_data.person_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to assign account to this person"
        )
    updated_account = db.update_account(account.id, account_data)
    if not updated_account:
        raise HTTPException(status_code=500, detail="Failed to update account")
    return updated_account


@split_router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account: AccountOut = Depends(get_owned_account)):
    if db.delete_account(account.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete account")


@split_router.get("/accounts/{account_id}/transactions")
def get_account_transactions(account: AccountOut = Depends(get_owned_account)):
    return db.get_transactions_by_account(account.id)
