"""User model - belongs to an Organization with role-based access."""

import uuid
from enum import Enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, Enum):
    """User roles within an organization."""
    OWNER = "owner"
    ADMIN = "admin"
    ESTIMATOR = "estimator"
    VIEWER = "viewer"


class User(Base, TimestampMixin):
    """
    User model - belongs to an Organization.
    Has role-based permissions within the org.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.ESTIMATOR)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
