import pytest
from app import app, users_collection, books_collection
from flask import url_for
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


def test_register_success(client):
    users_collection.delete_many({})
    
    response = client.post("/register", data={
        "email": "newuser@example.com",
        "password": "newuserpassword123"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.location

    user = users_collection.find_one({"email": "newuser@example.com"})
    assert user is not None
    assert user["password"] == "newuserpassword123"


def test_login(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_success(client):
    response = client.post("/login", data={
        "email": "testuser@example.com",
        "password": "testpassword"
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert response.location.endswith(url_for("home"))
    
    with client.session_transaction() as sess:
        assert "_user_id" in sess
        assert sess["_user_id"] == "testuser@example.com"


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

def test_update_note_success(client):
    book_id = books_collection.insert_one({
        "owner": "testuser@example.com",
        "title": "Test Book",
        "authors": ["Test Author"],
        "notes": "Test Note"
    }).inserted_id

    response = client.post(
        f"/library/{book_id}/note",
        data={"note": "New Updated Test Note"}
    )

    assert response.status_code == 302
    updated_book = books_collection.find_one({"_id": book_id})
    assert updated_book["notes"] == "New Updated Test Note"


def test_update_note_unauthorized(client):
    book_id = books_collection.insert_one({
        "owner": "anotheruser@example.com",
        "title": "Another Book",
        "authors": ["Another Author"],
        "notes": "Another Note"
    }).inserted_id

    response = client.post(
        f"/library/{book_id}/note",
        data={"note": "Test Note"}
    )

    assert response.status_code == 302
    unchanged_book = books_collection.find_one({"_id": book_id})
    assert unchanged_book["notes"] == "Another Note"


def test_update_note_empty(client):
    book_id = books_collection.insert_one({
        "owner": "testuser@example.com",
        "title": "Test Book",
        "authors": ["Test Author"],
        "notes": "Test Note"
    }).inserted_id

    response = client.post(
        f"/library/{book_id}/note",
        data={"note": ""}
    )

    assert response.status_code == 302
    updated_book = books_collection.find_one({"_id": book_id})
    assert updated_book["notes"] == ""