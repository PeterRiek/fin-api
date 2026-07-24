from fastapi import Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.schemas import AccountOut, PersonOut, SpaceOut, TransactionOut, UserOut

db = get_db()


def _find_user_space(user_id: int, space_id: int) -> SpaceOut | None:
    spaces = db.spaces.get_by_user(user_id)
    return next((s for s in spaces if s.id == space_id), None)


def get_owned_space(
    space_id: int, current_user: UserOut = Depends(get_current_user)
) -> SpaceOut:
    space = _find_user_space(current_user.id, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


def _find_user_person(user_id: int, person_id: int) -> PersonOut | None:
    persons = db.persons.get_by_user(user_id)
    return next((p for p in persons if p.id == person_id), None)


def get_owned_space_as_owner(
    space: SpaceOut = Depends(get_owned_space),
    current_user: UserOut = Depends(get_current_user),
) -> SpaceOut:
    if not db.space_users.is_owner(space.id, current_user.id):
        raise HTTPException(
            status_code=403, detail="Only the space owner can perform this action"
        )
    return space


def get_owned_person(
    person_id: int, current_user: UserOut = Depends(get_current_user)
) -> PersonOut:
    person = _find_user_person(current_user.id, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


def get_exclusively_owned_person(
    person: PersonOut = Depends(get_owned_person),
    current_user: UserOut = Depends(get_current_user),
) -> PersonOut:
    if not db.persons.is_exclusive_to_user(person.id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Cannot modify a person shared with another space",
        )
    return person


def _find_user_account(user_id: int, account_id: int) -> AccountOut | None:
    accounts = db.accounts.get_by_user(user_id)
    return next((a for a in accounts if a.id == account_id), None)


def get_owned_account(
    account_id: int, current_user: UserOut = Depends(get_current_user)
) -> AccountOut:
    account = _find_user_account(current_user.id, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def get_owned_transaction(
    transaction_id: int, current_user: UserOut = Depends(get_current_user)
) -> TransactionOut:
    transaction = db.transactions.get(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not _find_user_space(current_user.id, transaction.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this transaction"
        )
    return transaction
