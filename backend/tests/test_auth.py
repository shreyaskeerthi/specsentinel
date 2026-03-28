"""Tests for authentication endpoints."""

import pytest


def test_register_success(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "ACME Contractors",
            "full_name": "Jane Smith",
            "email": "jane@acme.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@acme.com"
    assert data["full_name"] == "Jane Smith"
    assert data["role"] == "owner"
    assert "id" in data
    assert "organization_id" in data


def test_register_duplicate_email(client):
    """Test registration fails with duplicate email."""
    user_data = {
        "organization_name": "First Org",
        "full_name": "First User",
        "email": "duplicate@test.com",
        "password": "password123",
    }

    # First registration
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with same email
    user_data["organization_name"] = "Second Org"
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]


def test_login_success(client, registered_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["user_data"]["email"],
            "password": registered_user["user_data"]["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_json_endpoint(client, registered_user):
    """Test JSON login endpoint."""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": registered_user["user_data"]["email"],
            "password": registered_user["user_data"]["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client, registered_user):
    """Test login fails with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["user_data"]["email"],
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login fails for nonexistent user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nobody@nowhere.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401


def test_get_me(client, registered_user):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/auth/me",
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["user_data"]["email"]
    assert data["full_name"] == registered_user["user_data"]["full_name"]


def test_get_me_unauthorized(client):
    """Test getting user info without token fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """Test getting user info with invalid token fails."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
