"""Latin loanword detector for Etruscan origin words.

Many Latin words are suspected or confirmed Etruscan loans,
particularly in semantic domains where Etruscans had cultural
influence: theatre, religion, luxury goods, and governance.

This module identifies Latin words that may have Etruscan origins
based on phonological, semantic, and historical criteria.
"""

import re
from dataclasses import dataclass
from typing import Optional

from ..config import DOMAIN_BOOST


@dataclass
class LoanwordCandidate:
    """A Latin word that may be an Etruscan loan."""

    latin_word: str
    meaning: str
    domain: str  # Semantic domain
    confidence: float
    evidence: list[str]  # Reasons for suspecting Etruscan origin
    etruscan_form: Optional[str] = None  # If known
    first_attestation: str = ""  # Earliest Latin source
    notes: str = ""


# Confirmed and highly probable Etruscan loanwords in Latin
KNOWN_ETRUSCAN_LOANS = [
    # Theatre/performance
    LoanwordCandidate(
        latin_word="histrio",
        meaning="actor",
        domain="theatre",
        confidence=0.95,
        evidence=["Ancient testimony (Livy)", "Non-IE etymology", "Etruscan hister attested"],
        etruscan_form="hister",
        first_attestation="Livy",
        notes="Livy explicitly states Etruscan origin",
    ),
    LoanwordCandidate(
        latin_word="persona",
        meaning="mask, character",
        domain="theatre",
        confidence=0.85,
        evidence=["Non-IE phonology", "Theatre context", "phersu attested in Etruscan tombs"],
        etruscan_form="φersu",
        notes="Tomb of the Augurs shows phersu figure",
    ),
    LoanwordCandidate(
        latin_word="subulo",
        meaning="flute player",
        domain="theatre",
        confidence=0.80,
        evidence=["Non-IE etymology", "Ancient testimony (Festus)"],
        first_attestation="Festus",
    ),

    # Religion/divination
    LoanwordCandidate(
        latin_word="haruspex",
        meaning="diviner (inspects entrails)",
        domain="divination",
        confidence=0.90,
        evidence=["Etruscan haruspicy tradition", "Non-IE morphology", "Ancient testimony"],
        notes="Core Etruscan religious practice",
    ),
    LoanwordCandidate(
        latin_word="lanista",
        meaning="gladiator trainer",
        domain="religion",
        confidence=0.85,
        evidence=["Non-IE etymology", "Etruscan funeral games context", "Isidore testimony"],
        notes="Connected to Etruscan funeral games tradition",
    ),
    LoanwordCandidate(
        latin_word="lar",
        meaning="household spirit",
        domain="religion",
        confidence=0.90,
        evidence=["Non-IE etymology", "Lar/Lars Etruscan names", "Ancient testimony"],
        etruscan_form="lar",
        notes="Etruscan family name element",
    ),
    LoanwordCandidate(
        latin_word="mantisa",
        meaning="addition, makeweight",
        domain="religion",
        confidence=0.75,
        evidence=["Non-IE phonology", "Ancient testimony (Festus)"],
        first_attestation="Festus",
    ),
    LoanwordCandidate(
        latin_word="mundus",
        meaning="ritual pit (also 'world')",
        domain="religion",
        confidence=0.70,
        evidence=["Etruscan foundation ritual", "Dual meaning religious/cosmological"],
        notes="Pit for offerings in Etruscan city foundation",
    ),

    # Luxury/material culture
    LoanwordCandidate(
        latin_word="balteus",
        meaning="belt, sword-belt",
        domain="luxury",
        confidence=0.75,
        evidence=["Non-IE etymology", "Etruscan metalwork tradition"],
    ),
    LoanwordCandidate(
        latin_word="catena",
        meaning="chain",
        domain="luxury",
        confidence=0.65,
        evidence=["Non-IE phonology", "Etruscan metalwork context"],
    ),
    LoanwordCandidate(
        latin_word="fenestra",
        meaning="window",
        domain="luxury",
        confidence=0.60,
        evidence=["Non-IE etymology", "Etruscan architecture influence"],
    ),
    LoanwordCandidate(
        latin_word="atrium",
        meaning="main hall",
        domain="luxury",
        confidence=0.80,
        evidence=["Ancient testimony (Varro)", "Atria city in Etruria", "Non-IE etymology"],
        first_attestation="Varro",
        notes="Varro connects to Etruscan Atria",
    ),

    # Governance/titles
    LoanwordCandidate(
        latin_word="lucumo",
        meaning="Etruscan chief/king",
        domain="political",
        confidence=0.95,
        evidence=["Explicitly Etruscan title", "Ancient testimony"],
        etruscan_form="lauchum?",
        notes="Etruscan royal/noble title",
    ),
    LoanwordCandidate(
        latin_word="satelles",
        meaning="attendant, bodyguard",
        domain="political",
        confidence=0.70,
        evidence=["Non-IE etymology", "Royal/court context"],
    ),
    LoanwordCandidate(
        latin_word="populus",
        meaning="people, nation",
        domain="political",
        confidence=0.50,
        evidence=["Non-IE etymology suggested", "Etruscan influence on Roman institutions"],
        notes="Controversial; some prefer IE etymology",
    ),

    # Miscellaneous
    LoanwordCandidate(
        latin_word="elementum",
        meaning="element, letter",
        domain="other",
        confidence=0.55,
        evidence=["Non-IE structure", "Etruscan alphabet transmission"],
        notes="May relate to alphabet names L-M-N",
    ),
    LoanwordCandidate(
        latin_word="cassis",
        meaning="helmet",
        domain="military",
        confidence=0.60,
        evidence=["Non-IE phonology", "Etruscan military equipment"],
    ),
    LoanwordCandidate(
        latin_word="antenna",
        meaning="sail-yard",
        domain="other",
        confidence=0.55,
        evidence=["Non-IE etymology", "Mediterranean maritime context"],
    ),
    LoanwordCandidate(
        latin_word="spurius",
        meaning="illegitimate",
        domain="other",
        confidence=0.80,
        evidence=["Etruscan spur- attested", "Ancient testimony"],
        etruscan_form="spur-",
        notes="Etruscan city/citizen root",
    ),
]


