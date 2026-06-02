"""Simple CLI helper to create or update auth users for Heja Boys backend."""

import argparse
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash

DB = "/home/HejaBoys/hejaWeb/data.db"


def query(sql, params=(), fetchone=False):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    rows = cur.fetchall()
    con.close()
    return (rows[0] if rows else None) if fetchone else rows


def init_tables():
    query("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
            active INTEGER NOT NULL DEFAULT 1
        )
    """)


def list_users():
    rows = query("SELECT id, username, role, active FROM users ORDER BY id ASC")
    if not rows:
        print("No users found.")
        return

    print("id | username | role | active")
    for row in rows:
        print(f"{row['id']} | {row['username']} | {row['role']} | {row['active']}")


def upsert_user(username, role, active, password):
    password_hash = generate_password_hash(password)
    existing = query("SELECT id FROM users WHERE username = ?", (username,), fetchone=True)

    if existing:
        query(
            "UPDATE users SET password_hash = ?, role = ?, active = ? WHERE username = ?",
            (password_hash, role, active, username),
        )
        print(f"Updated user: {username}")
    else:
        query(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, active),
        )
        print(f"Created user: {username}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/update/list users for Heja auth")
    parser.add_argument("--list", action="store_true", help="List existing users")
    parser.add_argument("--username", help="Username to create/update")
    parser.add_argument("--role", choices=["admin", "member"], default="member")
    parser.add_argument("--inactive", action="store_true", help="Set user as inactive")
    args = parser.parse_args()

    init_tables()

    if args.list:
        list_users()
    else:
        if not args.username:
            raise SystemExit("--username is required unless --list is used")

        password = getpass("Password (hidden): ")
        password2 = getpass("Repeat password: ")
        if password != password2:
            raise SystemExit("Passwords do not match")
        if len(password) < 8:
            raise SystemExit("Password must be at least 8 characters")

        upsert_user(args.username.strip(), args.role, 0 if args.inactive else 1, password)
