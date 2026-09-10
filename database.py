"""Student data storage for local development and managed PostgreSQL deployments.

SQLite remains useful for local work. A public student release must set
``EXAMIQ_DATABASE_URL`` to a managed PostgreSQL connection before it can claim
persistent cloud storage.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from neet_catalog import get_neet_papers


BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "database.db"

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # PostgreSQL is intentionally optional for local development.
    psycopg = None
    dict_row = None


INTEGRITY_ERRORS = (sqlite3.IntegrityError,)
if psycopg is not None:
    INTEGRITY_ERRORS += (psycopg.IntegrityError,)


def _configured_database_url() -> str:
    """Read the production URL from environment variables or Streamlit Secrets."""
    url = os.getenv("EXAMIQ_DATABASE_URL", "").strip()
    if url:
        return url

    try:
        import streamlit as st

        return str(st.secrets.get("EXAMIQ_DATABASE_URL", "")).strip()
    except Exception:
        return ""


def using_managed_postgres() -> bool:
    return _configured_database_url().startswith(("postgres://", "postgresql://"))


def storage_status() -> dict[str, str | bool]:
    """Return a truthful, user-facing description of the active storage backend."""
    if using_managed_postgres():
        return {
            "backend": "Managed PostgreSQL",
            "persistent": True,
            "detail": "Student records are stored in the configured managed database.",
        }
    return {
        "backend": "Local SQLite pilot",
        "persistent": False,
        "detail": "This Streamlit app instance can reset when the service restarts.",
    }


def _connection() -> Any:
    if using_managed_postgres():
        if psycopg is None:
            raise RuntimeError(
                "Managed PostgreSQL is configured, but psycopg is not installed. "
                "Install the project requirements before starting the app."
            )
        return psycopg.connect(_configured_database_url(), row_factory=dict_row)

    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _execute(connection: Any, query: str, parameters: tuple | list = ()) -> Any:
    """Use SQLite-style parameters locally and PostgreSQL-style parameters in cloud."""
    if using_managed_postgres():
        query = query.replace("?", "%s")
    return connection.execute(query, parameters)


def _executemany(connection: Any, query: str, parameters: list[tuple]) -> Any:
    if using_managed_postgres():
        query = query.replace("?", "%s")
    return connection.executemany(query, parameters)


def initialize_database() -> None:
    with _connection() as connection:
        if not using_managed_postgres():
            connection.execute("PRAGMA journal_mode = WAL")

        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS papers (
                paper_id TEXT PRIMARY KEY,
                exam TEXT NOT NULL,
                year INTEGER NOT NULL,
                session TEXT NOT NULL,
                subject TEXT NOT NULL,
                questions INTEGER NOT NULL,
                answer_key TEXT NOT NULL
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS students (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                exam TEXT NOT NULL,
                category TEXT NOT NULL,
                state TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS test_attempts (
                attempt_id TEXT PRIMARY KEY,
                student_email TEXT NOT NULL,
                paper_id TEXT NOT NULL,
                exam TEXT NOT NULL,
                year INTEGER NOT NULL,
                session TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                started_at DOUBLE PRECISION NOT NULL,
                submitted_at DOUBLE PRECISION,
                answers_json TEXT NOT NULL DEFAULT '{}',
                marked_for_review_json TEXT NOT NULL DEFAULT '[]',
                updated_at DOUBLE PRECISION NOT NULL,
                FOREIGN KEY (student_email) REFERENCES students(email)
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE INDEX IF NOT EXISTS idx_test_attempts_student_time
            ON test_attempts(student_email, updated_at DESC)
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                student_email TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL,
                rating INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                rank_useful TEXT NOT NULL,
                college_helpful TEXT NOT NULL,
                suggestions TEXT NOT NULL,
                FOREIGN KEY (student_email) REFERENCES students(email)
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS challenge_rooms (
                challenge_id TEXT PRIMARY KEY,
                share_code TEXT NOT NULL UNIQUE,
                host_email TEXT NOT NULL,
                paper_id TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL,
                FOREIGN KEY (host_email) REFERENCES students(email)
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS challenge_members (
                challenge_id TEXT NOT NULL,
                student_email TEXT NOT NULL,
                joined_at DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (challenge_id, student_email),
                FOREIGN KEY (challenge_id) REFERENCES challenge_rooms(challenge_id),
                FOREIGN KEY (student_email) REFERENCES students(email)
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS challenge_attempts (
                challenge_id TEXT NOT NULL,
                student_email TEXT NOT NULL,
                attempt_id TEXT NOT NULL,
                PRIMARY KEY (challenge_id, student_email),
                FOREIGN KEY (challenge_id) REFERENCES challenge_rooms(challenge_id),
                FOREIGN KEY (student_email) REFERENCES students(email),
                FOREIGN KEY (attempt_id) REFERENCES test_attempts(attempt_id)
            )
            """,
        )
        if not using_managed_postgres():
            # SQLite needs an explicit guard because a table constraint cannot
            # express "at most two rows for this challenge".
            _execute(
                connection,
                """
                CREATE TRIGGER IF NOT EXISTS limit_challenge_members
                BEFORE INSERT ON challenge_members
                WHEN (
                    SELECT COUNT(*)
                    FROM challenge_members
                    WHERE challenge_id = NEW.challenge_id
                ) >= 2
                BEGIN
                    SELECT RAISE(ABORT, 'This challenge already has two students.');
                END
                """,
            )

        _executemany(
            connection,
            """
            INSERT INTO papers (
                paper_id, exam, year, session, subject, questions, answer_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (paper_id) DO UPDATE SET
                exam = excluded.exam,
                year = excluded.year,
                session = excluded.session,
                subject = excluded.subject,
                questions = excluded.questions,
                answer_key = excluded.answer_key
            """,
            [
                (
                    paper["paper_id"],
                    paper["exam"],
                    paper["year"],
                    paper["session"],
                    paper["subject"],
                    paper["questions"],
                    paper["answer_key_file"],
                )
                for paper in get_neet_papers()
            ],
        )


