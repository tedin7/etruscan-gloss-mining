-- Etruscan Gloss Mining Database Schema
-- SQLite

PRAGMA foreign_keys = ON;

-- Authors table: Ancient authors who wrote about Etruscan
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    latin_name TEXT,
    dates TEXT,  -- e.g., "116-27 BCE"
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Works table: Specific works by authors
CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    latin_title TEXT,
    urn TEXT,  -- Perseus CTS URN
    date_composed TEXT,
    description TEXT,
    priority TEXT CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(id),
    UNIQUE(author_id, title)
);

-- Passages table: Text passages from works
CREATE TABLE IF NOT EXISTS passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    reference TEXT,  -- e.g., "Book 5, Chapter 10"
    text_latin TEXT,
    text_normalized TEXT,  -- Lowercased, cleaned
    source_url TEXT,
    mined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(id)
);

-- Etruscan vocabulary table: Known Etruscan words for cross-reference
CREATE TABLE IF NOT EXISTS etruscan_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    word_normalized TEXT NOT NULL,  -- Lowercase, no diacritics
    meaning TEXT,
    meaning_uncertain BOOLEAN DEFAULT FALSE,
    category TEXT,  -- 'basic', 'non-basic', 'morpheme', 'loanword'
    source TEXT,  -- Where this came from (Forni, Bonfante, etc.)
    reliability INTEGER CHECK (reliability BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, category)
);

-- Patterns table: Regex patterns for gloss detection
CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    regex TEXT NOT NULL,
    language TEXT CHECK (language IN ('latin', 'greek')),
    description TEXT,
    base_confidence REAL CHECK (base_confidence BETWEEN 0 AND 1),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining runs table: Audit trail of mining operations
CREATE TABLE IF NOT EXISTS mining_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER,
    pattern_id INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    passages_scanned INTEGER DEFAULT 0,
    candidates_found INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (pattern_id) REFERENCES patterns(id)
);

-- Candidates table: Candidate glosses found by mining
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id INTEGER,
    mining_run_id INTEGER,
    pattern_id INTEGER,
    etruscan_word TEXT NOT NULL,
    etruscan_normalized TEXT NOT NULL,
    meaning_proposed TEXT,
    context_before TEXT,
    context_after TEXT,
    full_match TEXT,  -- The full regex match
    pattern_confidence REAL,
    overall_score REAL,
    status TEXT CHECK (status IN ('pending', 'reviewing', 'accepted', 'rejected')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewer_notes TEXT,
    FOREIGN KEY (passage_id) REFERENCES passages(id),
    FOREIGN KEY (mining_run_id) REFERENCES mining_runs(id),
    FOREIGN KEY (pattern_id) REFERENCES patterns(id)
);

-- Validations table: Validation scores for candidates
CREATE TABLE IF NOT EXISTS validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    validation_type TEXT NOT NULL,  -- 'pattern', 'cross_reference', 'linguistic', 'context', 'llm'
    score REAL CHECK (score BETWEEN 0 AND 1),
    weight REAL,
    details TEXT,  -- JSON with validation details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    UNIQUE(candidate_id, validation_type)
);

-- Verified glosses table: Final verified glosses
CREATE TABLE IF NOT EXISTS verified_glosses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etruscan_word TEXT NOT NULL,
    etruscan_normalized TEXT NOT NULL,
    meaning TEXT NOT NULL,
    source_author TEXT,
    source_work TEXT,
    source_citation TEXT,  -- e.g., "Vita Divi Augusti 97"
    source_quote TEXT,  -- Original Latin/Greek quote
    reliability INTEGER CHECK (reliability BETWEEN 1 AND 5),
    notes TEXT,
    candidate_id INTEGER,  -- Link to original candidate if from mining
    is_seed BOOLEAN DEFAULT FALSE,  -- TRUE if from initial seed data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_passages_work ON passages(work_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_passage ON candidates(passage_id);
CREATE INDEX IF NOT EXISTS idx_vocab_word ON etruscan_vocabulary(word_normalized);
CREATE INDEX IF NOT EXISTS idx_verified_word ON verified_glosses(etruscan_normalized);
CREATE INDEX IF NOT EXISTS idx_validations_candidate ON validations(candidate_id);

-- Insert default patterns
INSERT OR IGNORE INTO patterns (name, regex, language, description, base_confidence) VALUES
    ('tusci_vocant', '[Tt]usci?\s+voca(?:n)?t\s+(\w+)', 'latin', 'Pattern: Tusci vocant X (The Etruscans call X)', 0.90),
    ('lingua_etrusca', '[Ee]trusca\s+lingua\s+(\w+)', 'latin', 'Pattern: Etrusca lingua X (In Etruscan language X)', 0.90),
    ('apud_etruscos', 'apud\s+[Ee]truscos\s+(\w+)', 'latin', 'Pattern: apud Etruscos X (Among the Etruscans X)', 0.85),
    ('etrusco_vocabulo', '[Ee]trusco\s+vocabulo\s+(\w+)', 'latin', 'Pattern: Etrusco vocabulo X (With Etruscan word X)', 0.90),
    ('quod_etrusci', 'quod\s+[Ee]trusci\s+(\w+)', 'latin', 'Pattern: quod Etrusci X (Which the Etruscans X)', 0.85),
    ('etrusca_origine', '(\w+)\s+[Ee]trusca\s+origin', 'latin', 'Pattern: X Etrusca origine (X of Etruscan origin)', 0.70),
    ('tyrrheni_vocant', '[Tt]yrrhen[io]s?\s+voca(?:n)?t\s+(\w+)', 'latin', 'Pattern: Tyrrheni vocant X (Tyrrhenians call X)', 0.85),
    ('tusco_nomine', '[Tt]usco\s+nomine\s+(\w+)', 'latin', 'Pattern: Tusco nomine X (With Tuscan name X)', 0.85);
