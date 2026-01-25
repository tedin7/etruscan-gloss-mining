# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NLP pipeline for mining Etruscan glosses from ancient Latin and Greek texts. The system uses regex pattern matching to find phrases like "Tusci vocant X" (The Etruscans call X) in classical texts, then validates candidates against known Etruscan vocabulary and phonotactic rules.

## Commands

```bash
# Setup database (creates SQLite at data/etruscan_glosses.db)
python scripts/setup_database.py

# Import seed data from markdown files
python scripts/import_seeds.py

# Run tests
python -m pytest tests/ -v

# Run single test
python -m pytest tests/test_patterns.py::TestGlossExtractor::test_extract_tusci_vocant -v

# Test pattern extraction on text
python scripts/mine_glosses.py --text "Tusci vocant subulo quod nos tibicinem"

# Validate a word against Etruscan phonotactics
python scripts/validate_candidates.py --word "aisar"

# Export results
python scripts/export_results.py --format markdown --type report -o results/findings.md
```

## Architecture

### Data Flow
```
Markdown seed files → import_seeds.py → SQLite DB
                                            ↓
Perseus API → text_cache.py → mine_glosses.py → candidates table
                                                      ↓
                              validate_candidates.py → scored/accepted
                                                      ↓
                              export_results.py → MD/CSV/JSON
```

### Core Modules (src/etruscan_miner/)

- **patterns/**: Regex patterns for gloss detection
  - `latin_patterns.py`: 30+ patterns like `tusci_vocant`, `etrusca_lingua`
  - `extractor.py`: `GlossExtractor` class applies patterns, extracts context

- **validation/**: Multi-factor scoring pipeline
  - `cross_reference.py`: Matches against known vocabulary (exact/root/similar)
  - `linguistic.py`: Etruscan phonotactic rules (no voiced stops b/d/g, typical endings)
  - `scorer.py`: Combines pattern confidence (30%), cross-ref (30%), linguistic (20%), context (20%)

- **db/**: SQLite persistence
  - `schema.sql`: 10 tables (authors, works, passages, candidates, verified_glosses, etc.)
  - `repository.py`: CRUD operations, all queries go through `Repository` class

- **corpus/**: Text acquisition
  - `perseus.py`: CTS API client with rate limiting
  - `text_cache.py`: Local caching to avoid repeated API calls

### Key Data Files
- `ANCIENT_GLOSSES_VERIFIED.md`: 43+ glosses with ancient source citations
- `CONSENSUS_GLOSSES_FORNI.md`: Academic consensus vocabulary (Forni et al.)
- `data/etruscan_glosses.db`: SQLite database (not in git)

### Validation Thresholds
- HIGH confidence: ≥0.85 → auto-accept
- MEDIUM confidence: 0.65-0.84 → needs review
- LOW confidence: <0.65 → reject

## Testing

Tests use fixtures in `tests/fixtures/sample_passages.json` containing known glosses and negative examples. Pattern tests verify >70% recall on documented glosses.

## Claude Teacher Mode

For every project, write a detailed FOR[yourname].md file that explains the whole project in plain language.

Explain the technical architecture, the structure of the codebase and how the various parts are connected, the technologies used, why we made these technical decisions, and lessons I can learn from it (this should include the bugs we ran into and how we fixed them, potential pitfalls and how to avoid them in the future, new technologies used, how good engineers think and work, best practices, etc).

It should be very engaging to read; don't make it sound like boring technical documentation/textbook. Where appropriate, use analogies and anecdotes to make it more understandable and memorable.
