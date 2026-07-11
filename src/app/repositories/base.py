from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker


class BaseRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    @contextmanager
    def session(self):
        s = self._session_factory()
        try:
            yield s
            s.commit()
        except:
            s.rollback()
            raise
        finally:
            s.close()
