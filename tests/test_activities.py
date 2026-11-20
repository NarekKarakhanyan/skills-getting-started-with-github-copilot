from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["max_participants"] == 12


def test_signup_adds_student_to_activity(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert "new.student@mergington.edu" in client.get(
        "/activities"
    ).json()["Chess Club"]["participants"]


def test_unregister_removes_student_from_activity(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in client.get(
        "/activities"
    ).json()["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("method", "activity_name", "email", "status_code", "detail"),
    [
        ("post", "Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        ("delete", "Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        (
            "post",
            "Chess Club",
            "michael@mergington.edu",
            400,
            "Student is already signed up",
        ),
        (
            "delete",
            "Chess Club",
            "student@mergington.edu",
            404,
            "Student is not signed up for this activity",
        ),
    ],
)
def test_signup_and_unregister_errors(
    client, method, activity_name, email, status_code, detail
):
    response = getattr(client, method)(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == status_code
    assert response.json()["detail"] == detail
