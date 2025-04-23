from flask import Flask, render_template, request
import requests

app = Flask(__name__, template_folder = "templates")

@app.route('/')
def index():
    return render_template('scanner.html')

@app.route("/items/<isbn>")
def get_book_info(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    data = response.json()
    
    book_data = data.get(f"ISBN:{isbn}")
    if not book_data:
        return {"error": "Book not found"}, 404
    
    book = {
        "title": book_data.get("title"),
        "authors": [author.get("name") for author in book_data.get("authors", [])],
        "cover": book_data.get("cover", {}).get("medium"),
        "isbn": isbn
    }
    
    if request.args.get("partial") == "true":
        return render_template('book.html', book=book)
    
    return render_template('book.html', book=book)

if __name__ == '__main__':
    app.run(debug=True)
    