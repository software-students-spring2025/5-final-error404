import pytest
from app import app, users_collection, books_collection
from unittest.mock import patch


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:

        users_collection.insert_one(
            {"email": "testuser@example.com", "password": "testpassword"}
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "testuser@example.com"
        yield client

        users_collection.delete_one({"email": "testuser@example.com"})


def test_register(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_login(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_logout(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert b"/login" in response.data


def test_not_logged_in(client):
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/scanner")
        assert response.status_code == 302
        assert b"/login" in response.data


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Scan the Barcode on the Back of a Book!" in response.data


@patch("app.requests.get")
def test_search(mock_get, client):

    mock_get.return_value.json.return_value = {
        "docs": [
            {
                "title": "Harry Potter and the Philosopher's Stone",
                "author_name": ["J.K. Rowling"],
                "cover_i": "123456",
                "isbn": ["9780747532699"],
            }
        ]
    }

    response = client.get("/search?q=harry+potter&partial=true")
    assert response.status_code == 200
    assert b"Save to My Library" in response.data


def test_add_to_library(client):
    book_data = {
        "title": "Harry Potter and the Philosopher's Stone",
        "authors": ["J.K. Rowling"],
        "isbn": "9780747532699",
        "cover": "https://example.com.jpg",
    }

    response = client.post("/save_book", data=book_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Category" in response.data


def test_remove_from_library(client):
    inserted = books_collection.insert_one(
        {
            "owner": "testuser@example.com",
            "title": "Harry Potter and the Philosopher's Stone",
            "authors": ["J.K. Rowling"],
            "isbn": "9780747532699",
            "cover": "https://example.com.jpg",
            "category": "Want to Read",
        }
    )

    book_id = str(inserted.inserted_id)
    response = client.post(f"/library/{book_id}/remove", follow_redirects=True)
    assert response.status_code == 200
    assert books_collection.find_one({"_id": inserted.inserted_id}) is None


def test_broken_search(client):
    response = client.get("/search?q=")
    assert response.status_code == 400


def test_library(client):
    response = client.get("/library")
    assert response.status_code == 200


def test_camera(client):
    response = client.get("/scanner")
    assert response.status_code == 200
    html = response.data.decode()
    assert "https://unpkg.com/@ericblade/quagga2" in html
    assert "Quagga.init" in html
