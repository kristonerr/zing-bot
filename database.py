import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "zing.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id TEXT PRIMARY KEY,
            language TEXT DEFAULT 'ru',
            premium_until TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            roast_count INTEGER DEFAULT 0,
            premium_until TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS bans (
            guild_id TEXT,
            user_id TEXT,
            banned_until TEXT,
            PRIMARY KEY (guild_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            username TEXT,
            joined_at TEXT DEFAULT (datetime('now')),
            stage TEXT DEFAULT 'greeting',
            interest TEXT,
            email TEXT,
            converted INTEGER DEFAULT 0,
            score TEXT DEFAULT 'new',
            notes TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    # Migrate existing tables
    for col in ["score TEXT DEFAULT 'new'", "thread_id TEXT"]:
        try:
            cur.execute(f"ALTER TABLE leads ADD COLUMN {col}")
        except:
            pass
    for col in ["onboard_channel_id TEXT", "auto_role_id TEXT"]:
        try:
            cur.execute(f"ALTER TABLE guilds ADD COLUMN {col}")
        except:
            pass
    conn.commit()
    conn.close()

def is_premium_guild(guild_id: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT premium_until FROM guilds WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    conn.close()
    if row and row["premium_until"]:
        until = datetime.fromisoformat(row["premium_until"])
        return until > datetime.now()
    return False

def set_premium_guild(guild_id: str, days: int = 30):
    until = datetime.now().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO guilds (guild_id, premium_until) VALUES (?, ?)",
        (guild_id, until),
    )
    conn.commit()
    conn.close()

def increment_roast(user_id: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (user_id, roast_count) VALUES (?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET roast_count = roast_count + 1",
        (user_id,),
    )
    conn.commit()
    conn.close()

def get_guild_language(guild_id: str) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT language FROM guilds WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    conn.close()
    if row:
        return row["language"]
    return "ru"

def set_guild_language(guild_id: str, lang: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO guilds (guild_id, language) VALUES (?, ?) "
        "ON CONFLICT(guild_id) DO UPDATE SET language = excluded.language",
        (guild_id, lang),
    )
    conn.commit()
    conn.close()

def add_lead(guild_id: str, user_id: str, username: str):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM leads WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO leads (guild_id, user_id, username) VALUES (?, ?, ?)",
            (guild_id, user_id, username),
        )
        conn.commit()
    conn.close()

def update_lead_stage(guild_id: str, user_id: str, stage: str, notes: str = None):
    conn = get_db()
    if notes:
        conn.execute(
            "UPDATE leads SET stage = ?, notes = notes || '\n' || ?, updated_at = datetime('now') WHERE guild_id = ? AND user_id = ?",
            (stage, notes, guild_id, user_id),
        )
    else:
        conn.execute(
            "UPDATE leads SET stage = ?, updated_at = datetime('now') WHERE guild_id = ? AND user_id = ?",
            (stage, guild_id, user_id),
        )
    conn.commit()
    conn.close()

def update_lead_interest(guild_id: str, user_id: str, interest: str):
    conn = get_db()
    conn.execute(
        "UPDATE leads SET interest = ?, updated_at = datetime('now') WHERE guild_id = ? AND user_id = ?",
        (interest, guild_id, user_id),
    )
    conn.commit()
    conn.close()

def update_lead_score(guild_id: str, user_id: str, score: str):
    conn = get_db()
    conn.execute(
        "UPDATE leads SET score = ?, updated_at = datetime('now') WHERE guild_id = ? AND user_id = ?",
        (score, guild_id, user_id),
    )
    conn.commit()
    conn.close()

def get_lead(guild_id: str, user_id: str):
    conn = get_db()
    if guild_id:
        row = conn.execute(
            "SELECT * FROM leads WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM leads WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchone()
    conn.close()
    return row

def get_leads(guild_id: str, limit: int = 20):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM leads WHERE guild_id = ? ORDER BY updated_at DESC LIMIT ?",
        (guild_id, limit),
    ).fetchall()
    conn.close()
    return rows

def set_onboard_channel(guild_id: str, channel_id: str):
    conn = get_db()
    conn.execute(
        "UPDATE guilds SET onboard_channel_id = ? WHERE guild_id = ?",
        (channel_id, guild_id),
    )
    conn.commit()
    conn.close()

def get_onboard_channel(guild_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT onboard_channel_id FROM guilds WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    conn.close()
    return row["onboard_channel_id"] if row and row["onboard_channel_id"] else None

def update_lead_thread(guild_id: str, user_id: str, thread_id: str):
    conn = get_db()
    conn.execute(
        "UPDATE leads SET thread_id = ?, updated_at = datetime('now') WHERE guild_id = ? AND user_id = ?",
        (thread_id, guild_id, user_id),
    )
    conn.commit()
    conn.close()

def set_auto_role(guild_id: str, role_id: str):
    conn = get_db()
    conn.execute(
        "UPDATE guilds SET auto_role_id = ? WHERE guild_id = ?",
        (role_id, guild_id),
    )
    conn.commit()
    conn.close()

def get_auto_role(guild_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT auto_role_id FROM guilds WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    conn.close()
    return row["auto_role_id"] if row and row["auto_role_id"] else None

def is_banned(guild_id: str, user_id: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT banned_until FROM bans WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    conn.close()
    if row and row["banned_until"]:
        until = datetime.fromisoformat(row["banned_until"])
        return until > datetime.now()
    return False
