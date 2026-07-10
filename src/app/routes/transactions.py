from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import (
    _find_user_space,
    get_owned_account,
    get_owned_transaction,
)
from app.schemas import (
    AccountOut,
    ContributionCreate,
    TransactionCreate,
    TransactionDetailOut,
    TransactionOut,
    UserOut,
)

transactions_router = APIRouter(prefix="/split", tags=["transactions"])

db = get_db()


# --- Transactions ---


@transactions_router.get("/transactions/{transaction_id}")
def get_transaction(
    transaction: TransactionOut = Depends(get_owned_transaction),
) -> TransactionDetailOut:
    contributions = db.get_contribution_details_by_transaction(transaction.id)
    return TransactionDetailOut(
        id=transaction.id,
        space_id=transaction.space_id,
        title=transaction.title,
        description=transaction.description,
        date=transaction.date,
        created_at=transaction.created_at,
        contributions=contributions,
    )


@transactions_router.post("/transactions", status_code=201)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: UserOut = Depends(get_current_user),
):
    if not _find_user_space(current_user.id, transaction_data.space_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to create transaction in this space"
        )
    return db.insert_transaction(transaction_data)


@transactions_router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction: TransactionOut = Depends(get_owned_transaction)):
    if db.delete_transaction(transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete transaction")


@transactions_router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_data: TransactionCreate,
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_transaction = db.update_transaction(transaction.id, transaction_data)
    if not updated_transaction:
        raise HTTPException(status_code=500, detail="Failed to update transaction")
    return updated_transaction


# --- Contributions ---


@transactions_router.get("/transactions/{transaction_id}/contributions")
def get_transaction_contributions(
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    return db.get_account_transactions_by_transaction(transaction.id)


@transactions_router.get("/transactions/{transaction_id}/contributions/{account_id}")
def get_contribution(
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    contribution = db.get_account_transaction(account.id, transaction.id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contribution


@transactions_router.post(
    "/transactions/{transaction_id}/contributions", status_code=201
)
def create_contribution(
    contribution_data: ContributionCreate,
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


@transactions_router.put("/transactions/{transaction_id}/contributions/{account_id}")
def update_contribution(
    contribution_data: ContributionCreate,
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_contribution = db.update_account_transaction(
        account.id, transaction.id, contribution_data
    )
    if not updated_contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return updated_contribution


@transactions_router.delete(
    "/transactions/{transaction_id}/contributions/{account_id}", status_code=204
)
def delete_contribution(
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    if db.delete_account_transaction(account.id, transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove contribution")
