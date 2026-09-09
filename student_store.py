"""Student account helpers backed by SQLite rather than a shared JSON file."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from database import create_student, get_student, get_students, initialize_database


HASH_ITERATIONS = 310_000


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _password_matches(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return hmac.compare_digest(calculated, digest_hex)
    except (TypeError, ValueError):
        return False


def register_student(student: dict, password: str) -> dict:
    if len(password) < 8:
        raise ValueError("Use a password with at least 8 characters.")
    return create_student(student, _password_hash(password))


def authenticate_student(email: str, password: str) -> dict | None:
    if not email or not password:
        return None

    student = get_student(email, include_password_hash=True)
    if not student or not _password_matches(password, student.pop("password_hash")):
        return None
    return student


def load_students() -> list[dict]:
    return get_students()


def current_student(session_state) -> dict | None:
    return session_state.get("current_student")


def initialize_student_store() -> None:
    initialize_database()
