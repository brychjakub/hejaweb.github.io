from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": [
        "https://hejaboys.cz",
        "https://www.hejaboys.cz",
        "https://brychjakub.github.io",
    ]}
})

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
        rows = query("""
            SELECT id, nazev, datum, misto, cas, popis, public
            FROM akce
            ORDER BY datum ASC, cas ASC
        """)

    return jsonify([dict(r) for r in rows])


# POST – pridani akce
@app.route("/api/akce", methods=["POST", "OPTIONS"])
def add_akce():
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json()

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
def delete_akce(id):
    if request.method == "OPTIONS":
        return "", 200

    query("DELETE FROM akce WHERE id = ?", (id,))
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    app.run()