def save_paper_metadata(rows: list[dict]) -> None:
    """Compatibility helper for future verified admin imports."""
    initialize_database()
    with _connection() as connection:
        _executemany(
            connection,
            """
            INSERT INTO papers (
                paper_id, exam, year, session, subject, questions, answer_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (paper_id) DO UPDATE SET
                exam = excluded.exam,
                year = excluded.year,
                session = excluded.session,
                subject = excluded.subject,
                questions = excluded.questions,
                answer_key = excluded.answer_key
            """,
            [
                (
                    row["paper_id"],
                    row["exam"],
                    int(row["year"]),
                    row["session"],
                    row["subject"],
                    int(row["questions"]),
                    row["answer_key"],
                )
                for row in rows
            ],
        )


def get_all_papers(exam: str | None = None) -> list[dict]:
    initialize_database()
    query = "SELECT paper_id, exam, year, session, subject, questions, answer_key FROM papers"
    parameters: tuple = ()
    if exam:
        query += " WHERE exam = ?"
        parameters = (exam,)
    query += " ORDER BY year DESC, session"

    with _connection() as connection:
        rows = _execute(connection, query, parameters).fetchall()
    return [dict(row) for row in rows]


def create_student(student: dict, password_hash: str) -> dict:
    initialize_database()
    email = student["email"].strip().lower()
    record = {
        "name": student["name"].strip(),
        "email": email,
        "mobile": student["mobile"].strip(),
        "exam": "NEET",
        "category": student["category"].strip(),
        "state": student["state"].strip(),
    }

    try:
        with _connection() as connection:
            _execute(
                connection,
                """
                INSERT INTO students (
                    email, name, mobile, exam, category, state, password_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["email"],
                    record["name"],
                    record["mobile"],
                    record["exam"],
                    record["category"],
                    record["state"],
                    password_hash,
                    time.time(),
                ),
            )
    except INTEGRITY_ERRORS as error:
        raise ValueError("An account with this email already exists. Please log in instead.") from error
    return record


def get_student(email: str, include_password_hash: bool = False) -> dict | None:
    initialize_database()
    columns = "email, name, mobile, exam, category, state"
    if include_password_hash:
        columns += ", password_hash"

    with _connection() as connection:
        row = _execute(
            connection,
            f"SELECT {columns} FROM students WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_students() -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = _execute(
            connection,
            "SELECT email, name, mobile, exam, category, state FROM students ORDER BY created_at DESC",
        ).fetchall()
    return [dict(row) for row in rows]


def _attempt_from_row(row: Any) -> dict:
    item = dict(row)
    item["answers"] = json.loads(item.pop("answers_json") or "{}")
    item["marked_for_review"] = json.loads(item.pop("marked_for_review_json") or "[]")
    item["submitted"] = item["submitted_at"] is not None
    item["updated_at"] = datetime.fromtimestamp(item["updated_at"]).strftime("%d %b %Y, %I:%M %p")
    return item


def create_or_resume_attempt(student_email: str, paper: dict) -> dict:
    initialize_database()
    normalized_email = student_email.strip().lower()
    with _connection() as connection:
        draft = _execute(
            connection,
            """
            SELECT * FROM test_attempts
            WHERE student_email = ? AND paper_id = ? AND submitted_at IS NULL
            ORDER BY updated_at DESC LIMIT 1
            """,
            (normalized_email, paper["paper_id"]),
        ).fetchone()
        if draft:
            return _attempt_from_row(draft)

        now = time.time()
        attempt_id = uuid.uuid4().hex
        _execute(
            connection,
            """
            INSERT INTO test_attempts (
                attempt_id, student_email, paper_id, exam, year, session,
                duration_seconds, started_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                normalized_email,
                paper["paper_id"],
                paper["exam"],
                int(paper["year"]),
                paper["session"],
                int(paper["duration_seconds"]),
                now,
                now,
            ),
        )
        row = _execute(connection, "SELECT * FROM test_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
    return _attempt_from_row(row)


def get_attempt(attempt_id: str, student_email: str) -> dict | None:
    initialize_database()
    with _connection() as connection:
        row = _execute(
            connection,
            "SELECT * FROM test_attempts WHERE attempt_id = ? AND student_email = ?",
            (attempt_id, student_email.strip().lower()),
        ).fetchone()
    return _attempt_from_row(row) if row else None


def save_attempt(attempt_id: str, student_email: str, answers: dict, marked_for_review: list[str]) -> bool:
    initialize_database()
    with _connection() as connection:
        cursor = _execute(
            connection,
            """
            UPDATE test_attempts
            SET answers_json = ?, marked_for_review_json = ?, updated_at = ?
            WHERE attempt_id = ? AND student_email = ? AND submitted_at IS NULL
            """,
            (
                json.dumps(answers, sort_keys=True),
                json.dumps(marked_for_review),
                time.time(),
                attempt_id,
                student_email.strip().lower(),
            ),
        )
    return cursor.rowcount == 1


def submit_attempt(attempt_id: str, student_email: str, answers: dict, marked_for_review: list[str]) -> bool:
    initialize_database()
    now = time.time()
    with _connection() as connection:
        cursor = _execute(
            connection,
            """
            UPDATE test_attempts
            SET answers_json = ?, marked_for_review_json = ?, submitted_at = ?, updated_at = ?
            WHERE attempt_id = ? AND student_email = ? AND submitted_at IS NULL
            """,
            (
                json.dumps(answers, sort_keys=True),
                json.dumps(marked_for_review),
                now,
                now,
                attempt_id,
                student_email.strip().lower(),
            ),
        )
    return cursor.rowcount == 1


def get_student_attempts(student_email: str, include_drafts: bool = True) -> list[dict]:
    initialize_database()
    query = "SELECT * FROM test_attempts WHERE student_email = ?"
    if not include_drafts:
        query += " AND submitted_at IS NOT NULL"
    query += " ORDER BY updated_at DESC"
    with _connection() as connection:
        rows = _execute(connection, query, (student_email.strip().lower(),)).fetchall()
    return [_attempt_from_row(row) for row in rows]


def get_latest_student_attempt(student_email: str) -> dict | None:
    attempts = get_student_attempts(student_email)
    submitted = [attempt for attempt in attempts if attempt["submitted"]]
    return submitted[0] if submitted else (attempts[0] if attempts else None)


def get_all_attempts() -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = _execute(connection, "SELECT * FROM test_attempts ORDER BY updated_at DESC").fetchall()
    return [_attempt_from_row(row) for row in rows]


def save_feedback(student_email: str, entry: dict) -> None:
    initialize_database()
    with _connection() as connection:
        _execute(
            connection,
            """
            INSERT INTO feedback (
                feedback_id, student_email, created_at, rating, difficulty,
                rank_useful, college_helpful, suggestions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                student_email.strip().lower(),
                time.time(),
                int(entry["rating"]),
                entry["difficulty"],
                entry["rank_useful"],
                entry["college_helpful"],
                entry.get("suggestions", "").strip(),
            ),
        )


def get_feedback() -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = _execute(connection, "SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    return [
        {
            "timestamp": datetime.fromtimestamp(row["created_at"]).strftime("%d %b %Y, %I:%M %p"),
            "student_email": row["student_email"],
            "rating": row["rating"],
            "difficulty": row["difficulty"],
            "rank_useful": row["rank_useful"],
            "college_helpful": row["college_helpful"],
            "suggestions": row["suggestions"],
        }
        for row in rows
    ]


def _new_share_code() -> str:
    # 48 random bits makes a private code impractical to guess while still
    # being short enough to type from a shared screen.
    return f"NEET-{uuid.uuid4().hex[:12].upper()}"


def create_challenge(student_email: str, paper_id: str) -> dict:
    """Create a two-student room. It has no synthetic participants or scores."""
    initialize_database()
    email = student_email.strip().lower()
    if not any(paper["paper_id"] == paper_id for paper in get_neet_papers()):
        raise ValueError("Choose a paper from the verified NEET catalogue.")

    for _ in range(3):
        challenge_id = uuid.uuid4().hex
        share_code = _new_share_code()
        now = time.time()
        try:
            with _connection() as connection:
                _execute(
                    connection,
                    """
                    INSERT INTO challenge_rooms (challenge_id, share_code, host_email, paper_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (challenge_id, share_code, email, paper_id, now),
                )
                _execute(
                    connection,
                    """
                    INSERT INTO challenge_members (challenge_id, student_email, joined_at)
                    VALUES (?, ?, ?)
                    """,
                    (challenge_id, email, now),
                )
        except INTEGRITY_ERRORS:
            continue
        return get_challenge(challenge_id, email) or {}

    raise RuntimeError("We could not create a private room. Please try again.")


def get_challenge_by_code(share_code: str, student_email: str | None = None) -> dict | None:
    initialize_database()
    normalized_code = share_code.strip().upper()
    with _connection() as connection:
        row = _execute(
            connection,
            "SELECT challenge_id FROM challenge_rooms WHERE share_code = ?",
            (normalized_code,),
        ).fetchone()
    if not row:
        return None
    return get_challenge(row["challenge_id"], student_email)


def _challenge_member_rows(connection: Any, challenge_id: str) -> list[dict]:
    rows = _execute(
        connection,
        """
        SELECT challenge_members.student_email, students.name, challenge_members.joined_at
        FROM challenge_members
        JOIN students ON students.email = challenge_members.student_email
        WHERE challenge_members.challenge_id = ?
        ORDER BY challenge_members.joined_at ASC
        """,
        (challenge_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_challenge(challenge_id: str, student_email: str | None = None) -> dict | None:
    initialize_database()
    with _connection() as connection:
        room = _execute(
            connection,
            "SELECT * FROM challenge_rooms WHERE challenge_id = ?",
            (challenge_id,),
        ).fetchone()
        if not room:
            return None
        item = dict(room)
        item["members"] = _challenge_member_rows(connection, challenge_id)
        item["member_count"] = len(item["members"])
        if student_email:
            item["joined"] = any(
                member["student_email"] == student_email.strip().lower() for member in item["members"]
            )
    return item


def join_challenge(share_code: str, student_email: str) -> dict:
    initialize_database()
    email = student_email.strip().lower()
    normalized_code = share_code.strip().upper()
    try:
        with _connection() as connection:
            room_query = "SELECT * FROM challenge_rooms WHERE share_code = ?"
            # PostgreSQL locks the room row until this transaction commits, so
            # two students cannot claim the last place at the same time.
            if using_managed_postgres():
                room_query += " FOR UPDATE"
            room = _execute(connection, room_query, (normalized_code,)).fetchone()
            if not room:
                raise ValueError("That challenge code was not found.")
            challenge_id = room["challenge_id"]
            existing = _execute(
                connection,
                """
                SELECT 1 FROM challenge_members
                WHERE challenge_id = ? AND student_email = ?
                """,
                (challenge_id, email),
            ).fetchone()
            if not existing:
                member_count = _execute(
                    connection,
                    "SELECT COUNT(*) AS member_count FROM challenge_members WHERE challenge_id = ?",
                    (challenge_id,),
                ).fetchone()["member_count"]
                if member_count >= 2:
                    raise ValueError("This challenge already has two students.")
                _execute(
                    connection,
                    """
                    INSERT INTO challenge_members (challenge_id, student_email, joined_at)
                    VALUES (?, ?, ?)
                    """,
                    (challenge_id, email, time.time()),
                )
    except INTEGRITY_ERRORS as error:
        raise ValueError("This challenge already has two students.") from error
    return get_challenge(challenge_id, email) or {}


def get_student_challenges(student_email: str) -> list[dict]:
    initialize_database()
    email = student_email.strip().lower()
    with _connection() as connection:
        rooms = _execute(
            connection,
            """
            SELECT challenge_rooms.challenge_id
            FROM challenge_rooms
            JOIN challenge_members ON challenge_members.challenge_id = challenge_rooms.challenge_id
            WHERE challenge_members.student_email = ?
            ORDER BY challenge_rooms.created_at DESC
            """,
            (email,),
        ).fetchall()
    return [get_challenge(row["challenge_id"], email) for row in rooms]


def record_challenge_attempt(challenge_id: str, student_email: str, attempt_id: str) -> bool:
    initialize_database()
    email = student_email.strip().lower()
    room = get_challenge(challenge_id, email)
    if not room or not room.get("joined"):
        return False
    with _connection() as connection:
        _execute(
            connection,
            """
            INSERT INTO challenge_attempts (challenge_id, student_email, attempt_id)
            VALUES (?, ?, ?)
            ON CONFLICT (challenge_id, student_email) DO UPDATE SET attempt_id = excluded.attempt_id
            """,
            (challenge_id, email, attempt_id),
        )
    return True


def get_challenge_attempts(challenge_id: str) -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = _execute(
            connection,
            """
            SELECT challenge_members.student_email, students.name, test_attempts.*
            FROM challenge_members
            JOIN students ON students.email = challenge_members.student_email
            LEFT JOIN challenge_attempts
                ON challenge_attempts.challenge_id = challenge_members.challenge_id
                AND challenge_attempts.student_email = challenge_members.student_email
            LEFT JOIN test_attempts ON test_attempts.attempt_id = challenge_attempts.attempt_id
            WHERE challenge_members.challenge_id = ?
            ORDER BY challenge_members.joined_at ASC
            """,
            (challenge_id,),
        ).fetchall()

    attempts = []
    for row in rows:
        item = dict(row)
        if item.get("attempt_id"):
            item = _attempt_from_row(item)
        else:
            item["submitted"] = False
        attempts.append(item)
    return attempts
