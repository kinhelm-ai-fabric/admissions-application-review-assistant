"""Review data access service."""

import logging

from app.models.database import get_db

logger = logging.getLogger(__name__)


def list_reviews_for_applicant(applicant_id):
    """Return all reviews for a given applicant."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT r.*, u.full_name AS reviewer_name
               FROM reviews r
               LEFT JOIN users u ON r.reviewer_id = u.id
               WHERE r.applicant_id = ?
               ORDER BY r.created_at DESC""",
            (applicant_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_review(data):
    """Insert a new review. Returns the new ID."""
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO reviews
               (applicant_id, reviewer_id, source,
                academic_score, essay_score, extracurricular_score,
                overall_score, recommendation, notes, strengths, concerns)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["applicant_id"],
                data.get("reviewer_id"),
                data.get("source", "manual"),
                data.get("academic_score"),
                data.get("essay_score"),
                data.get("extracurricular_score"),
                data.get("overall_score"),
                data.get("recommendation", ""),
                data.get("notes", ""),
                data.get("strengths", ""),
                data.get("concerns", ""),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_review(review_id):
    """Return a single review or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
