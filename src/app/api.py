from fastapi import FastAPI

from app.routes import (
    accounts_router,
    auth_router,
    persons_router,
    spaces_router,
    transactions_router,
)

app = FastAPI(title="fin")
app.include_router(auth_router)
app.include_router(persons_router)
app.include_router(spaces_router)
app.include_router(transactions_router)
app.include_router(accounts_router)
