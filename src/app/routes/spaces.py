from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.routes.ownership import get_owned_space, get_owned_space_as_owner
from app.schemas import (
    PersonBalanceOut,
    PersonSpaceCreate,
    SpaceCreate,
    SpaceOut,
    SpaceOverviewOut,
    SpaceSummaryOut,
    SpaceUserCreate,
    UserOut,
)

spaces_router = APIRouter(prefix="/split", tags=["spaces"])

db = get_db()


# --- Spaces ---


@spaces_router.get("/spaces")
def get_spaces(
    current_user: UserOut = Depends(get_current_user),
) -> list[SpaceSummaryOut]:
    return db.spaces.get_summaries_by_user(current_user.id)


@spaces_router.post("/spaces", status_code=201)
def create_space(
    space_data: SpaceCreate, current_user: UserOut = Depends(get_current_user)
):
    space = db.spaces.insert(space_data)
    space_user = SpaceUserCreate(
        space_id=space.id, user_id=current_user.id, is_owner=True
    )
    db.space_users.insert(space_user)
    return space


@spaces_router.get("/spaces/{space_id}")
def get_space(space: SpaceOut = Depends(get_owned_space)):
    return space


@spaces_router.delete("/spaces/{space_id}", status_code=204)
def delete_space(space: SpaceOut = Depends(get_owned_space_as_owner)):
    if db.spaces.delete(space.id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete space")


@spaces_router.put("/spaces/{space_id}")
def update_space(
    space_data: SpaceCreate,
    space: SpaceOut = Depends(get_owned_space),
):
    updated_space = db.spaces.update(space.id, space_data)
    if not updated_space:
        raise HTTPException(status_code=500, detail="Failed to update space")
    return updated_space


# --- Users in Space ---


@spaces_router.get("/spaces/{space_id}/users")
def get_space_users(space: SpaceOut = Depends(get_owned_space)):
    return db.users.get_by_space(space.id)


@spaces_router.post("/spaces/{space_id}/users", status_code=201)
def add_space_user(user_id: int, space: SpaceOut = Depends(get_owned_space_as_owner)):
    if db.space_users.exists(space.id, user_id):
        raise HTTPException(
            status_code=400, detail="User is already a member of this space"
        )
    space_user_create = SpaceUserCreate(
        space_id=space.id, user_id=user_id, is_owner=False
    )
    space_user_out = db.space_users.insert(space_user_create)
    if not space_user_out:
        raise HTTPException(status_code=500, detail="Failed to add user to space")
    return space_user_out


@spaces_router.delete("/spaces/{space_id}/users/{user_id}", status_code=204)
def remove_space_user(
    user_id: int,
    space: SpaceOut = Depends(get_owned_space),
    current_user: UserOut = Depends(get_current_user),
):
    if db.space_users.is_owner(space.id, user_id):
        raise HTTPException(status_code=403, detail="Cannot remove the space owner")
    if user_id != current_user.id and not db.space_users.is_owner(
        space.id, current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Only the space owner can remove other users"
        )
    if db.space_users.delete(space.id, user_id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove user from space")


# --- Persons in Space ---


@spaces_router.get("/spaces/{space_id}/persons")
def get_space_persons(space: SpaceOut = Depends(get_owned_space)):
    return db.persons.get_by_space(space.id)


@spaces_router.post("/spaces/{space_id}/persons", status_code=201)
def add_space_person(person_id: int, space: SpaceOut = Depends(get_owned_space)):
    person_space_create = PersonSpaceCreate(space_id=space.id, person_id=person_id)
    person_space_out = db.person_spaces.insert(person_space_create)
    if not person_space_out:
        raise HTTPException(status_code=500, detail="Failed to add person to space")
    return person_space_out


@spaces_router.delete("/spaces/{space_id}/persons/{person_id}", status_code=204)
def remove_space_person(person_id: int, space: SpaceOut = Depends(get_owned_space)):
    if db.person_spaces.delete(person_id, space.id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove person from space")


@spaces_router.get("/spaces/{space_id}/transactions")
def get_space_transactions(space: SpaceOut = Depends(get_owned_space)):
    return db.transactions.get_by_space(space.id)


# --- Composite views ---


@spaces_router.get("/spaces/{space_id}/overview")
def get_space_overview(
    space: SpaceOut = Depends(get_owned_space),
) -> SpaceOverviewOut:
    transactions = db.transactions.get_by_space(space.id)
    recent_transactions = sorted(transactions, key=lambda t: t.date, reverse=True)[:5]
    return SpaceOverviewOut(
        id=space.id,
        name=space.name,
        description=space.description,
        created_at=space.created_at,
        users=db.users.get_by_space(space.id),
        persons=db.persons.get_by_space(space.id),
        transaction_count=len(transactions),
        recent_transactions=recent_transactions,
    )


@spaces_router.get("/spaces/{space_id}/balances")
def get_space_balances(
    space: SpaceOut = Depends(get_owned_space),
) -> list[PersonBalanceOut]:
    return db.spaces.get_person_balances(space.id)
