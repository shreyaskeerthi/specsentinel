"""SQLAlchemy models — User, Project, TeamMember, Milestone, Analysis."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship

from app.db import Base


def gen_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    bid_due_date = Column(String, nullable=True)

    # Money
    contract_value = Column(Float, nullable=True)
    budget = Column(Float, nullable=True)
    contingency_percent = Column(Float, nullable=True)

    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="projects")
    team_members = relationship("TeamMember", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan", order_by="Milestone.date")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    invited = Column(String, default="no")
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="team_members")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    date = Column(String, nullable=False)  # ISO date
    phase = Column(String, nullable=False)  # preconstruction, construction, closeout
    type = Column(String, default="milestone")  # milestone, deadline, task, blackout, meeting
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, missed
    assignee = Column(String, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="milestones")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=True)
    source_type = Column(String, default="document")
    status = Column(String, default="pending")
    error_message = Column(Text, nullable=True)

    page_count = Column(Float, nullable=True)
    extraction_data = Column(JSON, nullable=True)
    risk_report = Column(JSON, nullable=True)
    division_data = Column(JSON, nullable=True)
    action_board = Column(JSON, nullable=True)
    meeting_result = Column(JSON, nullable=True)
    email_set = Column(JSON, nullable=True)
    chunks_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="analyses")
