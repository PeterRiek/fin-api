"""
routes
- auth/user creation login
- persons
- spaces (create, update, delete, list; users and persons in space)
- transactions (create, update, delete, list; contributions)
- accounts
- categories
"""

from app.routes.accounts import accounts_router
from app.routes.auth import auth_router
from app.routes.categories import categories_router
from app.routes.persons import persons_router
from app.routes.spaces import spaces_router
from app.routes.transactions import transactions_router

__all__ = [
    "accounts_router",
    "auth_router",
    "categories_router",
    "persons_router",
    "spaces_router",
    "transactions_router",
]
