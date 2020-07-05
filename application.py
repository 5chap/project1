import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Define the default route
@app.route("/")
def index():
    Hello = "Greetings!"
    return render_template("index.html", Hello = Hello)

# Register route gets user details from register template
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a user."""
    # Get form information
    if request.method == "POST":
        username = request.form["name"]
        password = request.form["password"]
        error = None

    # Check if user entered name and password in the username and password fields
    # Check if username already exist in the database
    if not username:
        error = "Pls enter username."
    elif not password:
        error = "Pls enter password."
    elif db.execute(
        "SELECT id FROM users WHERE username = :name", {"name":username}).fetchone() is not None:
        error = "Pls user {} already exist.".format(username)

    # Insert username and password into database table users
    if error is None:
        db.execute(
            "INSERT INTO users (username, password) VALUES (:name, :pword)",
            {"name":username, "pword":generate_password_hash(password)}
        )
        db.commit()

        # Redirect registered user to login route
        return redirect(url_for("login"))

    # Display error on index template
    return render_template("index.html", error = error)

# Accept user login credentials
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["name"]
        password = request.form["password"]
        error = None

        # Check if given username and password is valid
        user = db.execute("SELECT * FROM users WHERE username = :name", {"name":username}).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        # Create a user session
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("search"))

        flash(error)

    return render_template("login.html")

# Route to search for a book based on isbn, book title or author
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        bookName = request.form['bookName']

        # search by isbn, author or book title
        results=db.execute("SELECT * FROM books WHERE isbn=:Input OR title=:Input OR author=:Input",
        {"Input":bookName, "Input":bookName, "Input":bookName}).fetchall()

        # What to do if no result was found
        if results is None:
            notFound="Sorry,the book you are looking for is currently not available"
            render_template("search.html", notFound=notFound)

        # If matching result is found, display result on search template
        return render_template("search.html", results=results)
    return render_template("search.html")

# Select book details based on book Id and render the result on book template
@app.route("/books/<int:book_id>")
def books(book_id):
    """Lists details about a single book."""
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")
    return render_template("book.html", book=book)


# Route to logout user and end session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
