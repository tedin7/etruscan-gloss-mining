# Etruscan Gloss Mining

**Computational linguistics project to discover undocumented Etruscan glosses in ancient Greek and Latin texts using NLP and LLM pattern matching.**

Mining Perseus Digital Library and other corpora for phrases like *"Tusci vocant"*, *"lingua Etrusca"*, *"apud Etruscos"* to extract vocabulary the ancients preserved but modern scholarship hasn't systematically catalogued.

## The Problem

Ancient Roman authors occasionally explained Etruscan words in their texts. These "glosses" are scattered across thousands of pages of Latin and Greek literature. No one has ever done a **systematic computational scan** of the entire classical corpus to find them all.

**Current state:**
- ~60 known glosses documented by Etruscologists
- Thousands of Latin/Greek texts never searched systematically
- Pattern recognition could reveal dozens more

## Project Goals

1. **Build search patterns** for Etruscan mentions in Latin/Greek texts
2. **Mine Perseus Digital Library** (and other corpora) using NLP
3. **Extract and validate** candidate glosses
4. **Cross-reference** with existing Etruscan vocabulary
5. **Publish findings** for academic verification

## Repository Structure

```
etruscan-gloss-mining/
├── README.md                           # This file
├── CLAUDE.md                           # Development guide for Claude Code
├── FORYOU.md                           # Plain-language project explainer
├── PROJECT_SUMMARY.md                  # Full project overview
├── ANCIENT_GLOSSES_VERIFIED.md         # 47+ verified glosses from ancient sources
├── CONSENSUS_GLOSSES_FORNI.md          # 43+20+24 consensus glosses (Etruscologists)
├── glossary_tripod_complete.md         # Complete Tripod glossary (~1,500 words)
├── src/etruscan_miner/                 # Python package
│   ├── patterns/                       # Regex patterns for gloss detection
│   ├── validation/                     # 3-layer ML validation pipeline
│   ├── corpus/                         # Text acquisition (Perseus, Latin Library, Greek)
│   └── db/                             # SQLite persistence
├── scripts/                            # CLI tools
├── tests/                              # Pytest test suite
└── data/                               # Local data (not in repo)
    ├── etruscan_glosses.db             # SQLite database
    ├── labeled_candidates.json         # ML training data
    ├── models/                         # Trained classifiers
    └── corpus/                         # Downloaded texts (~140 MB)
```

## Key Resources

### Compiled Documentation (in this repo)
- **ANCIENT_GLOSSES_VERIFIED.md** - Verified glosses with ancient source citations
- **CONSENSUS_GLOSSES_FORNI.md** - Academic consensus: 43 basic + 20 non-basic + 24 morphemes
- **glossary_tripod_complete.md** - ~1,500 Etruscan words with definitions

