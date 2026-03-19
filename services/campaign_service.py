import sqlite3
import config


def _get_db():
    db = sqlite3.connect(config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    return db


def create_campaign(name: str, product: str, template_type: str, tone: str,
                    sender: str = '', pain_point: str = '') -> int:
    """Insert a new campaign into the database and return its ID."""
    db = _get_db()
    cursor = db.execute(
        'INSERT INTO campaigns (name, product, pain_point, template_type, tone, sender) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (name, product, pain_point, template_type, tone, sender)
    )
    db.commit()
    campaign_id = cursor.lastrowid
    db.close()
    return campaign_id
