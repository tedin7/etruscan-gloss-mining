# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NLP pipeline for mining Etruscan glosses from ancient Latin and Greek texts. The system uses regex pattern matching to find phrases like "Tusci vocant X" (The Etruscans call X) in classical texts, then validates candidates against known Etruscan vocabulary and phonotactic rules.

## Commands

### Unified CLI (Recommended)

```bash
# Install the package
pip install -e .

# Main entry point
etruscan --help

# Database operations
etruscan db setup                    # Create database
etruscan db stats                    # Show statistics
etruscan db import-seeds             # Import seed data
etruscan db reset                    # Reset database

# Corpus management
etruscan corpus download --all       # Download from all sources
etruscan corpus download --source latin_library
etruscan corpus download --source perseus
etruscan corpus download --source greek
etruscan corpus stats                # Show corpus statistics
etruscan corpus import-inscriptions  # Import inscription vocabulary

# Find candidates (replaces mine + discover)
etruscan find --text "Tusci vocant subulo quod nos tibicinem"
etruscan find --corpus latin_library
etruscan find --corpus all
etruscan find --corpus greek --greek-work dionysius_ant_rom
etruscan find --corpus all --advanced     # Enable advanced discovery methods
etruscan find --show pending              # Show pending candidates

# Analyze candidates (replaces validate + verify)
etruscan analyze --word harena            # Analyze single word with all 9 methods
etruscan analyze --status pending         # Analyze pending candidates
etruscan analyze --use-ml                 # Enable ML-based classifiers
etruscan analyze --methods-required 2     # Require 2+ methods to confirm
etruscan analyze --report                 # Generate comprehensive report
etruscan analyze --show-accepted          # Show accepted candidates

# ML model training
etruscan train word-classifier --test --importance
etruscan train context-classifier --test

# Export
etruscan export --format markdown -o findings.md
etruscan export --format json --type candidates
etruscan export --format csv --type all
```

### Legacy Scripts (for backwards compatibility)

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

# Download corpus texts (all sources)
python scripts/download_all_texts.py --all

# Download high-priority texts only (Isidore, Varro, Festus, Solinus)
python scripts/download_all_texts.py --latin-library --priority high

# Download from specific source
python scripts/download_all_texts.py --latin-library  # Latin Library HTML
python scripts/download_all_texts.py --perseus        # Perseus CTS API (Latin)
python scripts/download_all_texts.py --greek          # Perseus CTS API (Greek)
python scripts/download_all_texts.py --github         # Clone CLTK repos

# Download Greek texts with Etruscan references
python scripts/download_all_texts.py --greek --priority high  # Dionysius, Strabo

# Show corpus download statistics
python scripts/download_all_texts.py --stats

# Import inscription vocabulary from Zenodo/CIEW corpus
python scripts/import_inscriptions.py              # Import 10,000+ words
python scripts/import_inscriptions.py --stats      # Show statistics
python scripts/import_inscriptions.py --dry-run    # Preview without importing

# Download and import Hesychius lexicon glosses
python scripts/download_hesychius.py --list        # List known glosses
python scripts/download_hesychius.py --download --import-db  # Full import

# Mine Greek texts for Etruscan references
python scripts/mine_glosses.py --corpus greek      # Mine all Greek works
python scripts/mine_glosses.py --corpus greek --greek-work dionysius_ant_rom  # Specific work

# Test Greek pattern matching
python scripts/mine_glosses.py --text "Τυρρηνοί καλοῦσι λάρνα"

# Train word classifier (Layer 2 ML model)
python scripts/train_word_classifier.py --test --importance

# Train context classifier (Layer 3 ML model)
python scripts/train_context_classifier.py --test

# Use word classifier
python -c "from etruscan_miner.validation import WordClassifier; wc = WordClassifier.load(); print(wc.predict('ais'))"

# === NEW DISCOVERY PIPELINE ===

# Run full discovery on single text
python scripts/discover_new_words.py --text "Tusci vocant subulo quod nos tibicinem"

# Run discovery on corpus (Latin Library)
python scripts/run_full_discovery.py --sources latin_library --min-confidence 0.60

