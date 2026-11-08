from unittest.mock import patch

#Isabella Youhanna
#CISC327 Assignment 3

#stub test - success path

def test_return_notification_success(client, monkeypatch):
    #setting up necessary info for test
    #making a renter
    renterResponse=client.post("/renters", json={
        "name": "John Doe",
        "email": "johndoe@gmail.com"
    })
    renter_id=renterResponse.get_json()["id"]

    #making equipment
    equipResponse=client.post("/equipment", json={
        "name": "Shovel",
        "category": "Tools",
        "total_units": 3
    })
    equipment_id=equipResponse.get_json()["id"]

    #making a rental
    rentalResponse=client.post("/rentals", json={
        "renter_id": renter_id,
        "equipment_id": equipment_id
    })
    rentalID=rentalResponse.get_json()["id"]

    #replacement of function
    monkeypatch.setattr(
        "app.routes.rentals.send_notification",
        lambda recipient, subject, message: True
    )

    response=client.put(f"/rentals/{rentalID}/return")
    assert response.status_code == 200
    assert response.get_json()["notification_sent"] is True
    assert response.get_json()["return_date"] is not None


#mock test - success path
def test_return_notification_details(client):
    #setting up necessary info for test
    #making a renter
    renterResponse=client.post("/renters", json={
        "name": "John Doe",
        "email": "johndoe@gmail.com"
    })
    renter_id=renterResponse.get_json()["id"]

    #making equipment
    equipResponse=client.post("/equipment", json={
        "name": "Shovel",
        "category": "Tools",
        "total_units": 3
    })
    equipment_id=equipResponse.get_json()["id"]

    #making a rental
    rentalResponse=client.post("/rentals", json={
        "renter_id": renter_id,
        "equipment_id": equipment_id
    })  
    rentalID=rentalResponse.get_json()["id"]

    #replacement for function
    with patch(
        "app.routes.rentals.send_notification",
        return_value=True
    ) as mock_send:

        response=client.put(f"/rentals/{rentalID}/return")
        assert response.status_code == 200
        mock_send.assert_called_once_with(
            "johndoe@gmail.com",
            "Equipment Return Confirmation",
            "Your equipment has been successfully returned!"
        )


#Coverage Tests 
#Delete Equipment
def test_delete_equipment_not_found(client):
    """
    Deletes a piece of equipment that does not exist and returns a 404 error
    """
    response = client.delete("/equipment/10")
    assert response.status_code == 404
    assert response.get_json()== {"error": "Equipment not found"}

#Get Renter
def test_get_renter_not_found(client):
    """
    Attempts to retrieve a renter that does not exist 
    """
    response = client.get("/renters/5")
    assert response.status_code == 404
    assert response.get_json()== {"error": "Renter not found"}

#Delete Renter
def test_delete_renter_not_found(client):
    response=client.delete("/renters/20")
    assert response.status_code == 404
    assert response.get_json()=={"error": "Renter not found"} 

#Equipment Page
#Get Equipment Page
def test_equipment_page_get(client):
    response=client.get("/ui/equipment")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")

#Post Equipment Page
def test_equipment_page_post(client):
    response=client.post(
        "ui/equipment",
        data={"name":"Bicycle", "category":"Sports","total_units": "4"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("ui/equipment") #redirects back to equipment page

    eqResponse=client.get("/equipment")
    eq=eqResponse.get_json() 

    #checking info was saved correctly
    assert len(eq)==1 #1 item created 
    assert eq[0]["name"]=="Bicycle"
    assert eq[0]["category"]=="Sports"
    assert eq[0]["total_units"]==4 
    assert eq[0]["available_units"]==eq[0]["total_units"]

#Renters Page
#Get Renters Page
def test_renters_page_get(client):
    response=client.get("ui/renters")
    assert response.status_code==200
    assert response.content_type.startswith("text/html")

#Post Renters Page
def test_renters_page_post(client):
    response=client.post(
        "ui/renters",
        data={"name":"Doug Ford","email":"dougford@gmail.com"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("ui/renters") #redirects back to renter page

    renterResponse=client.get("/renters")
    renter=renterResponse.get_json()

    #checking data
    assert len(renter)==1
    assert renter[0]["name"]=="Doug Ford"
    assert renter[0]["email"]=="dougford@gmail.com"