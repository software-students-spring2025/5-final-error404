import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Scan the Barcode on the Back of a Book!" in response.data
    
def test_search(client):
    response = client.get("/search?q=harry+potter&partial=true")
    assert response.status_code == 200
    assert b"Add to My List" in response.data or b"No book found. Try again!" in response.data

def test_broken_search(client):
    response = client.get("/search?q=")
    assert response.status_code == 400
    
def test_library(client):
    response = client.get("/library")
    assert response.status_code == 200