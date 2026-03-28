"""Tests for project endpoints."""

import pytest
from datetime import date


def test_create_project(client, registered_user):
    """Test creating a new project."""
    response = client.post(
        "/api/v1/projects/",
        headers=registered_user["headers"],
        json={
            "name": "City Hall HVAC Renovation",
            "client_name": "City of Springfield",
            "description": "Complete HVAC system replacement",
            "bid_due_date": "2024-03-15",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "City Hall HVAC Renovation"
    assert data["client_name"] == "City of Springfield"
    assert data["status"] == "active"
    assert "id" in data


def test_create_project_minimal(client, registered_user):
    """Test creating project with minimal data."""
    response = client.post(
        "/api/v1/projects/",
        headers=registered_user["headers"],
        json={"name": "Quick Bid"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Quick Bid"
    assert data["client_name"] is None


def test_list_projects(client, registered_user):
    """Test listing projects."""
    # Create some projects
    for i in range(3):
        client.post(
            "/api/v1/projects/",
            headers=registered_user["headers"],
            json={"name": f"Project {i}"},
        )

    response = client.get(
        "/api/v1/projects/",
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_project(client, registered_user):
    """Test getting a specific project."""
    # Create project
    create_response = client.post(
        "/api/v1/projects/",
        headers=registered_user["headers"],
        json={"name": "Test Project", "client_name": "Test Client"},
    )
    project_id = create_response.json()["id"]

    # Get project
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Test Project"


def test_get_project_not_found(client, registered_user):
    """Test getting nonexistent project returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/projects/{fake_id}",
        headers=registered_user["headers"],
    )

    assert response.status_code == 404


def test_update_project(client, registered_user):
    """Test updating a project."""
    # Create project
    create_response = client.post(
        "/api/v1/projects/",
        headers=registered_user["headers"],
        json={"name": "Original Name"},
    )
    project_id = create_response.json()["id"]

    # Update project
    response = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=registered_user["headers"],
        json={"name": "Updated Name", "status": "won"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "won"


def test_delete_project(client, registered_user):
    """Test deleting a project."""
    # Create project
    create_response = client.post(
        "/api/v1/projects/",
        headers=registered_user["headers"],
        json={"name": "To Delete"},
    )
    project_id = create_response.json()["id"]

    # Delete project
    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=registered_user["headers"],
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(
        f"/api/v1/projects/{project_id}",
        headers=registered_user["headers"],
    )
    assert get_response.status_code == 404


def test_project_unauthorized(client):
    """Test project endpoints require authentication."""
    response = client.get("/api/v1/projects/")
    assert response.status_code == 401

    response = client.post("/api/v1/projects/", json={"name": "Test"})
    assert response.status_code == 401
