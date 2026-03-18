import sqlite3
import os
from flask import g
import config

def get_db():
    """Get a database connection, reusing one if it exists in the app context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def init_db():
    """Create all tables if they don't exist."""
    db = sqlite3.connect(config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS leads (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT,
            email    TEXT UNIQUE,
            company  TEXT,
            website  TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            product       TEXT NOT NULL,
            pain_point    TEXT DEFAULT "",
            template_type TEXT DEFAULT "short_pitch",
            tone          TEXT DEFAULT "friendly",
            sender        TEXT DEFAULT "",
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS emails (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER REFERENCES campaigns(id),
            lead_id     INTEGER REFERENCES leads(id),
            subject     TEXT,
            body        TEXT,
            opened      INTEGER DEFAULT 0,
            replied     INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER REFERENCES emails(id),
            reason      TEXT,
            reviewed    INTEGER DEFAULT 0,
            reported_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        INSERT OR IGNORE INTO settings (key, value) VALUES
            ("app_name", "Cold Email Generator"),
            ("default_sender", ""),
            ("default_tone", "friendly"),
            ("default_template", "short_pitch"),
            ("groq_model", "llama-3.3-70b-versatile"),
            ("groq_api_key", "");
    ''')
    db.commit()

    # Migrations: add columns introduced after initial schema
    migrations = [
        'ALTER TABLE campaigns ADD COLUMN pain_point TEXT DEFAULT ""',
    ]
    for sql in migrations:
        try:
            db.execute(sql)
            db.commit()
        except Exception:
            pass  # Column already exists

    db.close()
