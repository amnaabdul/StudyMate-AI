import sqlite3
import json
from contextlib import closing
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).resolve().parent.parent / "studymate.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_database():
    with closing(get_connection()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_progress (
                pdf_id TEXT NOT NULL,
                card_question TEXT NOT NULL,
                learned INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (pdf_id, card_question)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_decks (
                pdf_id TEXT PRIMARY KEY,
                cards_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def save_quiz_attempt(pdf_name, score, total_questions):
    if total_questions <= 0:
        raise ValueError("Total questions must be positive.")
    if not 0 <= score <= total_questions:
        raise ValueError("Score must be between zero and total questions.")

    percentage = round(score / total_questions * 100, 2)

    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            INSERT INTO quiz_attempts (
                pdf_name,
                score,
                total_questions,
                percentage,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pdf_name,
                score,
                total_questions,
                percentage,
                datetime.now().isoformat(timespec="seconds")
            )
        )


def get_quiz_attempts(pdf_name=None):
    with closing(get_connection()) as conn, conn:
        conn.row_factory = sqlite3.Row

        if pdf_name is None:
            rows = conn.execute(
                """
                SELECT *
                FROM quiz_attempts
                ORDER BY id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM quiz_attempts
                WHERE pdf_name = ?
                ORDER BY id ASC
                """,
                (pdf_name,)
            ).fetchall()

    return [dict(row) for row in rows]


def save_flashcard_progress(pdf_id, card_question, learned):
    """Save or update whether a flashcard is learned."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            INSERT INTO flashcard_progress (
                pdf_id, card_question, learned, updated_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pdf_id, card_question)
            DO UPDATE SET
                learned = excluded.learned,
                updated_at = excluded.updated_at
            """,
            (
                pdf_id,
                card_question,
                int(learned),
                datetime.now().isoformat(timespec="seconds")
            )
        )


def get_learned_flashcards(pdf_id):
    """Return the questions marked as learned for this PDF."""
    with closing(get_connection()) as conn, conn:
        rows = conn.execute(
            """
            SELECT card_question
            FROM flashcard_progress
            WHERE pdf_id = ? AND learned = 1
            """,
            (pdf_id,)
        ).fetchall()

    return {row[0] for row in rows}

def save_flashcards(pdf_id, flashcards):
    """Atomically replace a PDF deck, preserving question-based progress."""
    if not isinstance(flashcards, list) or not flashcards:
        raise ValueError("A deck must contain flashcards.")
    questions = set()
    for card in flashcards:
        if not isinstance(card, dict) or any(
            not isinstance(card.get(key), str) or not card[key].strip()
            for key in ("question", "answer")
        ):
            raise ValueError("Each flashcard needs a question and answer.")
        if card["question"] in questions:
            raise ValueError("Flashcard questions must be unique.")
        questions.add(card["question"])
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """INSERT INTO flashcard_decks (pdf_id, cards_json, updated_at)
               VALUES (?, ?, ?) ON CONFLICT(pdf_id) DO UPDATE SET
               cards_json = excluded.cards_json, updated_at = excluded.updated_at""",
            (pdf_id, json.dumps(flashcards, ensure_ascii=False),
             datetime.now().isoformat(timespec="seconds")),
        )


def get_saved_flashcards(pdf_id):
    """Load the most recently saved deck for this PDF without calling Ollama."""
    with closing(get_connection()) as conn, conn:
        row = conn.execute(
            "SELECT cards_json FROM flashcard_decks WHERE pdf_id = ?", (pdf_id,)
        ).fetchone()
    return json.loads(row[0]) if row else []
