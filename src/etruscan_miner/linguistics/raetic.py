"""Raetic language corpus and analysis.

Raetic is attested from ~200 inscriptions from the Alpine region
(Trentino-Alto Adige, Veneto, Tyrol). It may be related to
Etruscan as part of the Tyrsenian language family, though this
is debated. Shared vocabulary would be significant evidence.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RaeticInscription:
    """A Raetic inscription with analysis."""

    id: str  # Standard inscription ID (e.g., "SZ-1")
    text: str
    transliteration: str
    words: list[str]
    provenance: str
    date: str  # e.g., "5th c. BCE"
    notes: str = ""


@dataclass
class RaeticWord:
    """A Raetic word with analysis."""

    form: str
    normalized: str
    meaning: Optional[str] = None
    part_of_speech: Optional[str] = None
    inscription_id: str = ""
    etruscan_parallel: Optional[str] = None
    confidence: float = 0.0
    morphology: str = ""  # Morphological notes (e.g., "-ale suffix")
    notes: str = ""


# Key Raetic vocabulary (from Monumenta Linguae Raeticae and other sources)
RAETIC_VOCABULARY = [
    # Theophoric/religious terms
    RaeticWord(
        form="tinake",
        normalized="tinake",
        meaning="?gave/?dedicated",
        part_of_speech="verb",
        etruscan_parallel="tinś (Tinia, Jupiter)",
        confidence=0.75,
        notes="May contain theonym Tin- (cf. Etruscan Tinia)",
    ),
    RaeticWord(
        form="upiku",
        normalized="upiku",
        meaning="?",
        part_of_speech="noun",
        inscription_id="SZ-1",
        notes="Common element in Raetic",
    ),
    RaeticWord(
        form="laśanuale",
        normalized="lasanuale",
        meaning="?of Lasanu",
        part_of_speech="adjective",
        etruscan_parallel="-ale (genitive)",
        confidence=0.70,
        morphology="-ale suffix matches Etruscan/Lemnian",
    ),
    RaeticWord(
        form="pitave",
        normalized="pitave",
        meaning="?",
        part_of_speech="noun/verb",
        inscription_id="MA-1",
        notes="Possibly verbal",
    ),
    RaeticWord(
        form="eluku",
        normalized="eluku",
        meaning="?",
        part_of_speech="noun",
        notes="Personal name or title",
    ),
    RaeticWord(
        form="φelna",
        normalized="phelna",
        meaning="?",
        part_of_speech="noun",
        etruscan_parallel="velna-? (Vulcan?)",
        confidence=0.40,
        notes="Possibly theophoric",
    ),
    RaeticWord(
        form="kve",
        normalized="kve",
        meaning="and?",
        part_of_speech="conjunction",
        etruscan_parallel="-c/-k (and)",
        confidence=0.60,
        notes="Possibly enclitic conjunction like Etruscan -c",
    ),
    RaeticWord(
        form="rituske",
        normalized="rituske",
        meaning="?",
        part_of_speech="unknown",
        notes="-ke suffix possibly verbal",
    ),
    RaeticWord(
        form="śtena",
        normalized="stena",
        meaning="?",
        part_of_speech="noun",
        etruscan_parallel="-na (adjective suffix)",
        confidence=0.50,
        morphology="-na suffix like Etruscan",
    ),
    RaeticWord(
        form="kaśtrie",
        normalized="kastrie",
        meaning="?",
        part_of_speech="noun",
        notes="Possibly ethnic or title",
    ),
    RaeticWord(
        form="φeθiale",
        normalized="phethiale",
        meaning="?of Phethia",
        part_of_speech="genitive",
        etruscan_parallel="-ale (genitive)",
        confidence=0.70,
        morphology="-ale genitive like Etruscan",
    ),
    RaeticWord(
        form="laive",
        normalized="laive",
        meaning="?",
        part_of_speech="unknown",
        etruscan_parallel="lai- (?))",
        confidence=0.30,
    ),
    RaeticWord(
        form="priam",
        normalized="priam",
        meaning="?",
        part_of_speech="unknown",
        morphology="-m ending",
    ),
    RaeticWord(
        form="esimne",
        normalized="esimne",
        meaning="?",
        part_of_speech="unknown",
        notes="Possibly verbal or nominal",
    ),
    RaeticWord(
        form="velχanu",
        normalized="velchanu",
        meaning="Vulcan?",
        part_of_speech="theonym",
        etruscan_parallel="Velχans (Vulcan)",
        confidence=0.80,
        notes="Clear parallel to Etruscan Velchans/Vulcan",
    ),
    RaeticWord(
        form="aθale",
        normalized="athale",
        meaning="?of Atha",
        part_of_speech="genitive",
        etruscan_parallel="-ale",
        confidence=0.65,
        morphology="-ale genitive",
    ),
    RaeticWord(
        form="piθamne",
        normalized="pithamne",
        meaning="?",
        part_of_speech="unknown",
        morphology="-mne suffix",
    ),
    RaeticWord(
        form="lemnal",
        normalized="lemnal",
        meaning="?of Lemna",
        part_of_speech="genitive",
        etruscan_parallel="-al (genitive)",
        confidence=0.75,
        morphology="-al genitive like Etruscan",
    ),
    RaeticWord(
        form="φirakuśt",
        normalized="phirakust",
        meaning="?",
        part_of_speech="unknown",
        inscription_id="IT-1",
    ),
]

# Key inscriptions
RAETIC_CORPUS = [
    RaeticInscription(
        id="SZ-1",
        text="upiku laviśealu φelna",
        transliteration="upiku lavishealu phelna",
        words=["upiku", "lavishealu", "phelna"],
        provenance="Sanzeno",
        date="5th c. BCE",
    ),
    RaeticInscription(
        id="MA-1",
        text="pitave tinake",
        transliteration="pitave tinake",
        words=["pitave", "tinake"],
        provenance="Magrè",
        date="5th c. BCE",
        notes="Contains possible theonym Tin-",
    ),
    RaeticInscription(
        id="IT-1",
        text="φirakuśt velsie",
        transliteration="phirakust velsie",
        words=["phirakust", "velsie"],
        provenance="Isera-Tirano",
        date="5th-4th c. BCE",
    ),
    RaeticInscription(
        id="VN-1",
        text="velχanu esimne",
        transliteration="velchanu esimne",
        words=["velchanu", "esimne"],
        provenance="Veneto",
        date="5th c. BCE",
        notes="Contains Vulcan theonym",
    ),
]


class RaeticAnalyzer:
    """Analyzer for Raetic-Etruscan comparisons."""

    def __init__(self):
        """Initialize with corpus."""
        self.vocabulary = RAETIC_VOCABULARY
        self.inscriptions = RAETIC_CORPUS
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices."""
        self.by_form = {w.normalized: w for w in self.vocabulary}
        self.by_parallel = {}
        for w in self.vocabulary:
            if w.etruscan_parallel:
                parallel = w.etruscan_parallel.split("(")[0].strip().strip("*-?")
                if parallel:
                    self.by_parallel.setdefault(parallel.lower(), []).append(w)

    def find_parallel(self, etruscan_word: str) -> list[RaeticWord]:
        """Find Raetic parallels for an Etruscan word.

        Args:
            etruscan_word: Etruscan word to check

        Returns:
            List of Raetic words with potential parallels
        """
        word_lower = etruscan_word.lower()
        results = []

        # Direct parallel lookup
        if word_lower in self.by_parallel:
            results.extend(self.by_parallel[word_lower])

        # Check for morphological matches
        for raetic_word in self.vocabulary:
            if raetic_word in results:
                continue

            # Check shared endings
            if self._share_morpheme(word_lower, raetic_word.normalized):
                results.append(raetic_word)

        return results

    def _share_morpheme(self, etr: str, rae: str) -> bool:
        """Check if words share a morpheme."""
        shared_endings = ["al", "ale", "na", "ne", "ke", "ce"]
        for ending in shared_endings:
            if etr.endswith(ending) and rae.endswith(ending):
                return True
        return False

    def get_shared_morphemes(self) -> dict[str, list[tuple[str, str]]]:
        """Get morphemes shared with Etruscan.

        Returns:
            Dict mapping morpheme to (Raetic, Etruscan) example pairs
        """
        return {
            "-al/-ale (genitive)": [
                ("laśanuale", "spurial"),
                ("lemnal", "clan-al"),
                ("φeθiale", "vel-ial"),
            ],
            "-na (adjective)": [
                ("śtena", "rasna"),
            ],
            "-ke/-ce (verbal?)": [
                ("tinake", "turce"),
                ("rituske", "mulvenece"),
            ],
            "Tin- (Jupiter)": [
                ("tinake", "Tinia"),
            ],
            "Velχ- (Vulcan)": [
                ("velχanu", "Velχans"),
            ],
        }

    def validate_etruscan_word(self, word: str) -> tuple[bool, float, str]:
        """Check if an Etruscan word has Raetic support.

        Args:
            word: Word to validate

        Returns:
            Tuple of (has_parallel, confidence, notes)
        """
        parallels = self.find_parallel(word)

        if not parallels:
            return False, 0.0, "No Raetic parallel found"

        best = max(parallels, key=lambda w: w.confidence)
        notes = f"Raetic parallel: {best.form}"
        if best.meaning:
            notes += f" ({best.meaning})"

        return True, best.confidence, notes


def find_raetic_parallels(etruscan_words: list[str]) -> list[tuple[str, RaeticWord, float]]:
    """Find Raetic parallels for a list of Etruscan words.

    Args:
        etruscan_words: List of Etruscan words

    Returns:
        List of (etruscan_word, raetic_word, confidence) tuples
    """
    analyzer = RaeticAnalyzer()
    results = []

    for word in etruscan_words:
        parallels = analyzer.find_parallel(word)
        for parallel in parallels:
            results.append((word, parallel, parallel.confidence))

    return sorted(results, key=lambda x: x[2], reverse=True)
