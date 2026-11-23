import os
import sqlite3
import logging
import threading

logger = logging.getLogger(__name__)

_init_lock = threading.Lock()


def get_db_path(app=None):
    """Return the absolute database path."""
    if app:
        return app.config["DATABASE"]
    from flask import current_app
    return current_app.config["DATABASE"]


def get_db(app=None):
    """Return a new database connection."""
    path = get_db_path(app)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(app):
    """Create tables if they do not exist. Idempotent and thread-safe."""
    with _init_lock:
        conn = get_db(app)
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
            logger.info("Database initialized at %s", app.config["DATABASE"])
        finally:
            conn.close()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    full_name   TEXT    NOT NULL DEFAULT '',
    role        TEXT    NOT NULL DEFAULT 'reviewer',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applicants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL,
    gpa             REAL,
    test_score      INTEGER,
    intended_major  TEXT    NOT NULL DEFAULT '',
    essay           TEXT    NOT NULL DEFAULT '',
    extracurriculars TEXT   NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'pending',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id    INTEGER NOT NULL REFERENCES applicants(id),
    reviewer_id     INTEGER REFERENCES users(id),
    source          TEXT    NOT NULL DEFAULT 'manual',
    academic_score  INTEGER,
    essay_score     INTEGER,
    extracurricular_score INTEGER,
    overall_score   INTEGER,
    recommendation  TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    strengths       TEXT    NOT NULL DEFAULT '',
    concerns        TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Seed a default admin user (password: admin). Idempotent.
INSERT OR IGNORE INTO users (username, password, full_name, role)
VALUES ('admin', 'admin', 'Administrator', 'admin');
"""
