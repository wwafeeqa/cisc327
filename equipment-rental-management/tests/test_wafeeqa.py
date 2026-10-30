from datetime import date, timedelta


def create_equipment(client, name="Extension Ladder", total_units=3):
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


def checkout(client, equipment_id, renter_id, **extra):
    response = client.post(
        "/rentals",
        json={"equipment_id": equipment_id, "renter_id": renter_id, **extra},
    )
    assert response.status_code == 201
    return response.get_json()


def available_units(client, equipment_id):
    return client.get(f"/equipment/{equipment_id}/availability").get_json()[
        "available_units"
    ]


def find_rental(client, rental_id):
    """Fetch one rental through the lookup endpoint (there is no GET /rentals/<id>)."""
    rentals = client.get("/rentals").get_json()
    return next(r for r in rentals if r["id"] == rental_id)


# ------------------------------------------------------------
# F6: Set equipment status (PATCH /equipment/<id>/status) — R11, R12
# ------------------------------------------------------------


def test_set_status_out_of_service_is_persisted(client):
    """Marking equipment out of service is visible on a later GET."""
    equipment_id = create_equipment(client)

    response = client.patch(
        f"/equipment/{equipment_id}/status", json={"is_available": False}
    )
    assert response.status_code == 200
    assert response.get_json()["is_available"] is False

    assert client.get(f"/equipment/{equipment_id}").get_json()["is_available"] is False


def test_set_status_can_return_equipment_to_service(client):
    """Out-of-service equipment can be marked available again."""
    equipment_id = create_equipment(client)
    client.patch(f"/equipment/{equipment_id}/status", json={"is_available": False})

    response = client.patch(
        f"/equipment/{equipment_id}/status", json={"is_available": True}
    )
    assert response.status_code == 200
    assert client.get(f"/equipment/{equipment_id}").get_json()["is_available"] is True


def test_set_status_does_not_change_unit_counts(client):
    """Changing status leaves total_units and available_units alone."""
    equipment_id = create_equipment(client, total_units=4)

    data = client.patch(
        f"/equipment/{equipment_id}/status", json={"is_available": False}
    ).get_json()
    assert data["total_units"] == 4
    assert data["available_units"] == 4


def test_set_status_unknown_equipment_returns_404(client):
    response = client.patch("/equipment/999/status", json={"is_available": False})
    assert response.status_code == 404


def test_set_status_missing_field_is_rejected(client):
    """A request without is_available is a client error and changes nothing."""
    equipment_id = create_equipment(client)

    response = client.patch(f"/equipment/{equipment_id}/status", json={})
    assert response.status_code == 400
    assert client.get(f"/equipment/{equipment_id}").get_json()["is_available"] is True


# ------------------------------------------------------------
# F7: Get equipment availability (GET /equipment/<id>/availability) — R8, R16
# ------------------------------------------------------------


def test_availability_returns_full_summary(client):
    """A new item reports all of its units as available."""
    equipment_id = create_equipment(client, total_units=2)

    response = client.get(f"/equipment/{equipment_id}/availability")
    assert response.status_code == 200
    assert response.get_json() == {
        "equipment_id": equipment_id,
        "is_available": True,
        "available_units": 2,
        "total_units": 2,
    }


def test_availability_reflects_checkout_and_return(client):
    """available_units drops on checkout and recovers on return."""
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)

    rental = checkout(client, equipment_id, renter_id)
    assert available_units(client, equipment_id) == 1

    client.put(f"/rentals/{rental['id']}/return")
    assert available_units(client, equipment_id) == 2


def test_availability_reflects_out_of_service_status(client):
    equipment_id = create_equipment(client)
    client.patch(f"/equipment/{equipment_id}/status", json={"is_available": False})

    data = client.get(f"/equipment/{equipment_id}/availability").get_json()
    assert data["is_available"] is False


def test_availability_unknown_equipment_returns_404(client):
    assert client.get("/equipment/999/availability").status_code == 404
