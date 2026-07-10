from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import _find_user_person, get_owned_account
from app.schemas import AccountCreate, AccountOut, UserOut

accounts_router = APIRouter(prefix="/split", tags=["accounts"])

db = get_db()


@accounts_router.get("/accounts")
def get_accounts(current_user: UserOut = Depends(get_current_user)):
    return db.get_accounts_by_user(current_user.id)


@accounts_router.post("/accounts", status_code=201)
def create_account(
    account_data: AccountCreate, current_user: UserOut = Depends(get_current_user)
):
    if not _find_user_person(current_user.id, account_data.person_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create account for this person"
        )
    return db.insert_account(account_data)


@accounts_router.get("/accounts/{account_id}")
def get_account(account: AccountOut = Depends(get_owned_account)):
    return account


@accounts_router.put("/accounts/{account_id}")
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


@accounts_router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account: AccountOut = Depends(get_owned_account)):
    if db.delete_account(account.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete account")


@accounts_router.get("/accounts/{account_id}/transactions")
def get_account_transactions(account: AccountOut = Depends(get_owned_account)):
    return db.get_transactions_by_account(account.id)
