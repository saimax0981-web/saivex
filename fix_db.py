import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", "sqlite:///saivex.db")
print("DATABASE_URL =", db_url)

if not db_url.startswith("sqlite:///"):
    print("This fixer is only for SQLite.")
    raise SystemExit

db_path = db_url.replace("sqlite:///", "")

if db_path.startswith("/"):
    db_path = db_path[1:]

db_path = Path(db_path)
print("Fixing database:", db_path.resolve())

db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

if "user" not in tables:
    print("No user table found. App will create it on next run.")
else:
    cols = [r[1] for r in cur.execute("PRAGMA table_info(user)").fetchall()]
    print("Before:", cols)

    if "is_email_verified" not in cols:
        cur.execute("ALTER TABLE user ADD COLUMN is_email_verified BOOLEAN DEFAULT 1")
        print("Added is_email_verified")

    if "created_at" not in cols:
        cur.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
        print("Added created_at")

    cols = [r[1] for r in cur.execute("PRAGMA table_info(user)").fetchall()]
    print("After:", cols)

conn.commit()
conn.close()

print("Database fixed successfully.")