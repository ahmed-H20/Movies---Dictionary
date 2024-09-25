import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///shows.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route('/search')
def search():
    data = request.args.get('title')
    if not data:
        return render_template("search.html")
    search_string= f"%{data}%"
    result_d = db.execute("SELECT title FROM shows WHERE title LIKE %s LIMIT 50", [search_string])
    return render_template("search.html",data=result_d)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        if not username:
            return apology("You must enter username")

        if not password:
            return apology("You must enter password")

        if not confirm:
            return apology("You must enter confirm password")

        if password != confirm:
            return apology("possword and confirm should be same")

        hash = generate_password_hash(password)

        try:
            user_ses = db.execute("INSERT INTO users (username, password) VALUES (?, ?)", username, hash)
        except:
            return apology("user alredy exist")

        session["user_id"] = user_ses
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/details", methods=["GET", "POST"])
def details():
        title = request.args.get("title")
        data = db.execute("SELECT * FROM shows WHERE title = ? GROUP BY UPPER(TRIM(shows.title))", title)
        stars = db.execute("SELECT DISTINCT name FROM people JOIN stars on people.id = stars.person_id JOIN shows on stars.show_id = shows.id WHERE shows.title = ? GROUP BY UPPER(TRIM(people.name))", title)
        writer = db.execute("SELECT DISTINCT name FROM people JOIN writers ON people.id = writers.person_id JOIN shows ON writers.show_id = shows.id WHERE shows.title = ? GROUP BY UPPER(TRIM(people.name))", title)
        genres = db.execute("SELECT genre FROM genres JOIN shows ON shows.id = genres.show_id WHERE shows.title = ?",title)
        rating_db = db.execute("SELECT rating FROM ratings JOIN shows ON ratings.show_id = shows.id WHERE shows.title = ? GROUP BY UPPER(TRIM(shows.title))", title)
        if not title:
            return apology("no title")
        if not data:
            return apology("no data")
        if not stars:
            stars = ""
        if not writer:
            writer = ""
        if not genres:
            genres = ""

        if not rating_db:
            return render_template("details.html",show=data,stars=stars,writers=writer,rating="-")
        ratings = rating_db[0]["rating"]
        if not title and not data and not stars and not writer and not rating_db:
            return apology("empty")
        return render_template("details.html",show=data,stars=stars,writers=writer,rating=ratings,genres=genres)



@app.route("/fav")
def fav():
    title = request.args.get("title")
    if not title:
        data=db.execute("SELECT favorites FROM users")
        return render_template("favorite.html",data=data)
    #check not to duplicate data in fav
    check_duel=db.execute("SELECT favorites FROM users WHERE favorites = ?",title)
    if check_duel != []:
        flash("Alrady in favorites")
        return redirect("/search")
    db.execute("INSERT INTO users (favorites) VALUES (?)" ,title)
    data=db.execute("SELECT favorites FROM users")
    return render_template("favorite.html",data=data)

@app.route("/delete")
def delete():
    title = request.args.get("title")
    if not title:
        flash("error")
        return redirect("/fav")
    db.execute("DELETE FROM users WHERE favorites = ?", title)
    return redirect("/fav")

@app.route("/star")
def star():
    star = request.args.get("star")
    data = db.execute("SELECT * FROM people WHERE name = ?", star)
    shows = db.execute("SELECT title FROM shows JOIN stars ON shows.id = stars.show_id JOIN people ON stars.person_id = people.id WHERE people.name = ?",star)
    return render_template("star.html",data=data,shows=shows)

@app.route("/writer")
def writer():
    writer = request.args.get("writer")
    data = db.execute("SELECT * FROM people WHERE name = ?", writer)
    shows = db.execute("SELECT title FROM shows JOIN writers ON shows.id = writers.show_id JOIN people ON writers.person_id = people.id WHERE people.name = ?",writer)
    return render_template("writer.html",data=data,shows=shows)
