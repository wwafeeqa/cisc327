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