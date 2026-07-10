from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.schemas import SpaceCreate, SpaceUserCreate, UserOut


split_router = APIRouter(prefix="/split", tags=["split"])

db = get_db()


@split_router.get("/hello")
def hello(current_user: UserOut = Depends(get_current_user)):
    return {"message": f"Hello {current_user}"}


"""
routes
in user scope:
    spaces:
        get
        create
        delete
        update
        users:
            add user
            remove user
        persons:
            add person
            get all transactions in space
    persons (access to any person user is in a space with):
        accounts:
            get
            create
            delete
            update
"""


"""
sites

# login/register

# spaces
- all spaces user is in
- open space
- create space

# spaces/<space>
- list all persons
- list all users
- list all transactions

"""


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
def get_space(space_id: int, current_user: UserOut = Depends(get_current_user)):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


@split_router.delete("/spaces/{space_id}", status_code=204)
def delete_space(space_id: int, current_user: UserOut = Depends(get_current_user)):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if db.delete_space(space_id):
        return
    raise HTTPException(status_code=500, detail="Failed to delete space")


@split_router.put("/spaces/{space_id}")
def update_space(
    space_id: int,
    space_data: SpaceCreate,
    current_user: UserOut = Depends(get_current_user),
):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    updated_space = db.update_space(space_id, space_data)
    if not updated_space:
        raise HTTPException(status_code=500, detail="Failed to update space")
    return updated_space


@split_router.get("/spaces/{space_id}/users")
def get_space_users(space_id: int, current_user: UserOut = Depends(get_current_user)):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return db.get_users_by_space(space_id)


@split_router.post("/spaces/{space_id}/users", status_code=201)
def add_space_user(
    space_id: int, user_id: int, current_user: UserOut = Depends(get_current_user)
):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    space_user_create = SpaceUserCreate(
        space_id=space_id, user_id=user_id, is_owner=False
    )
    space_user_out = db.insert_space_user(space_user_create)
    if not space_user_out:
        raise HTTPException(status_code=500, detail="Failed to add user to space")
    return space_user_out


@split_router.delete("/spaces/{space_id}/users/{user_id}", status_code=204)
def remove_space_user(
    space_id: int, user_id: int, current_user: UserOut = Depends(get_current_user)
):
    spaces = db.get_spaces_by_user(current_user.id)
    space = next((s for s in spaces if s.id == space_id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if db.delete_space_user(space_id, user_id):
        return
    raise HTTPException(status_code=500, detail="Failed to remove user from space")
