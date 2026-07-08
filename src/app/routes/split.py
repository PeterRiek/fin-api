from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user


split_router = APIRouter(prefix="/split", tags=["split"])


@split_router.get("/hello")
def hello(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user}"}
