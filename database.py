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
    """)
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