### External Sources (not included - copyright)
- [Mel Copeland - Etruscan Glossary A](https://www.academia.edu/759774/) (2,800 words)
- [Gianfranco Forni - Basic Lexicon Database](https://www.academia.edu/22530267/)
- [Forni - Etruscan & Indo-European](https://www.academia.edu/37660067/)
- [Perseus Digital Library](https://www.perseus.tufts.edu/hopper/)
- [Etruscan Texts Project (UMass)](https://scholarworks.umass.edu/ces_texts/)

## Search Patterns

Target phrases to mine in Latin texts:

| Pattern | English | Example |
|---------|---------|---------|
| `Tusci vocant` | "The Etruscans call..." | Pliny, Varro |
| `lingua Etrusca` | "in the Etruscan language" | Various |
| `apud Etruscos` | "among the Etruscans" | Festus |
| `Etrusco vocabulo` | "with an Etruscan word" | Servius |
| `quod Etrusci` | "which the Etruscans..." | Multiple |

## Ancient Authors to Mine

| Author | Work | Potential |
|--------|------|-----------|
| **Varro** | *De Lingua Latina* | HIGH - etymologies |
| **Festus** | *De verborum significatione* | HIGH - dictionary |
| **Suetonius** | *Lives* | MEDIUM - anecdotes |
| **Isidore of Seville** | *Etymologiae* | MEDIUM - compilations |
| **Pliny the Elder** | *Naturalis Historia* | MEDIUM - plant/animal names |
| **Servius** | *Aeneid Commentary* | MEDIUM - annotations |

## Known Glosses (Examples)

| Etruscan | Meaning | Source | Reliability |
|----------|---------|--------|-------------|
| `aisar/aesar` | "gods" | Suetonius, Cassius Dio | ⭐⭐⭐⭐⭐ |
| `ais` | "god" | Multiple | ⭐⭐⭐⭐⭐ |
| `lanista` | "gladiator trainer" | Isidore | ⭐⭐⭐⭐ |
| `histrio` | "actor" | Livy, Valerius Maximus | ⭐⭐⭐⭐ |
| `subulo` | "flute player" | Varro | ⭐⭐⭐ |

## Methodology

### Phase 1: Pattern Development ✅
- 45+ regex patterns for Latin/Greek gloss indicators
- Tested against known positive examples (>70% recall)
- Confidence scores per pattern (0.65-0.95)

### Phase 2: Corpus Mining ✅
- Perseus CTS API (Latin: Pliny, Livy; Greek: Dionysius, Strabo, Herodotus)
- Latin Library HTML scraping (100+ texts: Varro, Festus, Isidore)
- CLTK GitHub repos (~2000 files)
- CIEW inscription corpus (10,000+ Etruscan words)

### Phase 3: Validation ✅
- 3-layer ML filter for false positive reduction
- Cross-reference against known vocabulary
- Phonotactic plausibility scoring
- Weighted scoring: pattern (30%) + cross-ref (30%) + linguistic (20%) + context (20%)

### Phase 4: Publication 🔴
- Document new findings
- Submit to Etruscological community for verification

## Technical Stack (Implemented)

- **Corpus access:** Perseus CTS API (Latin & Greek), Latin Library HTML scraping, CLTK GitHub repos, CIEW inscription corpus, Hesychius lexicon
- **Pattern matching:** 45+ regex patterns for Latin/Greek gloss indicators
- **ML Validation:** 3-layer filter:
  - Layer 1: spaCy/stanza dependency parsing for Etruscan attribution
  - Layer 2: Character n-gram word classifier (Etruscan vs Latin)
  - Layer 3: Context classifier (TF-IDF/embeddings/DistilBERT)
- **Storage:** SQLite with 10-table schema
- **Testing:** pytest with 107 tests, >70% recall on known glosses

## Quick Start

```bash
# Setup
python scripts/setup_database.py
python scripts/import_seeds.py

# Download texts
python scripts/download_all_texts.py --all

# Mine for glosses
python scripts/mine_glosses.py --corpus latin_library
python scripts/mine_glosses.py --corpus greek

# Validate and export
python scripts/validate_candidates.py --use-ml
python scripts/export_results.py --format markdown -o results/findings.md
```

## Contributing

This is an open research project. Contributions welcome:
- Pattern suggestions
- New corpus sources
- Validation of candidate glosses
- Code for mining pipelines

## References

### Academic Sources
- Bonfante, G. & L. (2002). *The Etruscan Language: An Introduction*
- Rix, H. (1991). *Etruskische Texte*
- Facchetti, G. M. (2000). *Frammenti di diritto privato etrusco*

### Online Resources
- [Rick Mc Callister - Etruscan Glossary (Tripod)](https://etruscans1.tripod.com)
- [Etruscan Texts Project](https://scholarworks.umass.edu/ces_texts/)
- [Perseus Digital Library](https://www.perseus.tufts.edu/hopper/)

## License

Documentation: CC BY 4.0
Code: MIT (when implemented)

---

*Started: January 2026 | Last updated: 2026-01-25*
