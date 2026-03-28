"""Pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Create a registered user and return credentials + token."""
    user_data = {
        "organization_name": "Test Contractor LLC",
        "full_name": "John Doe",
        "email": "john@testcontractor.com",
        "password": "testpassword123",
    }

    # Register
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {
        "user_data": user_data,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def sample_spec_text():
    """Sample spec document text for testing extraction."""
    return """
    DIVISION 00 - PROCUREMENT AND CONTRACTING REQUIREMENTS

    SECTION 00 72 00 - GENERAL CONDITIONS

    PART 1 - GENERAL

    1.01 INSURANCE REQUIREMENTS
    Contractor shall maintain General Liability Insurance with limits of
    not less than $2,000,000 per occurrence and $5,000,000 aggregate.
    Workers Compensation insurance is required per state law.
    Certificate of Insurance must be provided prior to contract execution.

    1.02 BONDING REQUIREMENTS
    Performance Bond: 100% of contract value required.
    Payment Bond: 100% of contract value required.
    Bid Bond: 5% of bid amount required with proposal.
    Surety must be licensed in the state of project location.

    1.03 WARRANTY
    General Warranty: Contractor warrants all work for a period of
    two (2) years from date of Substantial Completion.
    Extended warranty of five (5) years required for roofing systems.

    1.04 LIQUIDATED DAMAGES
    Time is of the essence. Liquidated damages shall be assessed at
    the rate of $1,500 per calendar day for each day of delay beyond
    the scheduled completion date.

    DIVISION 23 - HEATING, VENTILATING, AND AIR CONDITIONING

    SECTION 23 05 00 - COMMON WORK RESULTS FOR HVAC

    PART 1 - GENERAL

    1.01 TESTING, ADJUSTING, AND BALANCING (TAB)
    Independent third-party TAB agency required.
    TAB contractor shall be AABC or NEBB certified.
    Complete TAB report required before final inspection.

    1.02 COMMISSIONING
    Commissioning Authority (CxA) has been engaged by Owner.
    Contractor shall coordinate with CxA for all functional testing.
    Pre-functional checklists required for all equipment.
    Functional Performance Testing (FPT) required.

    PART 2 - PRODUCTS

    2.01 SUBMITTALS
    Submit product data for all HVAC equipment.
    Shop drawings required for ductwork and piping.
    Operation and maintenance manuals required.
    """
