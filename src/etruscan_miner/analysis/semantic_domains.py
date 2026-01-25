"""Semantic domain classifier for Etruscan cultural fields.

This module classifies Latin words and passages by semantic domain,
focusing on areas where Etruscan loanwords are most likely to occur:

1. DIVINATION - haruspicy, augury, lightning interpretation
2. THEATRE - actors, masks, performance
3. RELIGION - gods, rituals, temples
4. WINE/SYMPOSIUM - drinking vessels, wine culture
5. MILITARY - gladiators, combat
6. POLITICAL - magistrates, governance
7. ARCHITECTURE - temples, houses, tombs
8. MUSIC - instruments, musicians
9. MARITIME - ships, seafaring (Tyrrhenian Sea)
10. METALLURGY - bronze, iron working

Words in these domains that have unusual phonology or unclear
etymology are prime candidates for Etruscan origin.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class EtruscanDomain(Enum):
    """Semantic domains associated with Etruscan cultural influence."""

    DIVINATION = auto()  # Highest loan probability
    THEATRE = auto()  # Very high
    RELIGION = auto()  # High
    WINE = auto()  # High
    MILITARY = auto()  # Gladiators, combat
    POLITICAL = auto()  # Magistrates, offices
    ARCHITECTURE = auto()  # Temples, houses
    MUSIC = auto()  # Instruments
    MARITIME = auto()  # Ships, sea
    METALLURGY = auto()  # Bronze, iron
    FUNERARY = auto()  # Death, tombs
    AGRICULTURE = auto()  # Lower probability
    GENERAL = auto()  # Lowest


@dataclass
class DomainClassification:
    """Result of semantic domain classification."""

    word: str
    primary_domain: EtruscanDomain
    secondary_domains: list[EtruscanDomain] = field(default_factory=list)
    confidence: float = 0.0
    loan_probability: float = 0.0  # Based on domain
    context_keywords: list[str] = field(default_factory=list)
    notes: str = ""


class SemanticDomainClassifier:
    """Classifies words by Etruscan cultural semantic domains.

    Uses keyword matching and context analysis to determine which
    semantic domain a word belongs to, then calculates loan probability
    based on the domain.
    """

    def __init__(self):
        """Initialize domain keywords and probabilities."""
        self._init_domain_keywords()
        self._init_loan_probabilities()

    def _init_domain_keywords(self) -> None:
        """Initialize keyword lists for each domain."""
        self.domain_keywords = {
            EtruscanDomain.DIVINATION: {
                # Latin keywords indicating divination context
                "latin": {
                    "haruspex", "haruspic", "extispic", "extis", "exta",
                    "iecur", "fibra", "augur", "auspic", "omen", "ostent",
                    "prodig", "fulg", "fulmen", "tonitru", "portent",
                    "divin", "vatic", "oracul", "sorte", "inspic",
                    "lituo", "lituus", "templum", "inaugurar",
                    "liver", "entrail", "intestin", "viscera",
                },
                # Etruscan-derived words in this domain
                "etruscan_derived": {
                    "haruspex", "haruspices", "haruspicina",
                },
                # Context phrases
                "phrases": [
                    r"exta\s+inspic",
                    r"iecur\s+\w+\s+haruspex",
                    r"de\s+caelo\s+\w+\s+fulmen",
                    r"disciplina\s+etrusca",
                    r"libri\s+haruspicini",
                    r"libri\s+fulgurales",
                    r"libri\s+rituales",
                ],
            },

            EtruscanDomain.THEATRE: {
                "latin": {
                    "histrio", "actor", "scaen", "scen", "ludus", "ludi",
                    "persona", "mask", "larva", "fabul", "mim", "pantomim",
                    "theatr", "cavea", "pulpit", "prosken", "chorus",
                    "saltator", "saltat", "ludion", "ister",
                    "comoedi", "tragoedi", "palliat", "togat",
                },
                "etruscan_derived": {
                    "histrio", "histriones", "persona", "personae",
                    "ister", "phersu",
                },
                "phrases": [
                    r"ludi\s+scenic",
                    r"in\s+scaena",
                    r"ex\s+etruria\s+\w+\s+ludi",
                    r"histrio\w*\s+tusco",
                    r"persona\s+\w+\s+larva",
                ],
            },

            EtruscanDomain.RELIGION: {
                "latin": {
                    "deus", "dea", "sacr", "templ", "fanum", "delubr",
                    "ritual", "caeremon", "sacrific", "libar", "libat",
                    "pontif", "flamen", "vestal", "sacerdos",
                    "pieta", "pia", "pius", "religio", "superstitio",
                    "lar", "lares", "penat", "manes", "lemur",
                    "mundus", "rogus", "piacul", "lustrat",
                },
                "etruscan_derived": {
                    "lar", "lares", "mundus",
                },
                "phrases": [
                    r"lares\s+\w+\s+penates",
                    r"mundus\s+patet",
                    r"ritu\s+tusco",
                    r"more\s+etrusco",
                    r"disciplina\s+etrusca",
                ],
            },

            EtruscanDomain.WINE: {
                "latin": {
                    "vinum", "vini", "pocu", "pocul", "calix", "crater",
                    "cyath", "patera", "phial", "scyph", "canthar",
                    "amphora", "oenophor", "lagoen", "urna", "dolium",
                    "convivi", "symposi", "comissat", "epul",
                    "mero", "merum", "mustum", "temetum",
                },
                "etruscan_derived": set(),  # Less clear
                "phrases": [
                    r"in\s+convivio",
                    r"vinum\s+\w+\s+tusci",
                    r"amphora\s+\w+\s+etrusc",
                ],
            },

            EtruscanDomain.MILITARY: {
                "latin": {
                    "gladiator", "lanista", "murmillo", "secutor", "retiar",
                    "thraex", "arena", "harena", "ludus", "gladiat",
                    "pugna", "certam", "munus", "muner", "venat",
                    "arma", "gladius", "scutum", "galea", "lorica",
                },
                "etruscan_derived": {
                    "lanista", "lanistae",
                },
                "phrases": [
                    r"munus\s+gladiator",
                    r"in\s+arena",
                    r"lanista\s+\w+\s+gladiator",
                ],
            },

            EtruscanDomain.POLITICAL: {
                "latin": {
                    "magistr", "consul", "praetor", "dictat", "censor",
                    "rex", "regn", "imperat", "imperium", "potestas",
                    "fasces", "lictor", "trabea", "sella", "curul",
                    "triumph", "toga", "praetexta", "purpur",
                    "lucumo", "zilath", "lauchum",
                },
                "etruscan_derived": {
                    "lucumo", "lucumones",
                },
                "phrases": [
                    r"fasces\s+\w+\s+etrusc",
                    r"regna\s+tusco",
                    r"more\s+regio\s+etrusc",
                    r"lucumo\s+\w+\s+rex",
                ],
            },

            EtruscanDomain.ARCHITECTURE: {
                "latin": {
                    "atrium", "impluv", "complur", "tablinum", "cubicul",
                    "templ", "aedes", "fanum", "porticus", "vestibul",
                    "tect", "culmen", "fastig", "columna", "antae",
                    "tuscan", "doric", "ionic",
                },
                "etruscan_derived": {
                    "atrium", "atria",
                },
                "phrases": [
                    r"atrium\s+tuscanicum",
                    r"more\s+tusco\s+\w+\s+aedific",
                    r"templum\s+\w+\s+etrusc",
                ],
            },

            EtruscanDomain.MUSIC: {
                "latin": {
                    "tibicen", "tibicin", "tibia", "fistula", "subulo",
                    "lituus", "tuba", "cornu", "cithara", "lyra",
                    "cantor", "can", "modul", "melodia", "symphon",
                },
                "etruscan_derived": {
                    "subulo", "subulones",
                },
                "phrases": [
                    r"tibicines\s+\w+\s+etrusc",
                    r"subulo\s+tusco",
                    r"tibia\s+\w+\s+ludis",
                ],
            },

            EtruscanDomain.MARITIME: {
                "latin": {
                    "navis", "nav", "puppis", "prora", "remus", "velum",
                    "port", "litus", "mare", "tyrrhen", "tuscum",
                    "pirat", "praedo", "naut", "gubern", "classis",
                },
                "etruscan_derived": set(),
                "phrases": [
                    r"mare\s+tyrrhenum",
                    r"mare\s+tuscum",
                    r"piratae\s+tyrrhen",
                ],
            },

            EtruscanDomain.METALLURGY: {
                "latin": {
                    "aes", "aeris", "ferrum", "bronze", "aurum", "argentum",
                    "faber", "fabr", "fornax", "flamma", "malleus",
                    "incus", "cuda", "fabrica", "officina",
                },
                "etruscan_derived": set(),
                "phrases": [
                    r"aes\s+\w+\s+etrusc",
                    r"vasa\s+\w+\s+tusca",
                ],
            },

            EtruscanDomain.FUNERARY: {
                "latin": {
                    "sepulcr", "tumul", "rogus", "busta", "ciner",
                    "urn", "sarcophag", "epitaph", "funus", "funer",
                    "manes", "lemur", "inferus", "infer", "orcus",
                    "mort", "defunct", "obitus",
                },
                "etruscan_derived": set(),
                "phrases": [
                    r"more\s+tusco\s+\w+\s+sepel",
                    r"sepulcr\w+\s+etrusc",
                ],
            },
        }

    def _init_loan_probabilities(self) -> None:
        """Initialize base loan probabilities by domain."""
        self.domain_loan_probability = {
            EtruscanDomain.DIVINATION: 0.85,  # Highest - haruspicy was Etruscan specialty
            EtruscanDomain.THEATRE: 0.80,  # Very high - theatre came from Etruria
            EtruscanDomain.RELIGION: 0.70,  # High - many religious terms
            EtruscanDomain.WINE: 0.65,  # High - Etruscan wine culture
            EtruscanDomain.MILITARY: 0.60,  # Gladiators
            EtruscanDomain.POLITICAL: 0.55,  # Symbols of power
            EtruscanDomain.MUSIC: 0.55,  # Etruscan musicians
            EtruscanDomain.ARCHITECTURE: 0.50,  # Temple styles
            EtruscanDomain.MARITIME: 0.45,  # Tyrrhenian Sea
            EtruscanDomain.METALLURGY: 0.45,  # Bronze work
            EtruscanDomain.FUNERARY: 0.40,  # Tombs
            EtruscanDomain.AGRICULTURE: 0.20,  # Lower
            EtruscanDomain.GENERAL: 0.10,  # Lowest
        }

    def classify_word(self, word: str, context: str = "") -> DomainClassification:
        """Classify a word by semantic domain.

        Args:
            word: Word to classify
            context: Surrounding text context

        Returns:
            Domain classification result
        """
        word_lower = word.lower()
        context_lower = context.lower() if context else ""

        domain_scores: dict[EtruscanDomain, float] = {}
        matched_keywords: list[str] = []

        for domain, keywords in self.domain_keywords.items():
            score = 0.0

            # Check if word matches domain keywords
            for kw in keywords.get("latin", set()):
                if kw in word_lower or word_lower in kw:
                    score += 0.5
                    matched_keywords.append(kw)

            # Check if word is known Etruscan-derived
            if word_lower in keywords.get("etruscan_derived", set()):
                score += 1.0
                matched_keywords.append(f"etruscan:{word_lower}")

            # Check context for domain keywords
            if context_lower:
                for kw in keywords.get("latin", set()):
                    if kw in context_lower:
                        score += 0.2
                        if kw not in matched_keywords:
                            matched_keywords.append(kw)

                # Check for domain-specific phrases
                for phrase_pattern in keywords.get("phrases", []):
                    if re.search(phrase_pattern, context_lower):
                        score += 0.4
                        matched_keywords.append(f"phrase:{phrase_pattern[:20]}")

            if score > 0:
                domain_scores[domain] = score

        # Determine primary and secondary domains
        if domain_scores:
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            primary_domain = sorted_domains[0][0]
            primary_score = sorted_domains[0][1]
            secondary_domains = [d for d, s in sorted_domains[1:4] if s >= primary_score * 0.5]
        else:
            primary_domain = EtruscanDomain.GENERAL
            primary_score = 0.0
            secondary_domains = []

        # Calculate loan probability
        base_probability = self.domain_loan_probability[primary_domain]

        # Boost if in multiple domains
        if secondary_domains:
            for sec_domain in secondary_domains:
                base_probability += self.domain_loan_probability[sec_domain] * 0.1

        # Boost if context mentions Etruscans
        etruscan_mentions = len(re.findall(r'tusci|etrusc|tyrr', context_lower))
        if etruscan_mentions > 0:
            base_probability = min(1.0, base_probability + 0.15 * etruscan_mentions)

        return DomainClassification(
            word=word,
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            confidence=min(1.0, primary_score / 2.0),
            loan_probability=min(1.0, base_probability),
            context_keywords=list(set(matched_keywords))[:10],
        )

    def classify_passage(self, text: str) -> dict[EtruscanDomain, float]:
        """Classify an entire passage by domain.

        Args:
            text: Passage to classify

        Returns:
            Dictionary mapping domains to scores
        """
        text_lower = text.lower()
        domain_scores: dict[EtruscanDomain, float] = {}

        for domain, keywords in self.domain_keywords.items():
            score = 0.0

            # Count keyword occurrences
            for kw in keywords.get("latin", set()):
                count = len(re.findall(rf'\b{kw}\w*\b', text_lower))
                score += count * 0.1

            # Check phrases
            for phrase in keywords.get("phrases", []):
                if re.search(phrase, text_lower):
                    score += 0.3

            if score > 0:
                domain_scores[domain] = score

        return domain_scores

    def get_high_probability_domains(self) -> list[tuple[EtruscanDomain, float]]:
        """Get domains ordered by loan probability.

        Returns:
            List of (domain, probability) tuples
        """
        items = list(self.domain_loan_probability.items())
        return sorted(items, key=lambda x: x[1], reverse=True)

    def find_domain_candidates(
        self,
        words: list[str],
        context: str = ""
    ) -> list[DomainClassification]:
        """Find words in high-probability domains.

        Args:
            words: Words to classify
            context: Shared context

        Returns:
            Classifications for words in loan-likely domains
        """
        results = []

        for word in words:
            classification = self.classify_word(word, context)
            if classification.loan_probability >= 0.5:
                results.append(classification)

        # Sort by loan probability
        results.sort(key=lambda c: c.loan_probability, reverse=True)
        return results


def classify_semantic_domain(word: str, context: str = "") -> DomainClassification:
    """Classify a word by Etruscan cultural semantic domain.

    Args:
        word: Word to classify
        context: Surrounding text context

    Returns:
        Domain classification with loan probability
    """
    classifier = SemanticDomainClassifier()
    return classifier.classify_word(word, context)
