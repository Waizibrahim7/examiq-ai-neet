"""SQLite persistence for the NEET pilot.

The tables keep user data separate by student email. SQLite with WAL is suitable
for local development and a controlled pilot; production deployment should use
a managed PostgreSQL database before running high-concurrency examinations.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path

from neet_catalog import get_neet_papers


BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "database.db"


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database() -> None:
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
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
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                exam TEXT NOT NULL,
                category TEXT NOT NULL,
                state TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_attempts (
                attempt_id TEXT PRIMARY KEY,
                student_email TEXT NOT NULL,
                paper_id TEXT NOT NULL,
                exam TEXT NOT NULL,
                year INTEGER NOT NULL,
                session TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                started_at REAL NOT NULL,
                submitted_at REAL,
                answers_json TEXT NOT NULL DEFAULT '{}',
                marked_for_review_json TEXT NOT NULL DEFAULT '[]',
                updated_at REAL NOT NULL,
                FOREIGN KEY (student_email) REFERENCES students(email)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_test_attempts_student_time
            ON test_attempts(student_email, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                student_email TEXT NOT NULL,
                created_at REAL NOT NULL,
                rating INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                rank_useful TEXT NOT NULL,
                college_helpful TEXT NOT NULL,
                suggestions TEXT NOT NULL,
                FOREIGN KEY (student_email) REFERENCES students(email)
            )
            """
        )

        connection.executemany(
            """
            INSERT OR REPLACE INTO papers (
                paper_id, exam, year, session, subject, questions, answer_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
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
    """Compatibility helper for future admin imports."""
    initialize_database()
    with _connection() as connection:
        connection.executemany(
            """
            INSERT OR REPLACE INTO papers (
                paper_id, exam, year, session, subject, questions, answer_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
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
        rows = connection.execute(query, parameters).fetchall()
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
            connection.execute(
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
    except sqlite3.IntegrityError as error:
        raise ValueError("An account with this email already exists. Please log in instead.") from error
    return record


def get_student(email: str, include_password_hash: bool = False) -> dict | None:
    initialize_database()
    columns = "email, name, mobile, exam, category, state"
    if include_password_hash:
        columns += ", password_hash"

    with _connection() as connection:
        row = connection.execute(
            f"SELECT {columns} FROM students WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def get_students() -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = connection.execute(
            "SELECT email, name, mobile, exam, category, state FROM students ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def _attempt_from_row(row: sqlite3.Row) -> dict:
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
        draft = connection.execute(
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
        connection.execute(
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
        row = connection.execute("SELECT * FROM test_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
    return _attempt_from_row(row)


def get_attempt(attempt_id: str, student_email: str) -> dict | None:
    initialize_database()
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM test_attempts WHERE attempt_id = ? AND student_email = ?",
            (attempt_id, student_email.strip().lower()),
        ).fetchone()
    return _attempt_from_row(row) if row else None


def save_attempt(attempt_id: str, student_email: str, answers: dict, marked_for_review: list[str]) -> bool:
    initialize_database()
    with _connection() as connection:
        cursor = connection.execute(
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
        cursor = connection.execute(
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
        rows = connection.execute(query, (student_email.strip().lower(),)).fetchall()
    return [_attempt_from_row(row) for row in rows]


def get_latest_student_attempt(student_email: str) -> dict | None:
    attempts = get_student_attempts(student_email)
    submitted = [attempt for attempt in attempts if attempt["submitted"]]
    return submitted[0] if submitted else (attempts[0] if attempts else None)


def get_all_attempts() -> list[dict]:
    initialize_database()
    with _connection() as connection:
        rows = connection.execute("SELECT * FROM test_attempts ORDER BY updated_at DESC").fetchall()
    return [_attempt_from_row(row) for row in rows]


def save_feedback(student_email: str, entry: dict) -> None:
    initialize_database()
    with _connection() as connection:
        connection.execute(
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
        rows = connection.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
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
