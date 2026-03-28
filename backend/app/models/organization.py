"""Organization model - represents a contractor company (multi-tenant root)."""

import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    """
    Organization model - the multi-tenant root entity.
    Each contractor company is an Organization.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription"] = relationship(  # noqa: F821
        "Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"
