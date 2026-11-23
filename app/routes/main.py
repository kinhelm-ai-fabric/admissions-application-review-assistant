"""Main application routes — dashboard, applicants, reviews."""

import logging

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify,
)

from app.routes.auth import login_required
from app.services import applicant_service, review_service, kindo_service

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


# ── Dashboard ─────────────────────────────────────────────────────────

@main_bp.route("/")
@login_required
def dashboard():
    try:
        stats = applicant_service.get_applicant_stats()
    except Exception as exc:
        logger.exception("dashboard: service error — %s", exc)
        stats = {"total": 0, "pending": 0, "reviewed": 0, "admitted": 0, "denied": 0, "waitlisted": 0}

    try:
        recent = applicant_service.list_applicants()[:5]
    except Exception as exc:
        logger.exception("dashboard: service error — %s", exc)
        recent = []

    return render_template("pages/dashboard.html", stats=stats, recent=recent)


# ── Applicants ────────────────────────────────────────────────────────

@main_bp.route("/applicants")
@login_required
def applicants():
    status_filter = request.args.get("status", "all")
    try:
        apps = applicant_service.list_applicants(status=status_filter)
    except Exception as exc:
        logger.exception("applicants: service error — %s", exc)
        return render_template("errors/500.html"), 500

    if apps is None:
        apps = []
    return render_template("pages/applicants.html", applicants=apps, current_status=status_filter)


@main_bp.route("/applicants/new", methods=["GET", "POST"])
@login_required
def new_applicant():
    if request.method == "POST":
        data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "gpa": _parse_float(request.form.get("gpa")),
            "test_score": _parse_int(request.form.get("test_score")),
            "intended_major": request.form.get("intended_major", "").strip(),
            "essay": request.form.get("essay", "").strip(),
            "extracurriculars": request.form.get("extracurriculars", "").strip(),
        }
        if not data["first_name"] or not data["last_name"] or not data["email"]:
            flash("First name, last name, and email are required.", "danger")
            return render_template("pages/new_applicant.html", data=data)
        try:
            app_id = applicant_service.create_applicant(data)
        except Exception as exc:
            logger.exception("new_applicant: service error — %s", exc)
            flash("Failed to create applicant.", "danger")
            return render_template("pages/new_applicant.html", data=data)

        flash("Applicant added successfully.", "success")
        return redirect(url_for("main.view_applicant", applicant_id=app_id))
    return render_template("pages/new_applicant.html", data={})


@main_bp.route("/applicants/<int:applicant_id>")
@login_required
def view_applicant(applicant_id):
    try:
        applicant = applicant_service.get_applicant(applicant_id)
    except Exception as exc:
        logger.exception("view_applicant: service error — %s", exc)
        return render_template("errors/500.html"), 500

    if applicant is None:
        flash("Applicant not found.", "warning")
        return redirect(url_for("main.applicants"))

    try:
        reviews = review_service.list_reviews_for_applicant(applicant_id)
    except Exception as exc:
        logger.exception("view_applicant: service error loading reviews — %s", exc)
        reviews = []

    return render_template("pages/view_applicant.html", applicant=applicant, reviews=reviews)


