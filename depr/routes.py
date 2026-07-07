from fastapi import APIRouter, Depends, HTTPException
from app.database import Database
from app.dependencies import get_db
from app.schemas import AccountResponse, CategoryResponse, PersonResponse, TransactionCreate, NameSchema, TransactionResponse

router = APIRouter(prefix="/tricount")


# --- Accounts ---


@router.post("/accounts", status_code=201)
def create_account(body: NameSchema, db: Database = Depends(get_db)):
    return {"id": db.insert_account(body.name)}


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(db: Database = Depends(get_db)):
    return db.get_accounts()


@router.get("/accounts/{id}", response_model=AccountResponse)
def get_account(id: int, db: Database = Depends(get_db)):
    account = db.get_account(id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/accounts/{id}")
def update_account(id: int, body: NameSchema, db: Database = Depends(get_db)):
    if not db.update_account(id, body.name):
        raise HTTPException(status_code=404, detail="Account not found")
    return {"ok": True}


@router.delete("/accounts/{id}", status_code=204)
def delete_account(id: int, db: Database = Depends(get_db)):
    if not db.delete_account(id):
        raise HTTPException(status_code=404, detail="Account not found")


# --- Categories ---


@router.post("/categories", status_code=201)
def create_category(body: NameSchema, db: Database = Depends(get_db)):
    return {"id": db.insert_category(body.name)}


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Database = Depends(get_db)):
    return db.get_categories()


@router.get("/categories/{id}", response_model=CategoryResponse)
def get_category(id: int, db: Database = Depends(get_db)):
    category = db.get_category(id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{id}")
def update_category(id: int, body: NameSchema, db: Database = Depends(get_db)):
    if not db.update_category(id, body.name):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"ok": True}


@router.delete("/categories/{id}", status_code=204)
def delete_category(id: int, db: Database = Depends(get_db)):
    if not db.delete_category(id):
        raise HTTPException(status_code=404, detail="Category not found")


# --- Persons ---


@router.post("/persons", status_code=201)
def create_person(body: NameSchema, db: Database = Depends(get_db)):
    return {"id": db.insert_person(body.name)}


@router.get("/persons", response_model=list[PersonResponse])
def list_persons(db: Database = Depends(get_db)):
    return db.get_persons()


@router.get("/persons/{id}", response_model=PersonResponse)
def get_person(id: int, db: Database = Depends(get_db)):
    person = db.get_person(id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.put("/persons/{id}")
def update_person(id: int, body: NameSchema, db: Database = Depends(get_db)):
    if not db.update_person(id, body.name):
        raise HTTPException(status_code=404, detail="Person not found")
    return {"ok": True}


@router.delete("/persons/{id}", status_code=204)
def delete_person(id: int, db: Database = Depends(get_db)):
    if not db.delete_person(id):
        raise HTTPException(status_code=404, detail="Person not found")


# --- Transactions ---


@router.post("/transactions", status_code=201)
def create_transaction(transaction: TransactionCreate, db: Database = Depends(get_db)):
    return {"id": db.insert_transaction(transaction)}


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(db: Database = Depends(get_db)):
    return db.get_transactions()


@router.get("/transactions/{id}", response_model=TransactionResponse)
def get_transaction(id: int, db: Database = Depends(get_db)):
    transaction = db.get_transaction(id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/transactions/{id}")
def update_transaction(
    id: int, transaction: TransactionCreate, db: Database = Depends(get_db)
):
    if not db.update_transaction(id, transaction):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}


@router.delete("/transactions/{id}", status_code=204)
def delete_transaction(id: int, db: Database = Depends(get_db)):
    if not db.delete_transaction(id):
        raise HTTPException(status_code=404, detail="Transaction not found")
