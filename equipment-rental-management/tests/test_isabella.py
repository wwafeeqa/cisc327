#Isabella Youhanna
#CISC327 


#F1
def test_list_equipment(client):
    """
    Lists all equipment
    """
    response = client.get("/equipment")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

#F2
def test_add_equipment(client):
    """
    Adds new item and verifies that all details are corerct 
    """
    response = client.post("/equipment", json={"name": "Shovel","category": "Tools","total_units": 5})
    assert response.status_code == 201
    equipment = response.get_json()

    assert equipment["name"] == "Shovel"
    assert equipment["category"] == "Tools"
    assert equipment["total_units"] == 5
    assert equipment["available_units"] == 5

#F3
def test_get_one_equipment(client):
    """
    Creates a piece of equipment, adds it, retrieves it, verifies correct info
    """
    client.post("/equipment", json={"name": "Lawn Mower","category": "Machine","total_units": 3})
    response = client.get("/equipment/1")
    assert response.status_code == 200
    equipment = response.get_json()

    assert equipment["id"] == 1
    assert equipment["name"] == "Lawn Mower"
    assert equipment["category"] == "Machine"
    assert equipment["total_units"] == 3

#F5
def test_delete_equipment(client):
    """
    Adds equipment, deletes it, checks its gone
    """
    add_response = client.post("/equipment", json={"name": "Clock","category": "Electronics","total_units": 5})
    equipment_id = add_response.get_json()["id"]
    #deletion
    response = client.delete(f"/equipment/{equipment_id}")
    assert response.status_code == 204
    get_response = client.get(f"/equipment/{equipment_id}")
    assert get_response.status_code == 404

#F8 and F9
def test_list_renters(client):
    """
    Creates 3 renters then lists them out and verifies info
    """
    client.post("/renters", json={"name": "Robert Pattinson","email": "robpattinson@gmail.com"})
    client.post("/renters", json={"name": "Auston Matthews","email": "austonmatthews34@gmail.com"})
    client.post("/renters", json={"name": "Noah Kahan","email": "noahkahan@gmail.com"})

    response = client.get("/renters")
    assert response.status_code == 200
    renters = response.get_json()

    assert len(renters) == 3
    assert renters[0]["name"] == "Robert Pattinson"
    assert renters[1]["name"] == "Auston Matthews"
    assert renters[2]["name"] == "Noah Kahan"

#F10
def test_get_one_renter(client):
    """
    Adds renter, retrieves them, checks the request, verifies info
    """
    add_response=client.post("/renters", json={"name": "Michael Jordan","email": "mjordan@gmail.com"})
    renter_id = add_response.get_json()["id"]
    response = client.get(f"/renters/{renter_id}")
    assert response.status_code == 200
    renter = response.get_json()

    assert renter["id"] == renter_id
    assert renter["name"] == "Michael Jordan"
    assert renter["email"] == "mjordan@gmail.com"

#F11
def test_update_renter_email(client):
    """
    Adds renter, updates the email address, retrieve renter and verifies info
    """
    add_response=client.post("/renters", json={"name": "Deborah Ryan","email": "debbyryan@gmail.com"})
    renter_id = add_response.get_json()["id"]

    #updating the email address
    response = client.put(f"/renters/{renter_id}", json={"name": "Deborah Ryan","email": "deborahryan@gmail.com"})
    assert response.status_code == 200
    get_response = client.get(f"/renters/{renter_id}")
    assert get_response.status_code == 200
    renter = get_response.get_json()

    assert renter["email"] == "deborahryan@gmail.com"
    assert renter["name"] == "Deborah Ryan"


# Enhancement: search rentals by renter name and item name (R9a, R9b)
# Written by Wafeeqa Chowdhury in Isabella's place, with permission.
def create_named_rentals(client):
    """
    Creates two rentals whose renter and item names differ, returns their ids
    """
    ladder = client.post("/equipment", json={"name": "Extension Ladder","category": "Climbing","total_units": 2}).get_json()["id"]
    washer = client.post("/equipment", json={"name": "Pressure Washer","category": "Cleaning","total_units": 2}).get_json()["id"]
    robert = client.post("/renters", json={"name": "Robert Pattinson","email": "robpattinson@gmail.com"}).get_json()["id"]
    noah = client.post("/renters", json={"name": "Noah Kahan","email": "noahkahan@gmail.com"}).get_json()["id"]

    robert_rental = client.post("/rentals", json={"equipment_id": ladder,"renter_id": robert}).get_json()
    noah_rental = client.post("/rentals", json={"equipment_id": washer,"renter_id": noah}).get_json()
    return robert_rental, noah_rental


def test_search_rentals_by_renter_name(client):
    """
    R9a: searching a renter's full name returns only that renter's rental with its details
    """
    robert_rental, _ = create_named_rentals(client)

    response = client.get("/rentals", query_string={"renter_name": "Robert Pattinson"})
    assert response.status_code == 200
    assert response.get_json() == [robert_rental]


def test_search_rentals_by_item_name(client):
    """
    R9b: searching an item's full name returns only rentals of that item
    """
    _, noah_rental = create_named_rentals(client)

    response = client.get("/rentals", query_string={"item_name": "Pressure Washer"})
    assert response.status_code == 200
    assert response.get_json() == [noah_rental]


def test_search_rentals_by_name_is_partial_and_ignores_case(client):
    """
    R9a, R9b: a clerk can find a rental from part of a name typed in any case
    """
    robert_rental, noah_rental = create_named_rentals(client)

    assert client.get("/rentals", query_string={"renter_name": "pattin"}).get_json() == [robert_rental]
    assert client.get("/rentals", query_string={"item_name": "WASHER"}).get_json() == [noah_rental]


def test_search_rentals_by_renter_and_item_name_together(client):
    """
    R9a, R9b: combined searches only return rentals matching both names
    """
    robert_rental, _ = create_named_rentals(client)

    both = client.get("/rentals", query_string={"renter_name": "Robert", "item_name": "Ladder"})
    assert both.get_json() == [robert_rental]

    mismatched = client.get("/rentals", query_string={"renter_name": "Robert", "item_name": "Washer"})
    assert mismatched.status_code == 200
    assert mismatched.get_json() == []


def test_search_rentals_with_no_matching_name_returns_empty_list(client):
    """
    Names that match nothing return an empty list rather than an error
    """
    create_named_rentals(client)

    response = client.get("/rentals", query_string={"renter_name": "Nobody"})
    assert response.status_code == 200
    assert response.get_json() == []


def test_search_rentals_by_name_includes_returned_rentals(client):
    """
    A search shows the current return date, so history stays searchable after a return
    """
    robert_rental, _ = create_named_rentals(client)
    returned = client.put(f"/rentals/{robert_rental['id']}/return").get_json()

    response = client.get("/rentals", query_string={"renter_name": "Robert"})
    assert response.get_json() == [returned]
    assert response.get_json()[0]["return_date"] is not None


def test_search_rentals_after_renter_is_deleted_does_not_crash(client):
    """
    A rental whose renter was deleted no longer matches a name search but stays in the full list
    """
    robert_rental, noah_rental = create_named_rentals(client)
    client.delete(f"/renters/{robert_rental['renter_id']}")

    response = client.get("/rentals", query_string={"renter_name": "Robert"})
    assert response.status_code == 200
    assert response.get_json() == []
    assert client.get("/rentals").get_json() == [robert_rental, noah_rental]