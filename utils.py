import os
import json
import base64
import sqlite3
from contextlib import contextmanager
from eth_account import Account

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallets.db")
NATIVE_SYMBOLS = {
    "ETH": "ETH",
    "POL": "POL",
    "BNB": "BNB",
    "ARB": "ETH",
    "AVAX": "AVAX",
}

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wallets (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE,
                keystore TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS networks (
                code    TEXT PRIMARY KEY,
                rpc_url TEXT NOT NULL
            )
            """
        )
        conn.commit()

    try:
        os.chmod(DB_PATH, 0o600)
    except OSError: pass

def validate_password(password: str) -> None:
    if not password or len(password) < 8:
        raise ValueError("Password length should be more than 8 characters.")

def encrypt_private_key(private_key: str, password: str) -> str:
    keystore_dict = Account.encrypt(private_key, password)
    keystore_json = json.dumps(keystore_dict)
    return base64.b64encode(keystore_json.encode("utf-8")).decode("utf-8")

def decrypt_private_key(encoded_keystore: str, password: str) -> str:
    keystore_json = base64.b64decode(encoded_keystore.encode("utf-8")).decode("utf-8")
    keystore_dict = json.loads(keystore_json)
    try:
        private_key_bytes = Account.decrypt(keystore_dict, password)
    except ValueError:
        raise ValueError("Password is wrong.")
    return "0x" + private_key_bytes.hex()

def list_wallets():
    with get_connection() as conn:
        rows = conn.execute("SELECT id, address, keystore FROM wallets ORDER BY id").fetchall()
    return [
        {"index": r["id"], "address": r["address"], "keystore": r["keystore"]}
        for r in rows
    ]

def get_wallet(wallet_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT id, address, keystore FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
    if not row:
        return None
    return {"index": row["id"], "address": row["address"], "keystore": row["keystore"]}

def add_wallet(address: str, encoded_keystore: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO wallets (address, keystore) VALUES (?, ?)",
            (address, encoded_keystore),
        )
        conn.commit()
        return cur.lastrowid

def list_networks():
    with get_connection() as conn:
        rows = conn.execute("SELECT code, rpc_url FROM networks ORDER BY code").fetchall()
    return {r["code"]: r["rpc_url"] for r in rows}

def add_network(code: str, rpc_url: str) -> str:
    code = code.strip().upper()
    if not code or not rpc_url:
        raise ValueError("Both code and rpc_url are required.")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO networks (code, rpc_url) VALUES (?, ?)
            ON CONFLICT(code) DO UPDATE SET rpc_url = excluded.rpc_url
            """,
            (code, rpc_url),
        )
        conn.commit()
    return code

def delete_network(code: str) -> bool:
    code = code.strip().upper()
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM networks WHERE code = ?", (code,))
        conn.commit()
        return cur.rowcount > 0

def get_network(code: str):
    networks = list_networks()
    code = code.strip().upper()
    if code not in networks:
        raise ValueError(f"Network '{code}' not found.")
    return code, networks[code]