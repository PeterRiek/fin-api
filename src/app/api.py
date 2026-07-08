from fastapi import FastAPI

from app.routes import auth_router
from app.routes import split_router

app = FastAPI(title="fin")
app.include_router(auth_router)
app.include_router(split_router)
