"""Управление API-ключами GIGAMOGG.

Позволяет генерировать, просматривать, удалять и валидировать API-ключи
для интеграции с внешними программами, скриптами Python, расширениями и cURL
через совместимый со стандартом OpenAI API эндпоинт (/v1/chat/completions).
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
from typing import Any

KEYS_FILE = "keys.json"
_lock = threading.RLock()


def _load_data() -> dict[str, Any]:
    if not os.path.exists(KEYS_FILE):
        # Создаем ключ по умолчанию при первом запуске
        default_key = {
            "id": "key_default",
            "name": "Основной ключ (Default)",
            "key": "gm_live_" + secrets.token_hex(16),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_used_at": "Никогда",
            "total_calls": 0,
        }
        data = {"keys": [default_key]}
        _save_data(data)
        return data
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"keys": []}


def _save_data(data: dict[str, Any]) -> None:
    tmp = KEYS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, KEYS_FILE)


def list_keys() -> list[dict[str, Any]]:
    with _lock:
        data = _load_data()
        return data.get("keys", [])


def create_key(name: str | None = None) -> dict[str, Any]:
    with _lock:
        data = _load_data()
        clean_name = (name or "").strip() or f"Ключ #{len(data.get('keys', [])) + 1}"
        new_item = {
            "id": "key_" + secrets.token_hex(4),
            "name": clean_name,
            "key": "gm_live_" + secrets.token_hex(16),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_used_at": "Никогда",
            "total_calls": 0,
        }
        data.setdefault("keys", []).insert(0, new_item)
        _save_data(data)
        return new_item


def delete_key(key_or_id: str) -> bool:
    with _lock:
        data = _load_data()
        keys = data.get("keys", [])
        before = len(keys)
        keys = [k for k in keys if k.get("key") != key_or_id and k.get("id") != key_or_id]
        if len(keys) < before:
            data["keys"] = keys
            _save_data(data)
            return True
        return False


def verify_and_touch_key(raw_auth: str | None) -> bool:
    """Проверяет токен (из Authorization: Bearer <key> или x-api-key) и обновляет статистику."""
    if not raw_auth:
        return False
    token = raw_auth.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    with _lock:
        data = _load_data()
        for k in data.get("keys", []):
            if secrets.compare_digest(k.get("key", ""), token):
                k["total_calls"] = k.get("total_calls", 0) + 1
                k["last_used_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _save_data(data)
                return True
        return False
