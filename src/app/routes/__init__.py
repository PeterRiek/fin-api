"""
routes
- auth/user creation login
- spaces (create, update, delete, list)
- space add transaction (create, update, delete, list)
- accounts
- persons
"""

from app.routes.auth import auth_router
from app.routes.split import split_router

__all__ = ["auth_router", "split_router"]
