import uuid

SAMPLE_EVENT = {
    "name": "Jordan's 30th Birthday",
    "event_type": "birthday",
    "event_date": "2026-11-01",
    "location": "Austin, TX",
    "host_name": "Jordan Lee",
    "organizer_email": "jordan@example.com",
    "collaborator_emails": ["friend1@example.com", "friend2@example.com"],
    "guest_count": 40,
    "total_budget": 3000,
    "notes": "Rooftop party",
    "budget_items": [
        {
            "category": "Venue",
            "description": "Rooftop bar rental",
            "budgeted_amount": 1200,
            "vendor_name": "Skyline Bar",
        },
        {
            "category": "Catering",
            "budgeted_amount": 900,
            "actual_amount": 950,
            "paid": True,
        },
    ],
}


def test_create_event(client):
    resp = client.post("/events", json=SAMPLE_EVENT)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == SAMPLE_EVENT["name"]
    assert body["organizer_email"] == "jordan@example.com"
    assert body["collaborator_emails"] == SAMPLE_EVENT["collaborator_emails"]
    assert len(body["budget_items"]) == 2
    assert uuid.UUID(body["id"])  # valid UUID


def test_create_event_rejects_invalid_organizer_email(client):
    bad = dict(SAMPLE_EVENT, organizer_email="not-an-email")
    resp = client.post("/events", json=bad)
    assert resp.status_code == 422


def test_create_event_requires_organizer_email(client):
    bad = {k: v for k, v in SAMPLE_EVENT.items() if k != "organizer_email"}
    resp = client.post("/events", json=bad)
    assert resp.status_code == 422


def test_get_event_by_id(client):
    created = client.post("/events", json=SAMPLE_EVENT).json()
    resp = client.get(f"/events/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_event_not_found(client):
    resp = client.get(f"/events/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_list_events_filters_by_name(client):
    client.post("/events", json=SAMPLE_EVENT)
    other = dict(SAMPLE_EVENT, name="Company Holiday Party")
    client.post("/events", json=other)

    resp = client.get("/events", params={"name": "birthday"})
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()]
    assert names == ["Jordan's 30th Birthday"]


def test_put_event_fully_replaces_fields_and_budget_items(client):
    created = client.post("/events", json=SAMPLE_EVENT).json()
    event_id = created["id"]

    updated_payload = dict(
        SAMPLE_EVENT,
        name="Jordan's 30th Birthday (Rescheduled)",
        location="Dallas, TX",
        organizer_email="jordan.new@example.com",
        budget_items=[
            {"category": "Venue", "budgeted_amount": 1500, "vendor_name": "New Venue"}
        ],
    )
    resp = client.put(f"/events/{event_id}", json=updated_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Jordan's 30th Birthday (Rescheduled)"
    assert body["location"] == "Dallas, TX"
    assert body["organizer_email"] == "jordan.new@example.com"
    # Old "Catering" item should be gone -- PUT is a full replace.
    assert len(body["budget_items"]) == 1
    assert body["budget_items"][0]["category"] == "Venue"
    assert body["budget_items"][0]["vendor_name"] == "New Venue"


def test_put_event_not_found(client):
    resp = client.put(f"/events/{uuid.uuid4()}", json=SAMPLE_EVENT)
    assert resp.status_code == 404


def test_events_require_api_key(client):
    resp = client.post("/events", json=SAMPLE_EVENT, headers={"X-API-Key": ""})
    assert resp.status_code == 401


def test_events_reject_wrong_api_key(client):
    resp = client.post(
        "/events", json=SAMPLE_EVENT, headers={"X-API-Key": "wrong-key"}
    )
    assert resp.status_code == 401


def test_health_check_does_not_require_api_key(client):
    resp = client.get("/health", headers={"X-API-Key": ""})
    assert resp.status_code == 200
