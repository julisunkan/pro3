import sqlite3
import os
import config


def get_setting(key: str, default: str = '') -> str:
    """Read a single setting from the database, fall back to default."""
    try:
        db = sqlite3.connect(config.DATABASE_PATH)
        row = db.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
        db.close()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return default


def get_api_key() -> str:
    """
    Return the Groq API key.
    Priority: 1) Admin panel DB setting  2) GROQ_API_KEY env var
    """
    db_key = get_setting('groq_api_key', '')
    if db_key:
        return db_key
    return os.environ.get('GROQ_API_KEY', '')


def get_model() -> str:
    """Return the Groq model from settings, remapping deprecated names."""
    model = get_setting('groq_model', config.GROQ_MODEL)
    # Remap deprecated model names to current equivalents
    _deprecated = {
        'llama3-70b-8192': 'llama-3.3-70b-versatile',
        'llama3-8b-8192': 'llama-3.1-8b-instant',
        'mixtral-8x7b-32768': 'llama-3.3-70b-versatile',
    }
    return _deprecated.get(model, model) or config.GROQ_MODEL
