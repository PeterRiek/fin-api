from fastapi import APIRouter, HTTPException, Depends

from app.dependencies import get_db
from app.routes.auth import get_current_user
from app.schemas import CategoryCreate, CategoryOut, UserOut

categories_router = APIRouter(prefix="/split", tags=["categories"])

db = get_db()


@categories_router.get("/categories")
def get_categories() -> list[CategoryOut]:
    return db.get_categories()


@categories_router.post("/categories", status_code=201)
def create_category(
    category_data: CategoryCreate, _: UserOut = Depends(get_current_user)
) -> CategoryOut:
    return db.insert_category(category_data)


@categories_router.get("/categories/{category_id}")
def get_category(category_id: int) -> CategoryOut:
    category = db.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@categories_router.put("/categories/{category_id}")
def update_category(
    category_id: int,
    category_data: CategoryCreate,
    _: UserOut = Depends(get_current_user),
) -> CategoryOut:
    updated_category = db.update_category(category_id, category_data)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@categories_router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, _: UserOut = Depends(get_current_user)):
    if db.delete_category(category_id):
        return
    raise HTTPException(status_code=404, detail="Category not found")