@main_bp.route("/applicants/<int:applicant_id>/review", methods=["POST"])
@login_required
def submit_review(applicant_id):
    try:
        applicant = applicant_service.get_applicant(applicant_id)
    except Exception as exc:
        logger.exception("submit_review: service error — %s", exc)
        flash("Failed to load applicant.", "danger")
        return redirect(url_for("main.applicants"))

    if applicant is None:
        flash("Applicant not found.", "warning")
        return redirect(url_for("main.applicants"))

    data = {
        "applicant_id": applicant_id,
        "reviewer_id": session.get("user_id"),
        "source": "manual",
        "academic_score": _parse_int(request.form.get("academic_score")),
        "essay_score": _parse_int(request.form.get("essay_score")),
        "extracurricular_score": _parse_int(request.form.get("extracurricular_score")),
        "overall_score": _parse_int(request.form.get("overall_score")),
        "recommendation": request.form.get("recommendation", ""),
        "notes": request.form.get("notes", "").strip(),
        "strengths": request.form.get("strengths", "").strip(),
        "concerns": request.form.get("concerns", "").strip(),
    }

    try:
        review_service.create_review(data)
    except Exception as exc:
        logger.exception("submit_review: service error — %s", exc)
        flash("Failed to save review.", "danger")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    # Update applicant status to "reviewed"
    try:
        applicant_service.update_applicant_status(applicant_id, "reviewed")
    except Exception as exc:
        logger.exception("submit_review: failed to update status — %s", exc)

    flash("Review submitted.", "success")
    return redirect(url_for("main.view_applicant", applicant_id=applicant_id))


@main_bp.route("/applicants/<int:applicant_id>/ai-review", methods=["POST"])
@login_required
def ai_review(applicant_id):
    """Request an AI-powered review from the Kindo agent."""
    try:
        applicant = applicant_service.get_applicant(applicant_id)
    except Exception as exc:
        logger.exception("ai_review: service error — %s", exc)
        flash("Failed to load applicant.", "danger")
        return redirect(url_for("main.applicants"))

    if applicant is None:
        flash("Applicant not found.", "warning")
        return redirect(url_for("main.applicants"))

    try:
        result = kindo_service.review_applicant(applicant)
    except Exception as exc:
        logger.exception("ai_review: Kindo agent error — %s", exc)
        flash("AI review failed. Please try again later.", "danger")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    if result is None:
        flash("AI review returned an invalid response. Please try again.", "warning")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    review_data = {
        "applicant_id": applicant_id,
        "reviewer_id": None,
        "source": "ai",
        "academic_score": result["academic_score"],
        "essay_score": result["essay_score"],
        "extracurricular_score": result["extracurricular_score"],
        "overall_score": result["overall_score"],
        "recommendation": result["recommendation"],
        "notes": result.get("notes", ""),
        "strengths": result.get("strengths", ""),
        "concerns": result.get("concerns", ""),
    }

    try:
        review_service.create_review(review_data)
    except Exception as exc:
        logger.exception("ai_review: failed to save review — %s", exc)
        flash("AI review generated but failed to save.", "danger")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    try:
        applicant_service.update_applicant_status(applicant_id, "reviewed")
    except Exception as exc:
        logger.exception("ai_review: failed to update status — %s", exc)

    flash("AI review completed successfully.", "success")
    return redirect(url_for("main.view_applicant", applicant_id=applicant_id))


@main_bp.route("/applicants/<int:applicant_id>/status", methods=["POST"])
@login_required
def update_status(applicant_id):
    new_status = request.form.get("status", "")
    if new_status not in ("pending", "reviewed", "admitted", "waitlisted", "denied"):
        flash("Invalid status.", "danger")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    try:
        applicant_service.update_applicant_status(applicant_id, new_status)
    except Exception as exc:
        logger.exception("update_status: service error — %s", exc)
        flash("Failed to update status.", "danger")
        return redirect(url_for("main.view_applicant", applicant_id=applicant_id))

    flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("main.view_applicant", applicant_id=applicant_id))


# ── Getting Started ───────────────────────────────────────────────────

@main_bp.route("/getting-started")
@login_required
def getting_started():
    return render_template("pages/getting_started.html")


# ── Theme toggle ──────────────────────────────────────────────────────

@main_bp.route("/toggle-theme", methods=["POST"])
def toggle_theme():
    current = session.get("theme", "light")
    session["theme"] = "dark" if current == "light" else "light"
    return redirect(request.referrer or url_for("main.dashboard"))


# ── Helpers ───────────────────────────────────────────────────────────

def _parse_float(val):
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None


def _parse_int(val):
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None