class LatinLoanwordDetector:
    """Detector for Latin words with potential Etruscan origin."""

    def __init__(self):
        """Initialize detector."""
        self.known_loans = KNOWN_ETRUSCAN_LOANS
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices."""
        self.by_word = {loan.latin_word.lower(): loan for loan in self.known_loans}
        self.by_domain = {}
        for loan in self.known_loans:
            self.by_domain.setdefault(loan.domain, []).append(loan)

    def is_known_loan(self, word: str) -> Optional[LoanwordCandidate]:
        """Check if word is a known Etruscan loan.

        Args:
            word: Latin word to check

        Returns:
            LoanwordCandidate if known, None otherwise
        """
        return self.by_word.get(word.lower())

    def get_loans_by_domain(self, domain: str) -> list[LoanwordCandidate]:
        """Get all known loans in a semantic domain.

        Args:
            domain: Domain name (theatre, religion, luxury, political)

        Returns:
            List of LoanwordCandidate objects
        """
        return self.by_domain.get(domain, [])

    def analyze_word(self, word: str, context: str = "") -> LoanwordCandidate:
        """Analyze a word for potential Etruscan origin.

        Args:
            word: Latin word to analyze
            context: Surrounding text for semantic analysis

        Returns:
            LoanwordCandidate with analysis
        """
        # Check if already known
        known = self.is_known_loan(word)
        if known:
            return known

        # Analyze unknown word
        evidence = []
        confidence = 0.3  # Base confidence for unknown words

        word_lower = word.lower()

        # Check phonological features
        if self._has_etruscan_phonology(word_lower):
            evidence.append("Non-IE phonological features")
            confidence += 0.15

        # Check endings
        if self._has_etruscan_ending(word_lower):
            evidence.append("Etruscan-type ending")
            confidence += 0.10

        # Check semantic domain
        domain = self._detect_domain(context)
        if domain in DOMAIN_BOOST:
            evidence.append(f"Found in Etruscan-influenced domain: {domain}")
            confidence += DOMAIN_BOOST[domain]

        # Check for Etruscan-like structure
        if self._has_etruscan_structure(word_lower):
            evidence.append("Etruscan-like word structure")
            confidence += 0.10

        return LoanwordCandidate(
            latin_word=word,
            meaning="?",
            domain=domain or "unknown",
            confidence=min(confidence, 0.90),
            evidence=evidence,
            notes="Automatically analyzed candidate",
        )

    def _has_etruscan_phonology(self, word: str) -> bool:
        """Check for Etruscan phonological features."""
        # No voiced stops
        if not any(c in word for c in "bdg"):
            # Has aspirates or typical Etruscan sounds
            if any(pattern in word for pattern in ["ph", "th", "ch", "rs", "rn"]):
                return True
        return False

    def _has_etruscan_ending(self, word: str) -> bool:
        """Check for Etruscan-type endings in Latinized form."""
        etruscan_endings = [
            "na", "ne", "al", "el", "is", "us",  # Common Latinized Etruscan
            "enna", "ulla", "illa",  # Etruscan diminutives
        ]
        return any(word.endswith(e) for e in etruscan_endings)

    def _has_etruscan_structure(self, word: str) -> bool:
        """Check for Etruscan-like word structure."""
        # CVCV(C) pattern, no voiced stops, typical clusters
        if len(word) >= 4 and len(word) <= 8:
            vowel_count = sum(1 for c in word if c in "aeiou")
            consonant_count = len(word) - vowel_count
            if 0.4 <= vowel_count / len(word) <= 0.6:
                return True
        return False

    def _detect_domain(self, context: str) -> str:
        """Detect semantic domain from context."""
        context_lower = context.lower()

        domain_keywords = {
            "divination": ["haruspex", "augur", "omen", "liver", "extispic", "fulg"],
            "theatre": ["actor", "scaen", "fabul", "ludi", "spectacul"],
            "religion": ["sacr", "templum", "deus", "ritual", "libat"],
            "luxury": ["aurum", "gold", "purpur", "conviv", "banquet"],
            "political": ["magistrat", "rex", "imperium", "potestas"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in context_lower for kw in keywords):
                return domain

        return "unknown"


def detect_etruscan_loanwords(text: str) -> list[tuple[str, LoanwordCandidate]]:
    """Detect potential Etruscan loanwords in a Latin text.

    Args:
        text: Latin text to analyze

    Returns:
        List of (word, LoanwordCandidate) tuples
    """
    detector = LatinLoanwordDetector()
    results = []

    # Extract words
    words = re.findall(r'\b([a-zA-Z]{3,})\b', text)

    for word in set(words):  # Unique words only
        # Check if known loan
        known = detector.is_known_loan(word)
        if known:
            results.append((word, known))
        else:
            # Analyze with context
            candidate = detector.analyze_word(word, text)
            if candidate.confidence >= 0.5:
                results.append((word, candidate))

    return sorted(results, key=lambda x: x[1].confidence, reverse=True)
