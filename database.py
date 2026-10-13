"""SQLite connection and schema management."""
import os
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            batch_number TEXT NOT NULL COLLATE NOCASE UNIQUE,
            category TEXT NOT NULL,
            manufacturer TEXT NOT NULL DEFAULT '',
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            min_stock INTEGER NOT NULL CHECK(min_stock >= 0),
            manufacturing_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            supplier TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_medicines_expiry ON medicines(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_medicines_stock ON medicines(quantity, min_stock);
        CREATE INDEX IF NOT EXISTS idx_medicines_name ON medicines(name);
    """)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
