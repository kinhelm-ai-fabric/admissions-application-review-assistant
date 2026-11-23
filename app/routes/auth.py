"""Authentication routes."""

import logging
import functools

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash,
)

from app.models.database import get_db

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator that redirects to login if no session user."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            conn.close()
        except Exception as exc:
            logger.exception("login: database error — %s", exc)
            flash("An error occurred. Please try again.", "danger")
            return render_template("pages/login.html"), 500

        if user and user["password"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            next_url = request.args.get("next", "")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("pages/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("pages/register.html")

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)",
                (username, password, full_name),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.exception("register: database error — %s", exc)
            if "UNIQUE" in str(exc):
                flash("Username already exists.", "danger")
            else:
                flash("Registration failed.", "danger")
            return render_template("pages/register.html")

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("pages/register.html")
