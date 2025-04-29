import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import flask_login
import requests
from bson.objectid import ObjectId

load_dotenv()
DB_URI = os.getenv("URI")
DB_NAME = os.getenv("DBNAME")

client = MongoClient(DB_URI)
db = client[DB_NAME]

users_collection = db["users"]
users_collection.create_index("email", unique = True)

books_collection = db["books"]

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "supersecret")  

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        return None
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        return None
    user = User()
    user.id = email
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

@app.route('/')
def home():
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('scanner.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    password = request.form['password']

    user_data = users_collection.find_one({"email": email, "password": password})

    if user_data:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for('home'))

    return 'Bad login'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    email = request.form['email']
    password = request.form['password']

    if users_collection.find_one({"email": email}):
        return 'User already exists'

    users_collection.insert_one({"email": email, "password": password})
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@app.route("/scanner")
@flask_login.login_required
def scanner():
    user_email = flask_login.current_user.id
    books = list(books_collection.find({"owner": user_email}))
    return render_template("scanner.html", books=books)

# This handles extracting the isbn and using it to search for the book on OpenLibrary
@app.route("/items/<isbn>")
@flask_login.login_required
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
@flask_login.login_required
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
        isbn_list = result.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else None

        if title and authors:
            book = {
                "title": title,
                "authors": authors,
                "cover": (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                    if cover_id
                    else None
                ),
                "isbn": isbn,
                "source": "Searched",
            }
            books.append(book)

    if not books:
        return {"error": "No books found"}, 404

    if partial:
        return render_template("searches.html", books=books)

    return render_template("searches.html", books=books)

@app.route("/library")
@flask_login.login_required
def library():
    user_email = flask_login.current_user.id
    books = list(books_collection.find({"owner": user_email}))
    return render_template("category.html", books=books)

@app.route("/library/<book_id>/category", methods=["POST"])
@flask_login.login_required
def update_category(book_id):
    user_email = flask_login.current_user.id
    action = request.form.get("action")

    if action == "update":
        category = request.form.get("category")
        books_collection.update_one(
            {"_id": ObjectId(book_id), "owner": user_email},
            {"$set": {"category": category}}
        )
    elif action == "remove":
        books_collection.delete_one(
            {"_id": ObjectId(book_id), "owner": user_email}
        )

    return redirect(url_for("library"))

@app.route("/save_book", methods=["POST"])
@flask_login.login_required
def save_book():
    data = request.form
    title = data.get("title")
    authors = data.getlist("authors")  
    isbn = data.get("isbn")
    cover = data.get("cover")

    user_email = flask_login.current_user.id

    books_collection.insert_one({
        "owner": user_email,
        "title": title,
        "authors": authors,
        "isbn": isbn,
        "cover": cover,
        "category": None
    })

    return redirect(url_for("library")) 

@app.route("/library/<book_id>/remove", methods=["POST"])
@flask_login.login_required
def remove_book(book_id):
    user_email = flask_login.current_user.id

    books_collection.delete_one({
        "_id": ObjectId(book_id),
        "owner": user_email
    })

    return redirect(url_for("library"))

if __name__ == "__main__":
    app.run(debug=True)
