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
    CategoryOut,
    ContributionCreate,
    TransactionCategoryCreate,
    TransactionCategoryOut,
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
    contributions = db.contributions.get_details_by_transaction(transaction.id)
    categories = db.transaction_categories.get_categories_by_transaction(transaction.id)
    return TransactionDetailOut(
        id=transaction.id,
        space_id=transaction.space_id,
        title=transaction.title,
        description=transaction.description,
        date=transaction.date,
        type=transaction.type,
        linked_transaction_id=transaction.linked_transaction_id,
        created_at=transaction.created_at,
        contributions=contributions,
        categories=categories,
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
    return db.transactions.insert(transaction_data)


@transactions_router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction: TransactionOut = Depends(get_owned_transaction)):
    if db.transactions.delete(transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete transaction")


@transactions_router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_data: TransactionCreate,
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_transaction = db.transactions.update(transaction.id, transaction_data)
    if not updated_transaction:
        raise HTTPException(status_code=500, detail="Failed to update transaction")
    return updated_transaction


# --- Contributions ---


@transactions_router.get("/transactions/{transaction_id}/contributions")
def get_transaction_contributions(
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    return db.contributions.get_by_transaction(transaction.id)


@transactions_router.get("/transactions/{transaction_id}/contributions/{account_id}")
def get_contribution(
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    contribution = db.contributions.get(account.id, transaction.id)
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
    accounts = db.accounts.get_by_user(current_user.id)
    if not any(a.id == contribution_data.account_id for a in accounts):
        raise HTTPException(
            status_code=403, detail="Not authorized to use this account"
        )
    contribution_data.transaction_id = transaction.id
    return db.contributions.insert(contribution_data)


@transactions_router.put("/transactions/{transaction_id}/contributions/{account_id}")
def update_contribution(
    contribution_data: ContributionCreate,
    account: AccountOut = Depends(get_owned_account),
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    updated_contribution = db.contributions.update(
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
    if db.contributions.delete(account.id, transaction.id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove contribution")


# --- Categories ---


@transactions_router.get("/transactions/{transaction_id}/categories")
def get_transaction_categories(
    transaction: TransactionOut = Depends(get_owned_transaction),
) -> list[CategoryOut]:
    return db.transaction_categories.get_categories_by_transaction(transaction.id)


@transactions_router.post(
    "/transactions/{transaction_id}/categories", status_code=201
)
def add_transaction_category(
    category_id: int,
    transaction: TransactionOut = Depends(get_owned_transaction),
) -> TransactionCategoryOut:
    if not db.categories.get(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    link_data = TransactionCategoryCreate(
        transaction_id=transaction.id, category_id=category_id
    )
    return db.transaction_categories.insert(link_data)


@transactions_router.delete(
    "/transactions/{transaction_id}/categories/{category_id}", status_code=204
)
def remove_transaction_category(
    category_id: int,
    transaction: TransactionOut = Depends(get_owned_transaction),
):
    if db.transaction_categories.delete(transaction.id, category_id):
        return
    raise HTTPException(status_code=404, detail="Category not linked to transaction")
