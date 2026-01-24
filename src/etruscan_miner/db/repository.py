"""Repository for database CRUD operations."""

import sqlite3
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from .models import (
    Author,
    Candidate,
    EtruscanWord,
    MiningRun,
    Passage,
    Pattern,
    Validation,
    VerifiedGloss,
    Work,
)


def normalize_word(word: str) -> str:
    """Normalize a word for comparison: lowercase, remove diacritics."""
    # Decompose unicode characters and remove diacritics
    normalized = unicodedata.normalize("NFD", word.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


class Repository:
    """Database repository for Etruscan gloss mining."""

    def __init__(self, db_path: Path):
        """Initialize repository with database path."""
        self.db_path = db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Author operations
    def insert_author(self, author: Author) -> int:
        """Insert an author and return the ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO authors (name, latin_name, dates, description)
                   VALUES (?, ?, ?, ?)""",
                (author.name, author.latin_name, author.dates, author.description),
            )
            if cursor.lastrowid:
                return cursor.lastrowid
            # Get existing
            row = conn.execute(
                "SELECT id FROM authors WHERE name = ?", (author.name,)
            ).fetchone()
            return row["id"]

    def get_author_by_name(self, name: str) -> Optional[Author]:
        """Get an author by name."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM authors WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return Author(**dict(row))
            return None

    # Work operations
    def insert_work(self, work: Work) -> int:
        """Insert a work and return the ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO works
                   (author_id, title, latin_title, urn, date_composed, description, priority)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    work.author_id,
                    work.title,
                    work.latin_title,
                    work.urn,
                    work.date_composed,
                    work.description,
                    work.priority,
                ),
            )
            if cursor.lastrowid:
                return cursor.lastrowid
            row = conn.execute(
                "SELECT id FROM works WHERE author_id = ? AND title = ?",
                (work.author_id, work.title),
            ).fetchone()
            return row["id"]

    # Passage operations
    def insert_passage(self, passage: Passage) -> int:
        """Insert a passage and return the ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO passages
                   (work_id, reference, text_latin, text_normalized, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    passage.work_id,
                    passage.reference,
                    passage.text_latin,
                    passage.text_normalized,
                    passage.source_url,
                ),
            )
            return cursor.lastrowid

    # Vocabulary operations
    def insert_vocabulary(self, word: EtruscanWord) -> int:
        """Insert an Etruscan vocabulary word."""
        word.word_normalized = normalize_word(word.word)
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO etruscan_vocabulary
                   (word, word_normalized, meaning, meaning_uncertain, category, source, reliability, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    word.word,
                    word.word_normalized,
                    word.meaning,
                    word.meaning_uncertain,
                    word.category,
                    word.source,
                    word.reliability,
                    word.notes,
                ),
            )
            return cursor.lastrowid

    def find_vocabulary(self, word: str) -> list[EtruscanWord]:
        """Find vocabulary words matching a search term."""
        normalized = normalize_word(word)
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM etruscan_vocabulary
                   WHERE word_normalized = ? OR word_normalized LIKE ?""",
                (normalized, f"%{normalized}%"),
            ).fetchall()
            return [EtruscanWord(**dict(row)) for row in rows]

    def get_all_vocabulary(self) -> list[EtruscanWord]:
        """Get all vocabulary words."""
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM etruscan_vocabulary").fetchall()
            return [EtruscanWord(**dict(row)) for row in rows]

    # Pattern operations
    def get_active_patterns(self) -> list[Pattern]:
        """Get all active patterns."""
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM patterns WHERE active = 1"
            ).fetchall()
            return [Pattern(**dict(row)) for row in rows]

    def get_pattern_by_name(self, name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM patterns WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return Pattern(**dict(row))
            return None

    # Mining run operations
    def start_mining_run(self, work_id: Optional[int], pattern_id: Optional[int]) -> int:
        """Start a new mining run and return the ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO mining_runs (work_id, pattern_id, status)
                   VALUES (?, ?, 'running')""",
                (work_id, pattern_id),
            )
            return cursor.lastrowid

    def complete_mining_run(
        self, run_id: int, passages_scanned: int, candidates_found: int, error: Optional[str] = None
    ):
        """Complete a mining run."""
        status = "failed" if error else "completed"
        with self.connection() as conn:
            conn.execute(
                """UPDATE mining_runs
                   SET completed_at = CURRENT_TIMESTAMP,
                       passages_scanned = ?,
                       candidates_found = ?,
                       status = ?,
                       error_message = ?
                   WHERE id = ?""",
                (passages_scanned, candidates_found, status, error, run_id),
            )

    # Candidate operations
    def insert_candidate(self, candidate: Candidate) -> int:
        """Insert a candidate gloss."""
        candidate.etruscan_normalized = normalize_word(candidate.etruscan_word)
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO candidates
                   (passage_id, mining_run_id, pattern_id, etruscan_word, etruscan_normalized,
                    meaning_proposed, context_before, context_after, full_match,
                    pattern_confidence, overall_score, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    candidate.passage_id,
                    candidate.mining_run_id,
                    candidate.pattern_id,
                    candidate.etruscan_word,
                    candidate.etruscan_normalized,
                    candidate.meaning_proposed,
                    candidate.context_before,
                    candidate.context_after,
                    candidate.full_match,
                    candidate.pattern_confidence,
                    candidate.overall_score,
                    candidate.status,
                ),
            )
            return cursor.lastrowid

    def get_candidates_by_status(self, status: str) -> list[Candidate]:
        """Get candidates by status."""
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates WHERE status = ?", (status,)
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]

    def update_candidate_status(self, candidate_id: int, status: str, notes: Optional[str] = None):
        """Update candidate status."""
        with self.connection() as conn:
            conn.execute(
                """UPDATE candidates
                   SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewer_notes = ?
                   WHERE id = ?""",
                (status, notes, candidate_id),
            )

    # Validation operations
    def insert_validation(self, validation: Validation) -> int:
        """Insert a validation record."""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO validations
                   (candidate_id, validation_type, score, weight, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    validation.candidate_id,
                    validation.validation_type,
                    validation.score,
                    validation.weight,
                    validation.details,
                ),
            )
            return cursor.lastrowid

    def get_validations_for_candidate(self, candidate_id: int) -> list[Validation]:
        """Get all validations for a candidate."""
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM validations WHERE candidate_id = ?", (candidate_id,)
            ).fetchall()
            return [Validation(**dict(row)) for row in rows]

    # Verified gloss operations
    def insert_verified_gloss(self, gloss: VerifiedGloss) -> int:
        """Insert a verified gloss."""
        gloss.etruscan_normalized = normalize_word(gloss.etruscan_word)
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO verified_glosses
                   (etruscan_word, etruscan_normalized, meaning, source_author, source_work,
                    source_citation, source_quote, reliability, notes, candidate_id, is_seed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    gloss.etruscan_word,
                    gloss.etruscan_normalized,
                    gloss.meaning,
                    gloss.source_author,
                    gloss.source_work,
                    gloss.source_citation,
                    gloss.source_quote,
                    gloss.reliability,
                    gloss.notes,
                    gloss.candidate_id,
                    gloss.is_seed,
                ),
            )
            return cursor.lastrowid

    def get_all_verified_glosses(self) -> list[VerifiedGloss]:
        """Get all verified glosses."""
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM verified_glosses").fetchall()
            return [VerifiedGloss(**dict(row)) for row in rows]

    def find_verified_gloss(self, word: str) -> Optional[VerifiedGloss]:
        """Find a verified gloss by word."""
        normalized = normalize_word(word)
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM verified_glosses WHERE etruscan_normalized = ?",
                (normalized,),
            ).fetchone()
            if row:
                return VerifiedGloss(**dict(row))
            return None

    # Statistics
    def get_stats(self) -> dict:
        """Get database statistics."""
        with self.connection() as conn:
            stats = {}
            for table in [
                "authors",
                "works",
                "passages",
                "etruscan_vocabulary",
                "patterns",
                "candidates",
                "verified_glosses",
            ]:
                row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                stats[table] = row["count"]
            return stats
