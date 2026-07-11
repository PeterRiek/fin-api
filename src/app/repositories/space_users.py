from app.models import SpaceUser
from app.repositories.base import BaseRepository
from app.schemas import SpaceUserCreate, SpaceUserOut


class SpaceUserRepository(BaseRepository):
    def insert(self, data: SpaceUserCreate) -> SpaceUserOut:
        with self.session() as s:
            space_user = SpaceUser(
                space_id=data.space_id,
                user_id=data.user_id,
                is_owner=data.is_owner,
            )
            s.add(space_user)
            s.flush()
            return SpaceUserOut.model_validate(space_user)

    def get(self, space_user_id: int) -> SpaceUserOut | None:
        with self.session() as s:
            row = s.query(SpaceUser).filter_by(id=space_user_id).first()
            return SpaceUserOut.model_validate(row) if row else None

    def get_all(self) -> list[SpaceUserOut]:
        with self.session() as s:
            rows = s.query(SpaceUser).all()
            return [SpaceUserOut.model_validate(r) for r in rows]

    def update(self, space_user_id: int, data: SpaceUserCreate) -> SpaceUserOut | None:
        with self.session() as s:
            space_user = s.query(SpaceUser).filter_by(id=space_user_id).first()
            if not space_user:
                return None
            space_user.space_id = data.space_id
            space_user.user_id = data.user_id
            space_user.is_owner = data.is_owner
            return SpaceUserOut.model_validate(space_user)

    def delete(self, space_id: int, user_id: int) -> bool:
        with self.session() as s:
            space_user = (
                s.query(SpaceUser).filter_by(space_id=space_id, user_id=user_id).first()
            )
            if not space_user:
                return False
            s.delete(space_user)
            return True
