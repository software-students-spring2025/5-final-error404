import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import requests

load_dotenv()
DB_URI = os.getenv("URI")
DB_NAME = os.getenv("DBNAME")

client = MongoClient(DB_URI)
db = client(DB_NAME)

app = Flask(__name__, template_folder="templates")

#scanner page acts as the home page
@app.route("/")
def index():
    return render_template("scanner.html")

# This handles extracting the isbn and using it to search for the book on OpenLibrary
@app.route("/items/<isbn>")
def get_book_info(isbn):
    url = (
        f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    )
    response = requests.get(url)
    data = response.json()

    book_data = data.get(f"ISBN:{isbn}")
    if not book_data:
        return {"error": "Book not found"}, 404

    book = {
        "title": book_data.get("title"),
        "authors": [author.get("name") for author in book_data.get("authors", [])],
        "cover": book_data.get("cover", {}).get("medium"),
        "isbn": isbn,
        "source": "Scanned",
    }

    if request.args.get("partial") == "true":
        return book, 200, {"Content-Type": "application/json"}

    return render_template("book.html", book=book)

#This handles searching for books using the OpenLibrary API via title, author or isbn
@app.route("/search")
def search_books():
    query = request.args.get("q", "")
    partial = request.args.get("partial", "false").lower() == "true"

    if not query:
        return {"error": "No query provided"}, 400

    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    data = response.json()
    results = data.get("docs", [])

    books = []
    for i, result in enumerate(results[:5]):
        title = result.get("title")
        authors = result.get("author_name", [])
        cover_id = result.get("cover_i")

        if title and authors:
            book = {
                "title": title,
                "authors": authors,
                "cover": (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                    if cover_id
                    else None
                ),
                "source": "Searched",
            }
            books.append(book)

    if not books:
        return {"error": "No books found"}, 404

    if partial:
        return render_template("searches.html", books=books)

    return render_template("searches.html", books=books)

# Displays saved books
@app.route("/library")
def library():
    books = []
    return render_template("category.html", books=books)

# Update Book Category
@app.route("/library/<book_id>/category", methods=["POST"])
def update_category(book_id):
    return redirect(url_for("view_library"))

if __name__ == "__main__":
    app.run(debug=True)
