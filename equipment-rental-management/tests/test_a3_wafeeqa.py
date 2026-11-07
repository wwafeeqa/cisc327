"""Assignment 3, Member B (Wafeeqa): return notification failure and non-trigger paths.

The return route (PUT /rentals/<id>/return) calls send_notification() after a
successful return. These tests replace it where app/routes/rentals.py uses it,
so no notification is recorded by the real simulator.
"""

from datetime import date
from unittest.mock import patch

NOTIFY = "app.routes.rentals.send_notification"


def create_equipment(client, name="Extension Ladder", total_units=2):
    response = client.post(
        "/equipment",
        json={"name": name, "category": "Climbing", "total_units": total_units},
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def create_renter(client, name="Sam Lee"):
    response = client.post(
        "/renters",
        json={"name": name, "email": f"{name.split()[0].lower()}@example.com"},
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def checkout(client, equipment_id, renter_id):
    response = client.post(
        "/rentals", json={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert response.status_code == 201
    return response.get_json()


def available_units(client, equipment_id):
    return client.get(f"/equipment/{equipment_id}/availability").get_json()[
        "available_units"
    ]


def find_rental(client, rental_id):
    rentals = client.get("/rentals").get_json()
    return next(r for r in rentals if r["id"] == rental_id)


# Stub: failure path


def test_return_succeeds_when_notification_fails(client, monkeypatch):
    """Stub returning False: the return still succeeds and reports no notification."""
    monkeypatch.setattr(NOTIFY, lambda recipient, subject, message: False)
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)

    response = client.put(f"/rentals/{rental['id']}/return")

    assert response.status_code == 200
    data = response.get_json()
    assert data["notification_sent"] is False
    assert data["return_date"] == date.today().isoformat()
    assert find_rental(client, rental["id"])["return_date"] is not None
    assert available_units(client, equipment_id) == 2


# Mocks: non-trigger paths


def test_no_notification_when_rental_already_returned(client):
    """A repeat return is rejected and sends no second notification."""
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)
    client.put(f"/rentals/{rental['id']}/return")

    with patch(NOTIFY) as mock_send:
        response = client.put(f"/rentals/{rental['id']}/return")

        assert response.status_code == 400
        assert response.get_json()["error"] == "Rental already returned"
        assert available_units(client, equipment_id) == 2
        mock_send.assert_not_called()


def test_no_notification_when_rental_not_found(client):
    """Returning a nonexistent rental is rejected and sends no notification."""
    with patch(NOTIFY) as mock_send:
        response = client.put("/rentals/999/return")

        assert response.status_code == 404
        assert response.get_json()["error"] == "Rental not found"
        assert client.get("/rentals").get_json() == []
        mock_send.assert_not_called()


def test_no_notification_when_renter_deleted(client):
    """If the renter no longer exists, the return succeeds without a notification."""
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)
    assert client.delete(f"/renters/{renter_id}").status_code in (200, 204)

    with patch(NOTIFY) as mock_send:
        response = client.put(f"/rentals/{rental['id']}/return")

        assert response.status_code == 200
        assert response.get_json()["notification_sent"] is False
        assert find_rental(client, rental["id"])["return_date"] is not None
        assert available_units(client, equipment_id) == 2
        mock_send.assert_not_called()
