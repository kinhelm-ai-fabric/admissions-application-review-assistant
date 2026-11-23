"""Applicant data access service."""

import logging

from app.models.database import get_db

logger = logging.getLogger(__name__)


def list_applicants(status=None):
    """Return all applicants, optionally filtered by status."""
    conn = get_db()
    try:
        if status and status != "all":
            rows = conn.execute(
                "SELECT * FROM applicants WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applicants ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_applicant(applicant_id):
    """Return a single applicant by ID, or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM applicants WHERE id = ?", (applicant_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_applicant(data):
    """Insert a new applicant. Returns the new ID."""
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO applicants
               (first_name, last_name, email, gpa, test_score,
                intended_major, essay, extracurriculars)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["first_name"],
                data["last_name"],
                data["email"],
                data.get("gpa"),
                data.get("test_score"),
                data.get("intended_major", ""),
                data.get("essay", ""),
                data.get("extracurriculars", ""),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_applicant_status(applicant_id, status):
    """Update an applicant's status."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE applicants SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, applicant_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_applicant_stats():
    """Return counts by status."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM applicants GROUP BY status"
        ).fetchall()
        stats = {r["status"]: r["count"] for r in rows}
        stats["total"] = sum(stats.values())
        return stats
    finally:
        conn.close()
