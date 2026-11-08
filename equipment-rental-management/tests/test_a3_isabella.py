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
def test_delete_equipment(client):
    """
    Deletes it a piece of equipment that does not exist and returns a 404 error
    """
    response = client.delete("/equipment/10")
    assert response.status_code == 404
    assert response.get_json()== {"error": "Equipment not found"}

