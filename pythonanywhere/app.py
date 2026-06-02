from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
from werkzeug.security import check_password_hash
import secrets
import sqlite3

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": [
    "https://hejaboys.cz",
    "https://www.hejaboys.cz",
    "https://brychjakub.github.io",
]}})

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


def init_auth_tables():
    query("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    query("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    query("""
        CREATE TABLE IF NOT EXISTS account_balance (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            amount_czk INTEGER NOT NULL DEFAULT 0,
            updated_by INTEGER,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """)

    query("INSERT OR IGNORE INTO account_balance (id, amount_czk) VALUES (1, 0)")


def parse_bearer_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return ""


def get_current_user():
    token = parse_bearer_token()
    if not token:
        return None

    return query(
        """
        SELECT u.id, u.username, u.role
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND u.active = 1
        """,
        (token,),
        fetchone=True,
    )


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method == "OPTIONS":
            return "", 200

        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        request.current_user = user
        return f(*args, **kwargs)

    return wrapper


def require_admin(f):
    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        user = request.current_user
        if user["role"] != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)

    return wrapper


# AUTH
@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = query(
        "SELECT id, username, password_hash, role FROM users WHERE username = ? AND active = 1",
        (username,),
        fetchone=True,
    )

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = secrets.token_urlsafe(48)
    query("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user["id"]))

    return jsonify({"token": token, "user": {"username": user["username"], "role": user["role"]}})


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    user = request.current_user
    return jsonify({"username": user["username"], "role": user["role"]})


@app.route("/api/auth/logout", methods=["POST", "OPTIONS"])
def logout():
    if request.method == "OPTIONS":
        return "", 200

    token = parse_bearer_token()
    if token:
        query("DELETE FROM sessions WHERE token = ?", (token,))

    return jsonify({"status": "logged_out"})


# GET – stav spolecneho uctu
@app.route("/api/account", methods=["GET"])
@require_auth
def get_account_balance():
    account = query(
        """
        SELECT a.amount_czk, a.updated_at, u.username AS updated_by
        FROM account_balance a
        LEFT JOIN users u ON u.id = a.updated_by
        WHERE a.id = 1
        """,
        fetchone=True,
    )

    return jsonify({
        "amount_czk": account["amount_czk"],
        "updated_at": account["updated_at"],
        "updated_by": account["updated_by"],
    })


# PUT – uprava stavu spolecneho uctu
@app.route("/api/account", methods=["PUT", "OPTIONS"])
@require_admin
def update_account_balance():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}

    try:
        amount_czk = int(data.get("amount_czk"))
    except (TypeError, ValueError):
        return jsonify({"error": "Neplatna castka"}), 400

    user = request.current_user
    query(
        """
        UPDATE account_balance
        SET amount_czk = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
        """,
        (amount_czk, user["id"]),
    )

    return jsonify({"status": "updated", "amount_czk": amount_czk})


# GET – vypis akci
@app.route("/api/akce", methods=["GET"])
def get_akce():
    public_filter = (request.args.get("public") or "").strip().lower()

    if public_filter in {"1", "true", "yes"}:
        rows = query("""
            SELECT id, nazev, datum, misto, cas, popis, public
            FROM akce
            WHERE public = 1
            ORDER BY datum ASC, cas ASC
        """)
    else:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        rows = query("""
            SELECT id, nazev, datum, misto, cas, popis, public
            FROM akce
            ORDER BY datum ASC, cas ASC
        """)

    return jsonify([dict(r) for r in rows])


# POST – pridani akce
@app.route("/api/akce", methods=["POST", "OPTIONS"])
@require_admin
def add_akce():
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json() or {}

    query("""
        INSERT INTO akce (nazev, datum, misto, cas, popis, public)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["nazev"],
        data["datum"],
        data.get("misto", ""),
        data.get("cas", ""),
        data.get("popis", ""),
        int(data.get("public", 0))
    ))

    return jsonify({"status": "created"}), 201


# PUT – uprava akce / zverejneni
@app.route("/api/akce/<int:id>", methods=["PUT", "OPTIONS"])
@require_admin
def update_akce(id):
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}

    existing = query("SELECT * FROM akce WHERE id = ?", (id,), fetchone=True)
    if not existing:
        return jsonify({"error": "Akce nenalezena"}), 404

    updated_nazev = data.get("nazev", existing["nazev"])
    updated_datum = data.get("datum", existing["datum"])
    updated_misto = data.get("misto", existing["misto"])
    updated_cas = data.get("cas", existing["cas"])
    updated_popis = data.get("popis", existing["popis"])
    updated_public = int(data.get("public", existing["public"]))

    query("""
        UPDATE akce
        SET nazev = ?, datum = ?, misto = ?, cas = ?, popis = ?, public = ?
        WHERE id = ?
    """, (
        updated_nazev,
        updated_datum,
        updated_misto,
        updated_cas,
        updated_popis,
        updated_public,
        id
    ))

    return jsonify({"status": "updated"})


# DELETE – smazani akce
@app.route("/api/akce/<int:id>", methods=["DELETE", "OPTIONS"])
@require_admin
def delete_akce(id):
    if request.method == "OPTIONS":
        return "", 200

    query("DELETE FROM akce WHERE id = ?", (id,))
    return jsonify({"status": "deleted"})


init_auth_tables()

if __name__ == "__main__":
    app.run()