# Run on all sources
python scripts/run_full_discovery.py --sources latin_library,perseus,greek

# Export discovery results
python scripts/run_full_discovery.py --output results/discoveries.json

# Test cross-linguistic modules
python -c "from etruscan_miner.linguistics import LemnianAnalyzer; la = LemnianAnalyzer(); print(len(la.get_high_confidence_parallels()), 'Lemnian parallels')"
```

## Architecture

### Data Flow
```
                         etruscan CLI
                              ↓
Markdown seed files → etruscan db import-seeds → SQLite DB
                                                       ↓
Perseus API → etruscan corpus download → text_cache → etruscan find → candidates table
                                                                            ↓
                                        etruscan analyze (9 methods) → scored/accepted
                                                                            ↓
                                                      etruscan export → MD/CSV/JSON
```

Alternative (legacy scripts):
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

- **cli/**: Unified command-line interface
  - `__init__.py`: Main CLI router with Click groups
  - `commands/db.py`: Database operations (setup, stats, reset, import-seeds)
  - `commands/corpus.py`: Corpus download and management
  - `commands/find.py`: Find candidates with pattern matching + advanced discovery
  - `commands/analyze.py`: Analyze candidates with unified 9-method scoring
  - `commands/train.py`: ML model training
  - `commands/export.py`: Results export
  - `utils.py`: Shared CLI utilities

- **patterns/**: Regex patterns for gloss detection
  - `latin_patterns.py`: 30+ patterns like `tusci_vocant`, `etrusca_lingua`
  - `extractor.py`: `GlossExtractor` class applies patterns, extracts context

- **validation/**: Multi-factor scoring pipeline (9 methods)
  - `unified.py`: Unified 9-method validator (pattern, cross-ref, linguistic, phonotactic, context, inscription, semantic, lemnian, raetic)
  - `cross_reference.py`: Matches against known vocabulary (exact/root/similar)
  - `linguistic.py`: Etruscan phonotactic rules (no voiced stops b/d/g, typical endings)
  - `dependency_filter.py`: Layer 1 - spaCy dependency parsing for Etruscan attribution
  - `word_classifier.py`: Layer 2 - Character n-gram ML classifier for Etruscan-like words
  - `context_classifier.py`: Layer 3 - Context classifier (TF-IDF/embeddings/DistilBERT)
  - `scorer.py`: Legacy 4-factor scorer (pattern, cross-ref, linguistic, context)

- **db/**: SQLite persistence
  - `schema.sql`: 10 tables (authors, works, passages, candidates, verified_glosses, etc.)
  - `repository.py`: CRUD operations, all queries go through `Repository` class

- **corpus/**: Text acquisition from multiple sources
  - `perseus.py`: CTS API client (Pliny NH, Livy, Virgil available; Varro/Festus NOT in inventory)
  - `latin_library.py`: HTML scraper for thelatinlibrary.com (100+ texts including Isidore, Livy, Suetonius)
  - `greek_texts.py`: Greek texts from Perseus (Dionysius, Strabo, Herodotus)
  - `inscriptions.py`: CIEW corpus loader (10,000+ Etruscan words from inscriptions)
  - `hesychius.py`: Hesychius lexicon parser for Tyrrhenian glosses
  - `text_cache.py`: Local caching to avoid repeated API calls
  - `medieval_glossaries.py`: Medieval Latin glossaries (Isidore, Placidus, CGL)
  - `byzantine.py`: Byzantine encyclopedias (Suda, Etymologicum Magnum)
  - `papyri.py`: Papyri.info integration for Greek documentary papyri
  - `archaeological.py`: Archaeological inscription databases (EAGLE, TLE)

- **linguistics/**: Cross-linguistic analysis for Etruscan discovery
  - `lemnian.py`: Lemnian corpus (~40 words from Kaminia stele, only known Etruscan relative)
  - `raetic.py`: Raetic inscriptions (~200 texts from Alpine region)
  - `loanword_detector.py`: Latin words with suspected Etruscan origin (~25 confirmed loans)
  - `greek_substrate.py`: Pre-Greek Tyrrhenian substrate words
  - `italic_parallels.py`: Umbrian/Oscan parallels (Iguvine Tables, etc.)
  - `morphology.py`: Etruscan morphological analysis (roots, suffixes, case endings)
  - `form_predictor.py`: Predict unattested forms from known roots
  - `name_expander.py`: Expand theonyms and anthroponyms (Tinia → Tinial, etc.)

- **statistics/**: Statistical anomaly detection
  - `hapax_analyzer.py`: Find words appearing only once in Latin literature
  - `phonotactic_anomaly.py`: Detect words with non-Latin phonology
  - `geographic_scorer.py`: Boost words near Etruscan geographic markers
  - `author_profiler.py`: Weight discoveries by author reliability (Varro > Isidore)

- **ml/**: Machine learning for advanced discovery
  - `embeddings.py`: Word embeddings for semantic similarity clustering
  - `semantic_search.py`: Topic-based semantic search (divination, theatre, religion)
  - `foreign_word_ner.py`: Named Entity Recognition for foreign words in Latin text
  - `etymology_detector.py`: Detect etymology discussion passages

- **discovery/**: Unified discovery pipeline
  - `pipeline.py`: Orchestrates all discovery methods with multi-factor scoring

### Key Data Files
- `ANCIENT_GLOSSES_VERIFIED.md`: 43+ glosses with ancient source citations
- `CONSENSUS_GLOSSES_FORNI.md`: Academic consensus vocabulary (Forni et al.)
- `data/etruscan_glosses.db`: SQLite database (not in git)
- `data/latin_vocabulary.txt`: Latin vocabulary for classifier training (~1400 words)
- `data/labeled_candidates.json`: Labeled training data for context classifier
- `data/models/word_classifier.pkl`: Trained word classifier model
- `data/models/context_classifier/`: Trained context classifier model
- `data/corpus/`: Downloaded texts (not in git, ~140 MB when fully populated)
  - `latin_library/`: HTML files from thelatinlibrary.com
  - `perseus/`: XML from Perseus CTS API
  - `greek/`: JSON files from Perseus CTS API (Greek texts)
  - `github/`: Cloned CLTK repositories
  - `inscriptions/`: Etruscan inscription corpus (Zenodo CSV + CIEW text)
  - `hesychius/`: Hesychius lexicon extracts

### Validation Thresholds
- HIGH confidence: ≥0.85 → auto-accept
- MEDIUM confidence: 0.65-0.84 → needs review
- LOW confidence: <0.65 → reject

## Testing

Tests use fixtures in `tests/fixtures/sample_passages.json` containing known glosses and negative examples. Pattern tests verify >70% recall on documented glosses.

## Corpus Sources

| Source | Available Texts | Notes |
|--------|-----------------|-------|
| Latin Library | Varro, Isidore (20 books), Livy (37 books), Suetonius, Festus Breviarium | HTML scraping, 2s rate limit |
| Perseus CTS | Pliny NH, Livy, Virgil Aeneid | GetValidReff broken; use GetPassage |
| Perseus Greek | Dionysius, Strabo Geography, Herodotus, Plutarch | Greek texts with Τυρρηνοί refs |
| GitHub/CLTK | lat_text_latin_library | Pre-scraped, ~2000 files |
| Inscriptions | CIEW corpus (Zenodo + Internet Archive) | 10,000+ Etruscan words from inscriptions |
| Hesychius | Greek lexicon extracts | Scholarly glosses with Tyrrhenian tags |

**Important:** Varro, Festus De Verborum Significatione, Servius, and Isidore are NOT in Perseus CTS inventory. Use Latin Library for these.

## Claude Teacher Mode

For every project, write a detailed FOR[yourname].md file that explains the whole project in plain language.

Explain the technical architecture, the structure of the codebase and how the various parts are connected, the technologies used, why we made these technical decisions, and lessons I can learn from it (this should include the bugs we ran into and how we fixed them, potential pitfalls and how to avoid them in the future, new technologies used, how good engineers think and work, best practices, etc).

It should be very engaging to read; don't make it sound like boring technical documentation/textbook. Where appropriate, use analogies and anecdotes to make it more understandable and memorable.
