from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

APP_NAME = "MN Laser Lab Manager"
DB_FILE = "mn_laser_lab.db"


def user_data_dir() -> Path:
    forced = os.environ.get("MN_USER_DATA_DIR", "").strip()
    if forced:
        return Path(forced)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    return Path.home() / ".mn_laser_lab_manager"


def db_path() -> Path:
    user_data_dir().mkdir(parents=True, exist_ok=True)
    return user_data_dir() / DB_FILE


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            INSERT OR IGNORE INTO meta(key, value) VALUES('schema_version', '37_webapp');

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                collection TEXT DEFAULT '',
                status TEXT DEFAULT 'idea',
                description TEXT DEFAULT '',
                labor_minutes INTEGER DEFAULT 0,
                machine_minutes INTEGER DEFAULT 0,
                material_cost REAL DEFAULT 0,
                extra_cost REAL DEFAULT 0,
                suggested_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT DEFAULT '',
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                subcategory TEXT DEFAULT '',
                supplier TEXT DEFAULT '',
                unit TEXT DEFAULT 'pz',
                quantity REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                min_stock REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bom_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                inventory_item_id INTEGER,
                description TEXT NOT NULL,
                quantity REAL DEFAULT 1,
                unit_cost REAL DEFAULT 0,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY(inventory_item_id) REFERENCES inventory_items(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                customer_id INTEGER,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'preventivo',
                total REAL DEFAULT 0,
                deposit REAL DEFAULT 0,
                due_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL
            );
            """
        )


def load_legacy_state() -> dict:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT value FROM app_state WHERE key='main'").fetchone()
    if not row:
        return {}
    try:
        return json.loads(row["value"])
    except Exception:
        return {}


def save_legacy_state(data: dict) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO app_state(key,value,updated_at) VALUES('main',?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (json.dumps(data, ensure_ascii=False), now_iso()),
        )
