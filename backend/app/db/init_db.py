"""Database initialization and seeding utilities."""

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Initialize database tables."""
    # Import all models to ensure they're registered with Base
    from app.models import organization, user, project, document, analysis, subscription  # noqa

    Base.metadata.create_all(bind=engine)


def seed_db(db: Session) -> None:
    """Seed database with initial data (for development)."""
    # TODO: Add seed data for development/testing
    pass
