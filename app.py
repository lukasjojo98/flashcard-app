from typing import Final

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlite3 import Error
from helpers import apology
from os import path
from dotenv import load_dotenv
import os
import sqlite3
from db import get_card_or_default

load_dotenv(".env")

PORT = os.environ.get("PORT")
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MiB
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        try:
            ROOT = path.dirname(path.realpath(__file__))
            conn = sqlite3.connect(path.join(ROOT, "users.db"))
            db = conn.cursor()
            db.execute(
                "SELECT * FROM user WHERE username = (?)",
                [request.form.get("username")],
            )
            conn.commit()
            rows = db.fetchall()

        except Error as e:
            print(e)

        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0][0]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    del session["user_id"]
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    ROOT = path.dirname(path.realpath(__file__))
    conn = sqlite3.connect(path.join(ROOT, "users.db"))
    db = conn.cursor()
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Username cant be blank")
        try:
            db.execute("SELECT username FROM user WHERE username = (?)", [username])
            conn.commit()
            rows = db.fetchall()

        except Error as e:
            print(e)
        if len(rows) > 0:
            row = rows[0]
            if username == row[0]:
                return apology("Username already taken")
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Password fields cant be empty")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords dont match")
        try:
            db.execute(
                "INSERT INTO user (username, hash) VALUES (?,?)",
                [username, generate_password_hash(password)],
            )
            conn.commit()
        except Error as e:
            print(e)

        try:
            db.execute("SELECT * FROM user WHERE username = ?", [username])
            conn.commit()
            rows = db.fetchall()
        except Error as e:
            print(e)
        row = rows[0]
        session["user_id"] = row[0]
        try:
            db.execute(
                "UPDATE user SET loggedfilms = 0 WHERE id = ?",
                [username, generate_password_hash(password)],
            )
            conn.commit()
        except Error as e:
            print(e)
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/", methods=["GET"])
@app.route("/decks", methods=["GET"])
def index() -> str:
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    try:
        ROOT = path.dirname(path.realpath(__file__))
        conn = sqlite3.connect(path.join(ROOT, "decks.db"))
        db = conn.cursor()
        db.execute("SELECT * FROM decks WHERE user_id = (?)", [user_id])
        conn.commit()
        decks = db.fetchall()
    except Error as e:
        print(e)
        return redirect("/login")

    return render_template("index.html", decks=decks)


@app.route("/study/<int:deck_id>", methods=["GET"])
def study(deck_id: int) -> str:
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    try:
        card_content = get_card_or_default(user_id, deck_id)
        print(card_content)
    except Error as e:
        print(e)
        return redirect("/login")

    if not card_content:
        return apology("No cards found", 404)

    return render_template(
        "study.html",
        card_id=card_content[0],
        question=card_content[3],
        answer=card_content[4],
        question_image=card_content[6],
        answer_image=card_content[7]
    )


@app.route("/api/v1/update_score/<card_id>", methods=["POST"])
def update_score(card_id: int) -> any:
    score: Final = request.get_json().get("four_score")

    try:
        ROOT = path.dirname(path.realpath(__file__))
        conn = sqlite3.connect(path.join(ROOT, "decks.db"))
        db = conn.cursor()
        db.execute(
            "UPDATE cards SET four_score = (?) WHERE user_id = (?) AND id = (?)",
            [score, session["user_id"], card_id],
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Score updated!"}), 200
    except Error as e:
        print(e)


@app.route("/add", methods=["GET", "POST"])
def add_deck() -> any:
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    if request.method == "POST":
        deck_name = request.form.get("deck_name")
        tags = request.form.get("tags")

        if not deck_name:
            return apology("Deck name cannot be blank", 400)

        try:
            ROOT = path.dirname(path.realpath(__file__))
            conn = sqlite3.connect(path.join(ROOT, "decks.db"))
            db = conn.cursor()
            db.execute(
                "INSERT INTO decks (user_id, name, cards) VALUES (?, ?, 0)",
                [user_id, deck_name],
            )
            conn.commit()
        except Error as e:
            print(e)
            return apology("Could not add deck", 500)

        return redirect("/decks")

    return render_template("add-decks.html")


@app.route("/decks/<deck_id>/add", methods=["GET", "POST"])
def add_card(deck_id: int) -> any:
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")
        question_image = request.files.get("question-image")
        answer_image = request.files.get("answer-image")

        a_path = ""
        q_path = ""

        if question_image and question_image.filename:
            q_filename = secure_filename(question_image.filename)
            q_path = os.path.join(app.config["UPLOAD_FOLDER"], q_filename)
            question_image.save(q_path)

        if answer_image and answer_image.filename:
            a_filename = secure_filename(answer_image.filename)
            a_path = os.path.join(app.config["UPLOAD_FOLDER"], a_filename)
            answer_image.save(a_path)

        print("question_image", question_image)
        print("answer_image", answer_image)

        try:
            ROOT = path.dirname(path.realpath(__file__))
            conn = sqlite3.connect(path.join(ROOT, "decks.db"))
            db = conn.cursor()
            db.execute(
                "INSERT INTO cards (user_id, deck_id, question, answer, four_score, question_image_path, answer_image_path) VALUES (?, ?, ?, ?, 0, ?, ?)",
                [user_id, deck_id, question, answer, q_filename, a_filename],
            )
            conn.commit()
            db.execute(
                "SELECT cards FROM decks WHERE id = (?) AND user_id = (?)",
                [deck_id, user_id],
            )
            conn.commit()

            result = db.fetchall()
            card_count = result[0][0] + 1

            db.execute(
                "UPDATE decks SET cards = (?) WHERE id = (?) AND user_id = (?)",
                [card_count, deck_id, user_id],
            )
            conn.commit()

        except Error as e:
            print(e)
            return apology("Could not add card", 500)

        return redirect("/decks")

    return render_template("add-cards.html", deck_id=deck_id)


if __name__ == "__main__":
    app.run("0.0.0.0", port=PORT)
