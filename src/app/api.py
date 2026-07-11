from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    accounts_router,
    auth_router,
    categories_router,
    persons_router,
    spaces_router,
    transactions_router,
)

app = FastAPI(title="fin")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(persons_router)
app.include_router(spaces_router)
app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(categories_router)
