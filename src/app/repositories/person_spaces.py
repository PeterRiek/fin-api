from app.models import PersonSpace
from app.repositories.base import BaseRepository
from app.schemas import PersonSpaceCreate, PersonSpaceOut


class PersonSpaceRepository(BaseRepository):
    def insert(self, data: PersonSpaceCreate) -> PersonSpaceOut:
        with self.session() as s:
            person_space = PersonSpace(
                person_id=data.person_id,
                space_id=data.space_id,
            )
            s.add(person_space)
            s.flush()
            return PersonSpaceOut.model_validate(person_space)

    def get(self, person_id: int, space_id: int) -> PersonSpaceOut | None:
        with self.session() as s:
            row = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            return PersonSpaceOut.model_validate(row) if row else None

    def get_all(self) -> list[PersonSpaceOut]:
        with self.session() as s:
            rows = s.query(PersonSpace).all()
            return [PersonSpaceOut.model_validate(r) for r in rows]

    def update(
        self, person_id: int, space_id: int, data: PersonSpaceCreate
    ) -> PersonSpaceOut | None:
        with self.session() as s:
            person_space = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            if not person_space:
                return None
            person_space.person_id = data.person_id
            person_space.space_id = data.space_id
            return PersonSpaceOut.model_validate(person_space)

    def delete(self, person_id: int, space_id: int) -> bool:
        with self.session() as s:
            person_space = (
                s.query(PersonSpace)
                .filter_by(person_id=person_id, space_id=space_id)
                .first()
            )
            if not person_space:
                return False
            s.delete(person_space)
            return True
