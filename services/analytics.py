import sqlite3
import config


def _get_db():
    db = sqlite3.connect(config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    return db


def get_campaign_analytics(campaign_id: int) -> dict:
    """Return analytics metrics for a given campaign."""
    db = _get_db()

    row = db.execute(
        '''SELECT
            COUNT(*) as total,
            SUM(opened) as opens,
            SUM(replied) as replies
           FROM emails
           WHERE campaign_id = ?''',
        (campaign_id,)
    ).fetchone()
    db.close()

    total = row['total'] or 0
    opens = row['opens'] or 0
    replies = row['replies'] or 0

    open_rate = round((opens / total * 100), 1) if total > 0 else 0
    reply_rate = round((replies / total * 100), 1) if total > 0 else 0

    return {
        'total': total,
        'opens': opens,
        'replies': replies,
        'open_rate': open_rate,
        'reply_rate': reply_rate,
    }
