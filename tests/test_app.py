from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        activities.clear()
        activities.update(self.original_activities)

    def test_unregister_removes_only_selected_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Unregistered michael@mergington.edu from Chess Club"},
        )
        remaining = self.client.get("/activities").json()
        self.assertEqual(
            remaining["Chess Club"]["participants"], ["daniel@mergington.edu"]
        )
        self.assertEqual(
            remaining["Programming Class"], self.original_activities["Programming Class"]
        )
        self.assertEqual(
            remaining["Chess Club"]["max_participants"],
            self.original_activities["Chess Club"]["max_participants"],
        )

    def test_unregister_unknown_activity(self):
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "michael@mergington.edu"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_unknown_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": "unknown@example.com"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(), {"detail": "Student is not signed up for this activity"}
        )
        self.assertEqual(activities, self.original_activities)

    def test_unregister_requires_email(self):
        response = self.client.delete("/activities/Chess%20Club/unregister")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities, self.original_activities)

    def test_unregister_last_participant_and_sign_up_again(self):
        params = {"email": "student+art@mergington.edu"}
        self.assertEqual(
            self.client.post("/activities/Art%20Club/signup", params=params).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete("/activities/Art%20Club/unregister", params=params).status_code,
            200,
        )
        self.assertEqual(activities["Art Club"]["participants"], [])
        self.assertEqual(
            self.client.delete("/activities/Art%20Club/unregister", params=params).status_code,
            404,
        )
        self.assertEqual(
            self.client.post("/activities/Art%20Club/signup", params=params).status_code,
            200,
        )
