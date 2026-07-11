from datetime import datetime

from app.models import SpaceUser, User
from app.repositories.base import BaseRepository
from app.schemas import UserCreate, UserOut
from app.security import hash_password, verify_password


class UserRepository(BaseRepository):
    def insert(self, data: UserCreate) -> UserOut:
        with self.session() as s:
            user = User(
                username=data.username,
                email=data.email,
                password_hash=hash_password(data.password),  # hash before storing
                created_at=datetime.now(),
            )
            s.add(user)
            s.flush()
            return UserOut.model_validate(user)  # built while session is still open

    def get(self, user_id: int) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(id=user_id).first()
            return UserOut.model_validate(row) if row else None

    def get_by_username(self, username: str) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(username=username).first()
            return UserOut.model_validate(row) if row else None

    def authenticate(self, username: str, password: str) -> UserOut | None:
        with self.session() as s:
            row = s.query(User).filter_by(username=username).first()
            if row is None or not verify_password(password, row.password_hash):
                return None
            return UserOut.model_validate(row)

    def get_all(self) -> list[UserOut]:
        with self.session() as s:
            rows = s.query(User).all()
            return [UserOut.model_validate(r) for r in rows]

    def get_by_space(self, space_id: int) -> list[UserOut]:
        with self.session() as s:
            rows = (
                s.query(User)
                .join(SpaceUser, User.id == SpaceUser.user_id)
                .filter(SpaceUser.space_id == space_id)
                .all()
            )
            return [UserOut.model_validate(r) for r in rows]

    def update(self, user_id: int, data: UserCreate) -> UserCreate | None:
        with self.session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return None
            user.username = data.username
            user.email = data.email
            user.password_hash = hash_password(data.password)
            return UserCreate.model_validate(user)

    def delete(self, user_id: int) -> bool:
        with self.session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            s.delete(user)
            return True
