"""Unit of Work for managing SQLAlchemy session lifecycle."""

from types import TracebackType

from sqlalchemy import Engine
from sqlalchemy.orm import Session


class UnitOfWork:
    """Context manager that provides a transactional session.

    Usage::

        with UnitOfWork(engine) as session:
            repo = SqlAlchemyEventRepository(session)
            repo.save(event)
        # auto-commits on success, rolls back on exception
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._session: Session | None = None

    def __enter__(self) -> Session:
        self._session = Session(self._engine)
        return self._session

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork.__exit__ called without an active session")
        if exc_type is not None:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()
        self._session = None
