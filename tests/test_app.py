import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_store


@pytest.fixture()
def client():
    # snapshot activities and provide a test client; restore after test
    original = copy.deepcopy(activities_store)
    client = TestClient(app)
    yield client
    activities_store.clear()
    activities_store.update(original)


def test_root_redirect(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (307, 302)
    assert resp.headers.get("location") == "/static/index.html"


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # expect a mapping with at least the known activities
    assert isinstance(data, dict)
    assert "Chess Club" in data
    first = data["Chess Club"]
    assert "description" in first and "participants" in first


def test_signup_and_duplicate_errors(client):
    activity = "Tennis Team"
    email = "newstudent@mergington.edu"

    # signup success
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(url)
    assert resp.status_code == 200
    assert email in activities_store[activity]["participants"]

    # duplicate signup returns 400
    resp2 = client.post(url)
    assert resp2.status_code == 400

    # non-existent activity
    resp3 = client.post("/activities/DoesNotExist/signup?email=test@x.com")
    assert resp3.status_code == 404


def test_unregister_and_error_cases(client):
    activity = "Chess Club"
    # pick an existing participant
    existing = activities_store[activity]["participants"][0]

    url = f"/activities/{urllib.parse.quote(activity)}/unregister?email={urllib.parse.quote(existing)}"
    resp = client.delete(url)
    assert resp.status_code == 200
    assert existing not in activities_store[activity]["participants"]

    # unregistering someone not signed up => 400
    resp2 = client.delete(url)
    assert resp2.status_code == 400

    # unregister from non-existent activity => 404
    resp3 = client.delete("/activities/Nope/unregister?email=a@b.com")
    assert resp3.status_code == 404
