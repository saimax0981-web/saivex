import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", "sqlite:///saivex_stage3.db")
print("DATABASE_URL =", db_url)

if not db_url.startswith("sqlite:///"):
    print("This migration is only for local SQLite. Cloud PostgreSQL will create tables from the app.")
    raise SystemExit

db_path = db_url.replace("sqlite:///", "")

# Flask-SQLAlchemy resolves relative sqlite paths inside instance folder.
if "/" not in db_path and "\\" not in db_path:
    path = Path("instance") / db_path
else:
    path = Path(db_path)

print("Fixing:", path.resolve())
path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(path)
cur = conn.cursor()

# Fix user table if needed
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if "user" in tables:
    cols = [r[1] for r in cur.execute("PRAGMA table_info(user)").fetchall()]
    if "is_email_verified" not in cols:
        cur.execute("ALTER TABLE user ADD COLUMN is_email_verified BOOLEAN DEFAULT 1")
        print("Added user.is_email_verified")
    if "created_at" not in cols:
        cur.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
        print("Added user.created_at")

# Create subscription table
cur.execute("""
CREATE TABLE IF NOT EXISTS subscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    status VARCHAR(30) DEFAULT 'active',
    razorpay_order_id VARCHAR(150) DEFAULT '',
    razorpay_payment_id VARCHAR(150) DEFAULT '',
    started_at DATETIME,
    expires_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES user(id)
)
""")
print("Subscription table ready")

conn.commit()
conn.close()
print("Business database migration complete.")
