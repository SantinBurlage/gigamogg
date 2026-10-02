"""Система аутентификации и база данных пользователей GIGAMOGG.

SQLite база данных:
- Регистрация и авторизация (хеширование паролей sha256 + salt)
- Роли: 'admin' (полный доступ к ML-нитям, бенчмаркам, API-ключам) и 'user' (чистый интерфейс диалога)
- Главный администратор по умолчанию: Santin (Кирилл Бакунин)
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import time
from typing import Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "giga.db")
_LOCK = threading.RLock()


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    salted = (salt + password).encode("utf-8")
    pwd_hash = hashlib.sha256(salted).hexdigest()
    return pwd_hash, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    expected_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(expected_hash, stored_hash)


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _LOCK:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

        # Создаем администратора Santin по умолчанию, если пользователей нет
        cursor.execute("SELECT id FROM users WHERE username = 'Santin'")
        if not cursor.fetchone():
            pwd_hash, salt = _hash_password("santin123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("Santin", pwd_hash, salt, "admin", time.time())
            )
            conn.commit()
        conn.close()


def register_user(username: str, password: str) -> dict[str, Any]:
    username = username.strip()
    if not username or len(username) < 3:
        return {"error": "Имя пользователя должно содержать не менее 3 символов."}
    if not password or len(password) < 4:
        return {"error": "Пароль должен содержать не менее 4 символов."}

    with _LOCK:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        if cursor.fetchone():
            conn.close()
            return {"error": "Пользователь с таким именем уже существует."}

        pwd_hash, salt = _hash_password(password)
        # Если регистрируется Santin или Кирилл — роль admin, иначе user
        role = "admin" if username.lower() in ("santin", "admin", "kirill", "бакунин") else "user"
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, pwd_hash, salt, role, time.time())
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = secrets.token_hex(24)
        cursor.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, time.time())
        )
        conn.commit()
        conn.close()

        return {
            "ok": True,
            "token": token,
            "user": {
                "id": user_id,
                "username": username,
                "role": role,
            }
        }


def login_user(username: str, password: str) -> dict[str, Any]:
    username = username.strip()
    with _LOCK:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, salt, role FROM users WHERE LOWER(username) = LOWER(?)",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": "Пользователь не найден."}

        if not _verify_password(password, row["password_hash"], row["salt"]):
            conn.close()
            return {"error": "Неверный пароль."}

        token = secrets.token_hex(24)
        cursor.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, row["id"], time.time())
        )
        conn.commit()
        conn.close()

        return {
            "ok": True,
            "token": token,
            "user": {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
            }
        }


def get_user_by_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    clean_token = token.replace("Bearer ", "").strip()
    with _LOCK:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (clean_token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(id=row["id"], username=row["username"], role=row["role"])
        return None


def logout_user(token: str | None):
    if not token:
        return
    clean_token = token.replace("Bearer ", "").strip()
    with _LOCK:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (clean_token,))
        conn.commit()
        conn.close()


init_db()
