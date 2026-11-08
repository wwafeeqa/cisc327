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


# Task 3: coverage-directed tests (Member B areas in Table A)

# update_equipment (PUT /equipment/<id>)


def test_update_equipment_changes_fields_and_persists(client):
    """A full update is returned and saved."""
    equipment_id = create_equipment(client, name="Ladder", total_units=2)

    response = client.put(
        f"/equipment/{equipment_id}",
        json={"name": "Tall Ladder", "category": "Access", "total_units": 4,
              "available_units": 4, "is_available": False},
    )

    assert response.status_code == 200
    expected = {"id": equipment_id, "name": "Tall Ladder", "category": "Access",
                "total_units": 4, "available_units": 4, "is_available": False}
    assert response.get_json() == expected
    assert client.get(f"/equipment/{equipment_id}").get_json() == expected


def test_update_equipment_partial_keeps_other_fields(client):
    """Fields left out of the request keep their current values."""
    equipment_id = create_equipment(client, name="Ladder", total_units=3)

    response = client.put(f"/equipment/{equipment_id}", json={"name": "Step Ladder"})

    assert response.status_code == 200
    item = client.get(f"/equipment/{equipment_id}").get_json()
    assert item["name"] == "Step Ladder"
    assert item["category"] == "Climbing"
    assert item["total_units"] == 3
    assert item["available_units"] == 3
    assert item["is_available"] is True


def test_update_unknown_equipment_returns_404(client):
    """Updating equipment that does not exist is rejected and creates nothing."""
    response = client.put("/equipment/999", json={"name": "Ghost"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "Equipment not found"
    assert client.get("/equipment").get_json() == []


# update_renter (PUT /renters/<id>)


def test_update_renter_partial_keeps_email(client):
    """Changing only the name leaves the email unchanged."""
    renter_id = create_renter(client, name="Sam Lee")

    response = client.put(f"/renters/{renter_id}", json={"name": "Samuel Lee"})

    assert response.status_code == 200
    renter = client.get(f"/renters/{renter_id}").get_json()
    assert renter["name"] == "Samuel Lee"
    assert renter["email"] == "sam@example.com"


def test_update_unknown_renter_returns_404(client):
    """Updating a renter that does not exist is rejected and creates nothing."""
    response = client.put("/renters/999", json={"name": "Nobody"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "Renter not found"
    assert client.get("/renters").get_json() == []


# views.py pages


def test_home_page_links_to_each_section(client):
    """The home page renders with links to the equipment, renter and rental pages."""
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Equipment Rental Management" in html
    for path in ("/ui/equipment", "/ui/renters", "/ui/rentals"):
        assert f'href="{path}"' in html


def test_ui_delete_equipment_removes_item_and_redirects(client):
    """Deleting equipment from the UI removes it and returns to the equipment page."""
    keep_id = create_equipment(client, name="Keep Ladder")
    delete_id = create_equipment(client, name="Old Ladder")

    response = client.post(f"/ui/equipment/{delete_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/equipment")
    assert client.get(f"/equipment/{delete_id}").status_code == 404
    assert [e["id"] for e in client.get("/equipment").get_json()] == [keep_id]


def test_ui_delete_unknown_equipment_changes_nothing(client):
    """Deleting a nonexistent id from the UI still redirects and removes nothing."""
    equipment_id = create_equipment(client)

    response = client.post("/ui/equipment/999/delete")

    assert response.status_code == 302
    assert [e["id"] for e in client.get("/equipment").get_json()] == [equipment_id]


def test_ui_delete_renter_removes_renter_and_redirects(client):
    """Deleting a renter from the UI removes them and returns to the renters page."""
    keep_id = create_renter(client, name="Kim Park")
    delete_id = create_renter(client, name="Sam Lee")

    response = client.post(f"/ui/renters/{delete_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/renters")
    assert client.get(f"/renters/{delete_id}").status_code == 404
    assert [r["id"] for r in client.get("/renters").get_json()] == [keep_id]


def test_ui_delete_unknown_renter_changes_nothing(client):
    """Deleting a nonexistent renter from the UI still redirects and removes nothing."""
    renter_id = create_renter(client)

    response = client.post("/ui/renters/999/delete")

    assert response.status_code == 302
    assert [r["id"] for r in client.get("/renters").get_json()] == [renter_id]


def test_ui_rentals_page_empty(client):
    """With no rentals, the page renders the checkout form and no Return buttons."""
    response = client.get("/ui/rentals")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Check Out Equipment" in html
    assert "Return</button>" not in html


def test_ui_rentals_page_lists_open_and_returned_rentals(client):
    """Open rentals show a Return button; returned rentals show their return date."""
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    open_rental = checkout(client, equipment_id, renter_id)
    returned = checkout(client, equipment_id, renter_id)
    with patch(NOTIFY, return_value=True):
        client.put(f"/rentals/{returned['id']}/return")

    response = client.get("/ui/rentals")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count("Return</button>") == 1
    assert f"/ui/rentals/{open_rental['id']}/return" in html
    assert f"/ui/rentals/{returned['id']}/return" not in html
    assert html.count("<td>-</td>") == 1  # only the open rental has no return date
