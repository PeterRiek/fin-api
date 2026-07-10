from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import get_owned_person
from app.schemas import PersonCreate, PersonOut, UserOut

persons_router = APIRouter(prefix="/split", tags=["persons"])

db = get_db()


@persons_router.get("/persons")
def get_persons(current_user: UserOut = Depends(get_current_user)):
    return db.get_persons_by_user(current_user.id)


@persons_router.post("/persons", status_code=201)
def create_person(person_data: PersonCreate, _: UserOut = Depends(get_current_user)):
    return db.insert_person(person_data)


@persons_router.get("/persons/{person_id}")
def get_person(person: PersonOut = Depends(get_owned_person)):
    return person


@persons_router.put("/persons/{person_id}")
def update_person(
    person_data: PersonCreate,
    person: PersonOut = Depends(get_owned_person),
):
    updated_person = db.update_person(person.id, person_data)
    if not updated_person:
        raise HTTPException(status_code=500, detail="Failed to update person")
    return updated_person


@persons_router.delete("/persons/{person_id}", status_code=204)
def delete_person(person: PersonOut = Depends(get_owned_person)):
    if db.delete_person(person.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete person")


@persons_router.get("/persons/{person_id}/transactions")
def get_person_transactions(person: PersonOut = Depends(get_owned_person)):
    return db.get_transactions_by_person(person.id)


@persons_router.get("/persons/{person_id}/accounts")
def get_person_accounts(person: PersonOut = Depends(get_owned_person)):
    return db.get_accounts_by_person(person.id)
