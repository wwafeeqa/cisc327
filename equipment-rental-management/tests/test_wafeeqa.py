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


# ------------------------------------------------------------
# F13: Check out equipment (POST /rentals, /ui/rentals) — R7, R13, R15
# ------------------------------------------------------------


def test_checkout_creates_open_rental(client):
    """A checkout records who rented what, and starts with no return date."""
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)

    rental = checkout(client, equipment_id, renter_id)
    assert rental["equipment_id"] == equipment_id
    assert rental["renter_id"] == renter_id
    assert rental["rental_date"] == date.today().isoformat()
    assert rental["return_date"] is None


def test_checkout_due_date_is_seven_days_after_rental_date(client):
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)

    rental = checkout(client, equipment_id, renter_id)
    rental_date = date.fromisoformat(rental["rental_date"])
    due_date = date.fromisoformat(rental["due_date"])
    assert due_date - rental_date == timedelta(days=7)


def test_checkout_decrements_available_units(client):
    equipment_id = create_equipment(client, total_units=3)
    renter_id = create_renter(client)

    checkout(client, equipment_id, renter_id)
    assert available_units(client, equipment_id) == 2


def test_checkout_records_deposit_amount(client):
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)

    rental = checkout(client, equipment_id, renter_id, deposit_amount=50.0)
    assert rental["deposit_amount"] == 50.0
    assert rental["deposit_released"] is False


def test_checkout_deposit_defaults_to_zero(client):
    equipment_id = create_equipment(client)
    renter_id = create_renter(client)

    rental = checkout(client, equipment_id, renter_id)
    assert rental["deposit_amount"] == 0.0


def test_checkout_unknown_equipment_returns_404(client):
    renter_id = create_renter(client)

    response = client.post(
        "/rentals", json={"equipment_id": 999, "renter_id": renter_id}
    )
    assert response.status_code == 404
    assert client.get("/rentals").get_json() == []


def test_checkout_out_of_service_equipment_is_rejected(client):
    """Out-of-service equipment cannot be rented, and its units stay untouched."""
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    client.patch(f"/equipment/{equipment_id}/status", json={"is_available": False})

    response = client.post(
        "/rentals", json={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert response.status_code == 400
    assert available_units(client, equipment_id) == 2
    assert client.get("/rentals").get_json() == []


def test_checkout_with_no_units_left_is_rejected(client):
    """A checkout cannot push available_units below zero."""
    equipment_id = create_equipment(client, total_units=1)
    renter_id = create_renter(client)
    checkout(client, equipment_id, renter_id)

    response = client.post(
        "/rentals", json={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert response.status_code == 400
    assert available_units(client, equipment_id) == 0


def test_checkout_unknown_renter_is_rejected(client):
    """A rental must belong to a renter that exists."""
    equipment_id = create_equipment(client, total_units=2)

    response = client.post(
        "/rentals", json={"equipment_id": equipment_id, "renter_id": 999}
    )
    assert response.status_code == 404
    assert available_units(client, equipment_id) == 2


def test_checkout_equipment_with_zero_total_units_is_rejected(client):
    """Boundary: an item created with no units can never be rented."""
    equipment_id = create_equipment(client, total_units=0)
    renter_id = create_renter(client)

    response = client.post(
        "/rentals", json={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert response.status_code == 400
    assert available_units(client, equipment_id) == 0


def test_checkout_missing_renter_id_is_rejected(client):
    """A checkout with no renter is a client error and must not consume a unit."""
    equipment_id = create_equipment(client, total_units=2)

    response = client.post("/rentals", json={"equipment_id": equipment_id})
    assert response.status_code == 400
    assert available_units(client, equipment_id) == 2


def test_ui_checkout_creates_rental_and_redirects(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)

    response = client.post(
        "/ui/rentals", data={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert response.status_code == 302

    rentals = client.get("/rentals").get_json()
    assert len(rentals) == 1
    assert rentals[0]["equipment_id"] == equipment_id
    assert rentals[0]["renter_id"] == renter_id
    assert available_units(client, equipment_id) == 1


def test_ui_checkout_unknown_equipment_creates_nothing(client):
    renter_id = create_renter(client)

    response = client.post(
        "/ui/rentals", data={"equipment_id": 999, "renter_id": renter_id}
    )
    assert response.status_code == 302
    assert client.get("/rentals").get_json() == []


def test_ui_checkout_out_of_service_equipment_creates_nothing(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    client.patch(f"/equipment/{equipment_id}/status", json={"is_available": False})

    client.post(
        "/ui/rentals", data={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert client.get("/rentals").get_json() == []
    assert available_units(client, equipment_id) == 2


def test_ui_checkout_with_no_units_left_creates_nothing(client):
    equipment_id = create_equipment(client, total_units=1)
    renter_id = create_renter(client)
    checkout(client, equipment_id, renter_id)

    client.post(
        "/ui/rentals", data={"equipment_id": equipment_id, "renter_id": renter_id}
    )
    assert len(client.get("/rentals").get_json()) == 1
    assert available_units(client, equipment_id) == 0


# ------------------------------------------------------------
# F14: Return equipment (PUT /rentals/<id>/return, UI return)
# ------------------------------------------------------------


def test_return_sets_return_date_and_restores_unit(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)

    response = client.put(f"/rentals/{rental['id']}/return")
    assert response.status_code == 200
    assert response.get_json()["return_date"] == date.today().isoformat()
    assert available_units(client, equipment_id) == 2


def test_return_twice_is_rejected_and_units_not_double_counted(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)
    client.put(f"/rentals/{rental['id']}/return")

    response = client.put(f"/rentals/{rental['id']}/return")
    assert response.status_code == 400
    assert available_units(client, equipment_id) == 2


def test_return_unknown_rental_returns_404(client):
    assert client.put("/rentals/999/return").status_code == 404


def test_ui_return_sets_return_date_and_restores_unit(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)

    response = client.post(f"/ui/rentals/{rental['id']}/return")
    assert response.status_code == 302
    assert find_rental(client, rental["id"])["return_date"] == date.today().isoformat()
    assert available_units(client, equipment_id) == 2


def test_ui_return_twice_does_not_double_count_units(client):
    equipment_id = create_equipment(client, total_units=2)
    renter_id = create_renter(client)
    rental = checkout(client, equipment_id, renter_id)

    client.post(f"/ui/rentals/{rental['id']}/return")
    client.post(f"/ui/rentals/{rental['id']}/return")
    assert available_units(client, equipment_id) == 2
