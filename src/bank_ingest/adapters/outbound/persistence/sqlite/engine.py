"""SQLite engine factory."""

from pathlib import Path

from sqlalchemy import Engine, create_engine


def create_sqlite_engine(db_path: Path) -> Engine:
    """Create a SQLAlchemy engine connected to a SQLite database file.

    Args:
        db_path: Path to the SQLite database file. Parent directories
            are created if they don't exist.

    Returns:
        A configured SQLAlchemy Engine instance.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)
