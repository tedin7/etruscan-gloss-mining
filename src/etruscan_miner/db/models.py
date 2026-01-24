"""Data models for Etruscan gloss mining."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Author:
    """Ancient author who wrote about Etruscan."""

    id: Optional[int] = None
    name: str = ""
    latin_name: Optional[str] = None
    dates: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Work:
    """A work by an ancient author."""

    id: Optional[int] = None
    author_id: int = 0
    title: str = ""
    latin_title: Optional[str] = None
    urn: Optional[str] = None
    date_composed: Optional[str] = None
    description: Optional[str] = None
    priority: str = "MEDIUM"
    created_at: Optional[datetime] = None


@dataclass
class Passage:
    """A text passage from a work."""

    id: Optional[int] = None
    work_id: int = 0
    reference: Optional[str] = None
    text_latin: Optional[str] = None
    text_normalized: Optional[str] = None
    source_url: Optional[str] = None
    mined_at: Optional[datetime] = None


@dataclass
class EtruscanWord:
    """Known Etruscan vocabulary word."""

    id: Optional[int] = None
    word: str = ""
    word_normalized: str = ""
    meaning: Optional[str] = None
    meaning_uncertain: bool = False
    category: str = "basic"  # basic, non-basic, morpheme, loanword
    source: Optional[str] = None
    reliability: int = 3
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Pattern:
    """Regex pattern for gloss detection."""

    id: Optional[int] = None
    name: str = ""
    regex: str = ""
    language: str = "latin"
    description: Optional[str] = None
    base_confidence: float = 0.8
    active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class MiningRun:
    """Audit trail for a mining operation."""

    id: Optional[int] = None
    work_id: Optional[int] = None
    pattern_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    passages_scanned: int = 0
    candidates_found: int = 0
    status: str = "running"
    error_message: Optional[str] = None


@dataclass
class Candidate:
    """A candidate gloss found by mining."""

    id: Optional[int] = None
    passage_id: Optional[int] = None
    mining_run_id: Optional[int] = None
    pattern_id: Optional[int] = None
    etruscan_word: str = ""
    etruscan_normalized: str = ""
    meaning_proposed: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    full_match: Optional[str] = None
    pattern_confidence: Optional[float] = None
    overall_score: Optional[float] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None


@dataclass
class Validation:
    """Validation score for a candidate."""

    id: Optional[int] = None
    candidate_id: int = 0
    validation_type: str = ""  # pattern, cross_reference, linguistic, context, llm
    score: float = 0.0
    weight: float = 0.0
    details: Optional[str] = None  # JSON string
    created_at: Optional[datetime] = None


@dataclass
class VerifiedGloss:
    """A verified Etruscan gloss."""

    id: Optional[int] = None
    etruscan_word: str = ""
    etruscan_normalized: str = ""
    meaning: str = ""
    source_author: Optional[str] = None
    source_work: Optional[str] = None
    source_citation: Optional[str] = None
    source_quote: Optional[str] = None
    reliability: int = 3
    notes: Optional[str] = None
    candidate_id: Optional[int] = None
    is_seed: bool = False
    created_at: Optional[datetime] = None
