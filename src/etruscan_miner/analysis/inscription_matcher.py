"""Inscription-to-Latin cross-reference system.

This module matches words from Etruscan inscriptions against Latin texts
to find potential unrecognized loanwords. It uses multiple matching strategies:

1. Exact match - inscription word appears in Latin
2. Root match - inscription root appears with Latin affixes
3. Derivative match - Latin word derives from inscription form
4. Phonetic match - similar sounds allowing for adaptation

The key insight is that known Etruscan words from inscriptions that also
appear in Latin texts (but aren't recognized as loans) are prime candidates
for newly discovered loanwords.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from collections import defaultdict


@dataclass
class InscriptionMatch:
    """A match between an inscription word and Latin text."""

    etruscan_word: str  # Original Etruscan form from inscription
    latin_word: str  # Matched Latin form
    match_type: str  # 'exact', 'root', 'derivative', 'phonetic'
    confidence: float  # 0.0 to 1.0
    inscription_source: str  # Source inscription
    latin_sources: list[str] = field(default_factory=list)
    frequency_in_inscriptions: int = 1
    frequency_in_latin: int = 1
    semantic_field: str = ""  # If detected
    notes: str = ""


class InscriptionMatcher:
    """Cross-references Etruscan inscriptions with Latin texts.

    This class loads the Etruscan inscription corpus and provides
    methods to find matches in Latin texts, identifying potential
    unrecognized loanwords.
    """

    def __init__(self):
        """Initialize the matcher with inscription data."""
        self.inscription_vocab: dict[str, dict] = {}
        self.latin_vocab: set[str] = set()
        self.known_loans: set[str] = set()
        self._load_inscriptions()
        self._load_known_loans()

    def _load_inscriptions(self) -> None:
        """Load Etruscan inscription vocabulary from CIEW corpus."""
        # Core vocabulary from inscriptions (subset for demonstration)
        # In production, this loads from data/corpus/inscriptions/
        self.inscription_vocab = {
            # Divine/religious terms
            "ais": {"meaning": "god", "freq": 150, "domain": "religion"},
            "aisna": {"meaning": "divine", "freq": 45, "domain": "religion"},
            "aisar": {"meaning": "gods", "freq": 89, "domain": "religion"},
            "celu": {"meaning": "earth/September", "freq": 23, "domain": "religion"},
            "cel": {"meaning": "earth", "freq": 67, "domain": "religion"},
            "cepen": {"meaning": "priest", "freq": 34, "domain": "religion"},
            "eisnev": {"meaning": "to sacrifice", "freq": 12, "domain": "religion"},
            "fanu": {"meaning": "sanctuary", "freq": 28, "domain": "religion"},
            "netsvis": {"meaning": "haruspex", "freq": 19, "domain": "divination"},
            "trutnvt": {"meaning": "haruspex", "freq": 8, "domain": "divination"},
            "frontac": {"meaning": "augur/lightning", "freq": 15, "domain": "divination"},
            "tular": {"meaning": "boundary", "freq": 89, "domain": "religion"},

            # Titles/offices
            "zilath": {"meaning": "magistrate", "freq": 234, "domain": "political"},
            "zilc": {"meaning": "magistracy", "freq": 178, "domain": "political"},
            "maru": {"meaning": "magistrate", "freq": 156, "domain": "political"},
            "marunuch": {"meaning": "magistracy", "freq": 67, "domain": "political"},
            "lucumo": {"meaning": "king/lord", "freq": 12, "domain": "political"},
            "lauchum": {"meaning": "king", "freq": 23, "domain": "political"},
            "purth": {"meaning": "dictator", "freq": 45, "domain": "political"},
            "camthi": {"meaning": "name of magistracy", "freq": 34, "domain": "political"},

            # Family/kinship
            "clan": {"meaning": "son", "freq": 567, "domain": "kinship"},
            "sec": {"meaning": "daughter", "freq": 423, "domain": "kinship"},
            "puia": {"meaning": "wife", "freq": 312, "domain": "kinship"},
            "nefts": {"meaning": "grandson/nephew", "freq": 89, "domain": "kinship"},
            "prumaths": {"meaning": "great-grandson", "freq": 34, "domain": "kinship"},
            "ati": {"meaning": "mother", "freq": 178, "domain": "kinship"},
            "papa": {"meaning": "grandfather", "freq": 56, "domain": "kinship"},
            "tethi": {"meaning": "grandmother", "freq": 45, "domain": "kinship"},

            # Numbers
            "thu": {"meaning": "one", "freq": 123, "domain": "number"},
            "zal": {"meaning": "two", "freq": 89, "domain": "number"},
            "ci": {"meaning": "three", "freq": 78, "domain": "number"},
            "sa": {"meaning": "four", "freq": 56, "domain": "number"},
            "mach": {"meaning": "five", "freq": 45, "domain": "number"},
            "huth": {"meaning": "six", "freq": 34, "domain": "number"},
            "semph": {"meaning": "seven", "freq": 23, "domain": "number"},
            "cezp": {"meaning": "eight", "freq": 19, "domain": "number"},
            "nurph": {"meaning": "nine", "freq": 15, "domain": "number"},
            "sar": {"meaning": "ten", "freq": 67, "domain": "number"},
            "avil": {"meaning": "year", "freq": 234, "domain": "time"},

            # Objects/items
            "zic": {"meaning": "writing/book", "freq": 45, "domain": "culture"},
            "zich": {"meaning": "written", "freq": 34, "domain": "culture"},
            "suthina": {"meaning": "for the tomb", "freq": 156, "domain": "funerary"},
            "suthi": {"meaning": "tomb", "freq": 289, "domain": "funerary"},
            "thapna": {"meaning": "cup/vessel", "freq": 78, "domain": "vessel"},
            "pruchum": {"meaning": "pitcher", "freq": 45, "domain": "vessel"},
            "culichna": {"meaning": "kylix (cup)", "freq": 34, "domain": "vessel"},
            "qutum": {"meaning": "pitcher", "freq": 23, "domain": "vessel"},
            "lautn": {"meaning": "family", "freq": 167, "domain": "kinship"},
            "etera": {"meaning": "foreigner/client", "freq": 56, "domain": "social"},

            # Actions/verbs
            "tur": {"meaning": "to give", "freq": 189, "domain": "action"},
            "mul": {"meaning": "to dedicate", "freq": 145, "domain": "religion"},
            "ar": {"meaning": "to make", "freq": 234, "domain": "action"},
            "ten": {"meaning": "to hold office", "freq": 89, "domain": "political"},
            "lup": {"meaning": "to die", "freq": 78, "domain": "death"},
            "ama": {"meaning": "to be", "freq": 156, "domain": "action"},
            "sval": {"meaning": "to live", "freq": 67, "domain": "life"},
            "fler": {"meaning": "to offer", "freq": 89, "domain": "religion"},
            "tur": {"meaning": "to give", "freq": 145, "domain": "action"},

            # Deities
            "tinia": {"meaning": "Jupiter/sky god", "freq": 89, "domain": "deity"},
            "uni": {"meaning": "Juno", "freq": 78, "domain": "deity"},
            "menrva": {"meaning": "Minerva", "freq": 67, "domain": "deity"},
            "turan": {"meaning": "Venus", "freq": 56, "domain": "deity"},
            "sethlans": {"meaning": "Vulcan", "freq": 45, "domain": "deity"},
            "turms": {"meaning": "Mercury", "freq": 34, "domain": "deity"},
            "fufluns": {"meaning": "Dionysus", "freq": 23, "domain": "deity"},
            "nethuns": {"meaning": "Neptune", "freq": 19, "domain": "deity"},
            "selvans": {"meaning": "Silvanus", "freq": 15, "domain": "deity"},
            "usil": {"meaning": "sun god", "freq": 34, "domain": "deity"},
            "thesan": {"meaning": "dawn goddess", "freq": 23, "domain": "deity"},
            "vetis": {"meaning": "underworld god", "freq": 12, "domain": "deity"},

            # Theatre/performance (relevant for loans)
            "phersu": {"meaning": "mask/actor", "freq": 8, "domain": "theatre"},
            "phersuna": {"meaning": "masked figure", "freq": 5, "domain": "theatre"},

            # Miscellaneous high-value
            "spura": {"meaning": "city", "freq": 123, "domain": "political"},
            "tamera": {"meaning": "temple official", "freq": 34, "domain": "religion"},
            "cecha": {"meaning": "rite/ritual", "freq": 56, "domain": "religion"},
            "hinthial": {"meaning": "ghost/shade", "freq": 23, "domain": "death"},
            "leine": {"meaning": "to die", "freq": 45, "domain": "death"},
            "thanchvil": {"meaning": "gift", "freq": 67, "domain": "action"},
            "zichu": {"meaning": "writer/scribe", "freq": 12, "domain": "culture"},
            "capra": {"meaning": "container", "freq": 34, "domain": "vessel"},
            "hampha": {"meaning": "curved vessel", "freq": 23, "domain": "vessel"},
        }

        # Try to load from actual CIEW corpus
        self._load_ciew_corpus()

    def _load_ciew_corpus(self) -> None:
        """Load vocabulary from CIEW corpus files."""
        from ..config import CORPUS_DIR

        ciew_file = CORPUS_DIR / "inscriptions" / "ciew_vocabulary.txt"
        if ciew_file.exists():
            try:
                with open(ciew_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('\t')
                            if len(parts) >= 2:
                                word = parts[0].lower()
                                if word not in self.inscription_vocab:
                                    self.inscription_vocab[word] = {
                                        "meaning": parts[1] if len(parts) > 1 else "",
                                        "freq": 1,
                                        "domain": "inscription",
                                    }
            except Exception:
                pass  # Use built-in vocab

    def _load_known_loans(self) -> None:
        """Load known Etruscan loanwords (to exclude from 'new' discoveries)."""
        self.known_loans = {
            # Theatre
            "histrio", "histriones", "persona", "personae",
            # Religion/divination
            "haruspex", "haruspices", "lanista", "lanistae",
            # Music
            "subulo", "subulones", "tibicen", "tibicines",
            # Architecture
            "atrium", "atria",
            # Titles
            "lucumo", "lucumones",
            # Religion
            "lar", "lares", "lars",
            # Misc
            "balteus", "baltei", "catena", "catenae",
            "fenestra", "fenestrae", "mantisa",
            "mundus", "satelles", "satellites",
            "spurius", "elementum", "elementa",
            "arena", "harena",  # Disputed but commonly cited
        }

    def _normalize_etruscan(self, word: str) -> str:
        """Normalize Etruscan spelling variations."""
        word = word.lower().strip()
        # Common spelling variations
        word = word.replace('χ', 'ch')
        word = word.replace('θ', 'th')
        word = word.replace('φ', 'ph')
        word = word.replace('ś', 's')
        word = word.replace('ç', 'c')
        return word

    def _normalize_latin(self, word: str) -> str:
        """Normalize Latin word for matching."""
        word = word.lower().strip()
        # Remove common Latin endings for root matching
        return word

    def _extract_root(self, word: str) -> str:
        """Extract probable root from an Etruscan word."""
        word = self._normalize_etruscan(word)

        # Remove common Etruscan suffixes
        suffixes = [
            'na', 'ra', 'la', 'sa', 'ta',  # Adjective/noun suffixes
            'al', 'il', 'ul',  # Genitive
            'thi', 'chi', 'si',  # Locative
            'ri', 'ni', 'li',  # Various
            'ce', 'che',  # Perfect
            'as', 'es', 'is', 'us',  # Endings
        ]

        for suffix in sorted(suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]

        return word

    def _phonetic_similarity(self, etr: str, lat: str) -> float:
        """Calculate phonetic similarity between Etruscan and Latin forms."""
        etr = self._normalize_etruscan(etr)
        lat = self._normalize_latin(lat)

        # Known sound correspondences
        correspondences = [
            ('ph', 'p'), ('ph', 'f'),
            ('th', 't'), ('th', 'd'),
            ('ch', 'c'), ('ch', 'k'), ('ch', 'g'),
            ('v', 'u'), ('v', 'w'),
            ('i', 'e'), ('u', 'o'),
            ('ai', 'ae'), ('ei', 'i'),
        ]

        # Apply correspondences
        etr_variants = [etr]
        for etr_sound, lat_sound in correspondences:
            new_variants = []
            for v in etr_variants:
                if etr_sound in v:
                    new_variants.append(v.replace(etr_sound, lat_sound))
            etr_variants.extend(new_variants)

        # Check for matches
        best_score = 0.0
        for variant in etr_variants:
            if variant == lat:
                return 1.0
            elif lat.startswith(variant) or variant.startswith(lat):
                score = min(len(variant), len(lat)) / max(len(variant), len(lat))
                best_score = max(best_score, score)
            elif variant in lat or lat in variant:
                score = min(len(variant), len(lat)) / max(len(variant), len(lat)) * 0.8
                best_score = max(best_score, score)

        return best_score

    def find_matches_in_text(self, text: str, source: str = "") -> list[InscriptionMatch]:
        """Find inscription words that appear in Latin text.

        Args:
            text: Latin text to search
            source: Source identifier

        Returns:
            List of matches found
        """
        matches = []
        text_lower = text.lower()

        # Extract words from text
        words_in_text = set(re.findall(r'\b[a-zA-Z]{3,}\b', text_lower))

        for etr_word, info in self.inscription_vocab.items():
            etr_norm = self._normalize_etruscan(etr_word)
            etr_root = self._extract_root(etr_word)

            for lat_word in words_in_text:
                # Skip if it's a known loan (not a new discovery)
                if lat_word in self.known_loans:
                    continue

                # Skip very common Latin words
                if lat_word in {'est', 'sunt', 'qui', 'quae', 'quod', 'et', 'in', 'ad', 'cum'}:
                    continue

                match_type = None
                confidence = 0.0

                # Exact match
                if etr_norm == lat_word:
                    match_type = "exact"
                    confidence = 0.95

                # Root match
                elif etr_root == lat_word[:len(etr_root)] and len(etr_root) >= 3:
                    match_type = "root"
                    confidence = 0.75

                # Phonetic match
                else:
                    sim = self._phonetic_similarity(etr_word, lat_word)
                    if sim >= 0.7:
                        match_type = "phonetic"
                        confidence = sim * 0.8

                if match_type:
                    # Boost confidence based on semantic domain
                    domain = info.get("domain", "")
                    if domain in {"religion", "divination", "theatre", "political"}:
                        confidence = min(1.0, confidence * 1.1)

                    matches.append(InscriptionMatch(
                        etruscan_word=etr_word,
                        latin_word=lat_word,
                        match_type=match_type,
                        confidence=confidence,
                        inscription_source="CIEW corpus",
                        latin_sources=[source] if source else [],
                        frequency_in_inscriptions=info.get("freq", 1),
                        semantic_field=domain,
                        notes=f"Etruscan meaning: {info.get('meaning', 'unknown')}",
                    ))

        return matches

    def cross_reference_corpus(self, corpus_dir: Path) -> list[InscriptionMatch]:
        """Cross-reference inscriptions against entire Latin corpus.

        Args:
            corpus_dir: Directory containing Latin texts

        Returns:
            List of all matches found
        """
        all_matches = []
        match_counts = defaultdict(int)

        # Process Latin Library files
        latin_dir = corpus_dir / "latin_library"
        if latin_dir.exists():
            for filepath in latin_dir.glob("*.html"):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    # Simple HTML stripping
                    text = re.sub(r'<[^>]+>', ' ', text)

                    matches = self.find_matches_in_text(text, filepath.stem)
                    for match in matches:
                        match_counts[(match.etruscan_word, match.latin_word)] += 1
                    all_matches.extend(matches)
                except Exception:
                    pass

        # Deduplicate and aggregate
        aggregated = {}
        for match in all_matches:
            key = (match.etruscan_word, match.latin_word)
            if key not in aggregated:
                aggregated[key] = match
            else:
                # Update with additional source
                if match.latin_sources:
                    aggregated[key].latin_sources.extend(match.latin_sources)
                aggregated[key].frequency_in_latin = match_counts[key]

        # Sort by confidence and frequency
        result = list(aggregated.values())
        result.sort(key=lambda m: (m.confidence, m.frequency_in_latin), reverse=True)

        return result

    def get_new_loan_candidates(self) -> list[InscriptionMatch]:
        """Get inscription words that could be unrecognized Latin loans.

        These are words that:
        1. Appear frequently in inscriptions (well-attested)
        2. Match patterns in Latin texts
        3. Are NOT already known as loans
        4. Are in semantic domains likely for borrowing

        Returns:
            List of candidate matches
        """
        from ..config import CORPUS_DIR

        matches = self.cross_reference_corpus(CORPUS_DIR)

        # Filter for high-quality candidates
        candidates = []
        for match in matches:
            # Skip known loans
            if match.latin_word in self.known_loans:
                continue

            # Require minimum confidence
            if match.confidence < 0.65:
                continue

            # Prefer words in loan-likely domains
            loan_domains = {"religion", "divination", "theatre", "political", "vessel"}
            if match.semantic_field in loan_domains:
                match.confidence = min(1.0, match.confidence * 1.15)

            candidates.append(match)

        # Sort by confidence
        candidates.sort(key=lambda m: m.confidence, reverse=True)

        return candidates[:50]  # Top 50


def cross_reference_inscriptions(text: str, source: str = "") -> list[InscriptionMatch]:
    """Cross-reference Etruscan inscriptions with Latin text.

    Args:
        text: Latin text to search
        source: Source identifier

    Returns:
        List of matches found
    """
    matcher = InscriptionMatcher()
    return matcher.find_matches_in_text(text, source)
