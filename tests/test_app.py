from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activity_data(client):
    # Arrange
    expected_activities = deepcopy(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    email = "student+art@mergington.edu"

    # Act
    response = client.post("/activities/Art%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert activities["Art Club"]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    original_participants = deepcopy(activities["Chess Club"]["participants"])

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities["Chess Club"]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@example.com"
    original_activities = deepcopy(activities)

    # Act
    response = client.post("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == original_activities


def test_signup_requires_email(client):
    # Arrange
    original_activities = deepcopy(activities)

    # Act
    response = client.post("/activities/Chess%20Club/signup")

    # Assert
    assert response.status_code == 422
    assert activities == original_activities


def test_unregister_removes_only_selected_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    original_programming_class = deepcopy(activities["Programming Class"])
    original_max_participants = activities["Chess Club"]["max_participants"]

    # Act
    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert activities["Chess Club"]["participants"] == ["daniel@mergington.edu"]
    assert activities["Programming Class"] == original_programming_class
    assert activities["Chess Club"]["max_participants"] == original_max_participants


def test_unregister_unknown_activity(client):
    # Arrange
    email = "michael@mergington.edu"
    original_activities = deepcopy(activities)

    # Act
    response = client.delete("/activities/Unknown/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == original_activities


def test_unregister_unknown_participant(client):
    # Arrange
    email = "unknown@example.com"
    original_activities = deepcopy(activities)

    # Act
    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activities == original_activities


def test_unregister_requires_email(client):
    # Arrange
    original_activities = deepcopy(activities)

    # Act
    response = client.delete("/activities/Chess%20Club/unregister")

    # Assert
    assert response.status_code == 422
    assert activities == original_activities


def test_unregister_last_participant_and_sign_up_again(client):
    # Arrange
    email = "student+art@mergington.edu"
    params = {"email": email}

    # Act
    signup_response = client.post("/activities/Art%20Club/signup", params=params)

    # Assert
    assert signup_response.status_code == 200
    assert activities["Art Club"]["participants"] == [email]

    # Act
    unregister_response = client.delete("/activities/Art%20Club/unregister", params=params)

    # Assert
    assert unregister_response.status_code == 200
    assert activities["Art Club"]["participants"] == []

    # Act
    repeated_unregister_response = client.delete(
        "/activities/Art%20Club/unregister", params=params
    )

    # Assert
    assert repeated_unregister_response.status_code == 404

    # Act
    repeated_signup_response = client.post("/activities/Art%20Club/signup", params=params)

    # Assert
    assert activities["Art Club"]["participants"] == [email]
    assert repeated_signup_response.status_code == 200
