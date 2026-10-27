"""
ClubHub Database Helper Module (db.py)
Provides reusable SQLite connection management with strict foreign key enforcement.
"""

import os
import sqlite3
from flask import g, current_app

# Absolute path to the database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "clubhub.db")


def get_db():
    """
    Returns an open SQLite database connection for the current request context.
    Configures row_factory to sqlite3.Row for dictionary-like column access
    and strictly enforces foreign keys using PRAGMA foreign_keys = ON.
    """
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE', DEFAULT_DB_PATH)
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        # Enable column name access: row['column_name']
        g.db.row_factory = sqlite3.Row
        # STRICT FOREIGN KEY ENFORCEMENT ON EVERY CONNECTION
        g.db.execute("PRAGMA foreign_keys = ON;")

    return g.db


def close_db(e=None):
    """
    Closes the database connection at the end of the request.
    Registered with the Flask application teardown context.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """
    Helper function to execute a parameterized SELECT query.
    Returns a list of dicts, or a single dict if one=True.
    """
    cursor = get_db().execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return dict(rows[0]) if rows else None
    return [dict(row) for row in rows]


def execute_db(query, args=()):
    """
    Helper function to execute an INSERT, UPDATE, or DELETE parameterized query.
    Returns the cursor for accessing lastrowid and rowcount.
    """
    db = get_db()
    cursor = db.execute(query, args)
    db.commit()
    return cursor


def init_app(app):
    """
    Registers database teardown hooks with the Flask application.
    """
    app.teardown_appcontext(close_db)

