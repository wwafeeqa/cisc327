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