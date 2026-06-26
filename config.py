"""
config.py — Manages app configuration including hashed credentials.
Credentials are stored as salted SHA-256 hashes; plaintext passwords
are never written to disk.
"""

import json
import os
import hashlib
import secrets

CONFIG_FILE = os.path.join("data", "config.json")

# Default password is "admin123" — user is prompted to change on first run.
DEFAULT_PASSWORD = "admin123"


def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, hashed


def _default_config() -> dict:
    salt, hashed = _hash_password(DEFAULT_PASSWORD)
    return {
        "password_salt": salt,
        "password_hash": hashed,
    }


def load_config() -> dict:
    """Load config from disk, creating it with defaults if missing."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        cfg = _default_config()
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Migrate: if old plaintext password key exists, re-hash and remove it
        if "password" in cfg:
            plain = cfg.pop("password")
            salt, hashed = _hash_password(plain)
            cfg["password_salt"] = salt
            cfg["password_hash"] = hashed
            save_config(cfg)
        return cfg
    except Exception:
        cfg = _default_config()
        save_config(cfg)
        return cfg


def save_config(cfg: dict):
    """Persist config to disk."""
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
