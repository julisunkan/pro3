import sqlite3
import config


def create_campaign(name: str, product: str, template_type: str, tone: str,
                    sender: str = '', pain_point: str = '') -> int:
    """Insert a new campaign into the database and return its ID."""
    db = sqlite3.connect(config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    cursor = db.execute(
        'INSERT INTO campaigns (name, product, pain_point, template_type, tone, sender) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (name, product, pain_point, template_type, tone, sender)
    )
    db.commit()
    campaign_id = cursor.lastrowid
    db.close()
    return campaign_id
