from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import _find_user_person, _find_user_space, get_owned_account
from app.schemas import (
    AccountBalanceOut,
    AccountCreate,
    AccountOut,
    SimpleTransactionCreate,
    TransactionDetailOut,
    TransferCreate,
    TransferOut,
    UserOut,
)

accounts_router = APIRouter(prefix="/split", tags=["accounts"])

db = get_db()


@accounts_router.get("/accounts")
def get_accounts(current_user: UserOut = Depends(get_current_user)):
    return db.accounts.get_by_user(current_user.id)


@accounts_router.post("/accounts", status_code=201)
def create_account(
    account_data: AccountCreate, current_user: UserOut = Depends(get_current_user)
):
    if not _find_user_person(current_user.id, account_data.person_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create account for this person"
        )
    return db.accounts.insert(account_data)


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
    updated_account = db.accounts.update(account.id, account_data)
    if not updated_account:
        raise HTTPException(status_code=500, detail="Failed to update account")
    return updated_account


@accounts_router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account: AccountOut = Depends(get_owned_account)):
    if db.accounts.delete(account.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete account")


@accounts_router.get("/accounts/{account_id}/transactions")
def get_account_transactions(
    account: AccountOut = Depends(get_owned_account),
) -> list[TransactionDetailOut]:
    return db.transactions.get_by_account(account.id)


@accounts_router.get("/accounts/{account_id}/balance")
def get_account_balance(
    account: AccountOut = Depends(get_owned_account),
) -> AccountBalanceOut:
    return db.accounts.get_balance(account.id)


@accounts_router.post("/accounts/{account_id}/transactions", status_code=201)
def create_account_transaction(
    transaction_data: SimpleTransactionCreate,
    account: AccountOut = Depends(get_owned_account),
    current_user: UserOut = Depends(get_current_user),
) -> TransactionDetailOut:
    if not _find_user_space(current_user.id, transaction_data.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create transaction in this space"
        )
    return db.accounts.create_transaction(account.id, transaction_data)


@accounts_router.post("/accounts/{account_id}/transfers", status_code=201)
def create_transfer(
    transfer_data: TransferCreate,
    account: AccountOut = Depends(get_owned_account),
    current_user: UserOut = Depends(get_current_user),
) -> TransferOut:
    if not _find_user_space(current_user.id, transfer_data.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create transaction in this space"
        )
    if transfer_data.to_account_id == account.id:
        raise HTTPException(
            status_code=400, detail="Cannot transfer to the same account"
        )
    if not db.accounts.get(transfer_data.to_account_id):
        raise HTTPException(status_code=404, detail="Destination account not found")
    return db.accounts.create_transfer(account.id, transfer_data)
