#!/usr/bin/env python3
"""Systematic multi-method verification of Etruscan loan candidates.

Applies the HARENA methodology to all candidates:
1. Phonotactic fingerprinting
2. Inscription cross-reference
3. Semantic domain analysis
4. Proto-Tyrsenian reconstruction
5. Cross-linguistic parallels (Lemnian/Raetic)

Words confirmed by 2+ methods are strong candidates for
reclassification from "possibly Etruscan" to "likely Etruscan".
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
import json
import re

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.analysis import (
    InscriptionMatcher,
    SemanticDomainClassifier,
    EtruscanDomain,
    PhonotacticFingerprinter,
    ProtoTyrsenianReconstructor,
)
from etruscan_miner.linguistics import LemnianAnalyzer, RaeticAnalyzer


@dataclass
class VerifiedCandidate:
    """A candidate verified by multiple methods."""
    word: str
    methods_confirmed: list[str] = field(default_factory=list)
    total_methods: int = 0
    confidence: float = 0.0

    # Evidence from each method
    phonotactic_score: float = 0.0
    phonotactic_features: list[str] = field(default_factory=list)

    inscription_match: str = ""
    inscription_meaning: str = ""
    inscription_domain: str = ""

    semantic_domain: str = ""
    semantic_probability: float = 0.0

    proto_form: str = ""
    proto_confidence: float = 0.0

    lemnian_parallel: str = ""
    raetic_parallel: str = ""

    # Status
    known_loan: bool = False
    semi_known: bool = False  # Already suspected but not confirmed
    potentially_new: bool = False

    notes: str = ""


class SystematicVerifier:
    """Systematically verifies candidates using multiple methods."""

    def __init__(self):
        print("Initializing verification systems...")
        self.fingerprinter = PhonotacticFingerprinter()
        self.inscriptions = InscriptionMatcher()
        self.domains = SemanticDomainClassifier()
        self.proto = ProtoTyrsenianReconstructor()
        self.lemnian = LemnianAnalyzer()
        self.raetic = RaeticAnalyzer()

        # Known Etruscan loans (already accepted)
        self.known_loans = {
            'histrio', 'histriones', 'persona', 'personae',
            'haruspex', 'haruspices', 'lanista', 'lanistae',
            'subulo', 'subulones', 'atrium', 'atria',
            'lucumo', 'lucumones', 'lar', 'lares',
            'catena', 'catenae', 'fenestra', 'fenestrae',
            'balteus', 'baltei', 'mantisa', 'satelles',
            'spurius', 'elementum', 'elementa', 'mundus',
        }

        # Semi-known (suspected but not confirmed)
        self.semi_known = {
            'harena', 'arena',  # Wiktionary: "possibly from Etruscan"
            'lanterna',  # Sometimes cited
            'antenna',  # Debated
            'cisterna',  # Sometimes cited
            'taberna',  # Sometimes cited
            'popina',  # Sometimes cited
            'trutina',  # Balance - debated
            'scaena', 'scena',  # Stage - Greek through Etruscan?
            'triumphus',  # Greek through Etruscan
            'tunica',  # Sometimes cited
            'roma',  # The city name itself - debated
        }

        # Words to test - combination of candidates from our discovery
        self.test_words = self._build_word_list()

    def _build_word_list(self) -> list[str]:
        """Build comprehensive word list from all sources."""
        words = set()

        # From our previous discovery results
        discovery_file = Path("results/full_discoveries.json")
        if discovery_file.exists():
            with open(discovery_file) as f:
                data = json.load(f)
            for c in data.get("candidates", []):
                if c.get("confidence", 0) >= 0.65:
                    words.add(c["word"].lower())

        # Add semi-known and test cases
        words.update(self.semi_known)

        # Add words with -na, -ra, -la endings from Latin
        # These are phonotactically Etruscan-like
        etruscan_ending_words = {
            # -na endings
            'harena', 'arena', 'antenna', 'cisterna', 'caverna',
            'lanterna', 'taberna', 'lucerna', 'lacerna', 'matrona',
            'persona', 'corona', 'columna', 'lamina', 'femina',
            'machina', 'patina', 'resina', 'ruina', 'culina',
            'rapina', 'regina', 'vagina', 'trutina', 'pruina',
            'farina', 'carina', 'salina', 'catena', 'pinna',
            'gemina', 'stamina', 'nomina', 'semina', 'lumina',

            # -ra endings
            'capra', 'fibra', 'umbra', 'fenestra', 'palestra',
            'orchestra', 'palaestra', 'magistra',

            # -la endings
            'fabula', 'tabula', 'nebula', 'fibula', 'copula',
            'formula', 'insula', 'peninsula', 'spatula', 'specula',

            # Theatre/religion domain
            'histrio', 'mimus', 'scaena', 'persona', 'larva',
            'haruspex', 'augur', 'fanum', 'templum',

            # Political domain
            'lucumo', 'lictor', 'fasces', 'trabea', 'triumphus',

            # Misc candidates
            'capra', 'tuba', 'littera', 'elementum',
        }
        words.update(etruscan_ending_words)

        return sorted(list(words))

    def verify_word(self, word: str) -> VerifiedCandidate:
        """Apply all verification methods to a word."""
        result = VerifiedCandidate(word=word)

        # Check if known
        if word.lower() in self.known_loans:
            result.known_loan = True
        if word.lower() in self.semi_known:
            result.semi_known = True

        # Method 1: Phonotactic fingerprinting
        fp = self.fingerprinter.fingerprint(word)
        result.phonotactic_score = fp.etruscan_score
        result.phonotactic_features = fp.etruscan_features

        if fp.substrate_probability >= 0.5:
            result.methods_confirmed.append("PHONOTACTIC")

        # Method 2: Inscription matching
        for etr_word, info in self.inscriptions.inscription_vocab.items():
            # Check for matches
            etr_norm = etr_word.lower()
            word_norm = word.lower()

            if etr_norm == word_norm:
                result.inscription_match = etr_word
                result.inscription_meaning = info.get("meaning", "")
                result.inscription_domain = info.get("domain", "")
                result.methods_confirmed.append("INSCRIPTION")
                break

            # Root match
            if len(etr_norm) >= 3 and word_norm.startswith(etr_norm):
                result.inscription_match = etr_word
                result.inscription_meaning = info.get("meaning", "")
                result.inscription_domain = info.get("domain", "")
                result.methods_confirmed.append("INSCRIPTION")
                break

        # Method 3: Semantic domain
        classification = self.domains.classify_word(word)
        result.semantic_domain = classification.primary_domain.name
        result.semantic_probability = classification.loan_probability

        if classification.loan_probability >= 0.6:
            result.methods_confirmed.append("SEMANTIC")

        # Method 4: Proto-Tyrsenian
        for proto_form in self.proto.reconstructions.values():
            matches = self.proto.find_latin_matches(proto_form)
            for match in matches:
                if match.latin_word.lower() == word.lower():
                    result.proto_form = proto_form.proto_form
                    result.proto_confidence = match.confidence
                    if match.confidence >= 0.5:
                        result.methods_confirmed.append("PROTO")
                    break

        # Method 5: Lemnian parallels
        try:
            lemnian_match = self.lemnian.find_parallel(word)
            if lemnian_match:
                result.lemnian_parallel = lemnian_match.lemnian_word
                result.methods_confirmed.append("LEMNIAN")
        except Exception:
            pass

        # Method 6: Raetic parallels
        try:
            raetic_match = self.raetic.find_parallel(word)
            if raetic_match:
                result.raetic_parallel = raetic_match.raetic_word
                result.methods_confirmed.append("RAETIC")
        except Exception:
            pass

        # Calculate totals
        result.total_methods = len(result.methods_confirmed)

        # Calculate confidence based on methods confirmed
        base_conf = 0.3
        for method in result.methods_confirmed:
            if method == "INSCRIPTION":
                base_conf += 0.25
            elif method == "PHONOTACTIC":
                base_conf += 0.15
            elif method == "SEMANTIC":
                base_conf += 0.10
            elif method == "PROTO":
                base_conf += 0.20
            elif method in ("LEMNIAN", "RAETIC"):
                base_conf += 0.15

        result.confidence = min(1.0, base_conf)

        # Mark as potentially new if multi-method and not known
        if result.total_methods >= 2 and not result.known_loan:
            result.potentially_new = True

        return result

    def verify_all(self) -> list[VerifiedCandidate]:
        """Verify all words in the test list."""
        results = []

        for word in self.test_words:
            result = self.verify_word(word)
            if result.total_methods >= 1:  # At least one method confirms
                results.append(result)

        # Sort by number of methods, then confidence
        results.sort(key=lambda r: (r.total_methods, r.confidence), reverse=True)

        return results

    def print_report(self, results: list[VerifiedCandidate]):
        """Print comprehensive verification report."""
        print("\n" + "=" * 70)
        print("SYSTEMATIC MULTI-METHOD VERIFICATION REPORT")
        print("=" * 70)

        # Categorize results
        multi_method_new = [r for r in results if r.total_methods >= 2 and not r.known_loan]
        multi_method_known = [r for r in results if r.total_methods >= 2 and r.known_loan]
        semi_known_confirmed = [r for r in results if r.semi_known and r.total_methods >= 2]
        single_method = [r for r in results if r.total_methods == 1]

        # Report multi-method NEW discoveries
        print(f"\n🌟 MULTI-METHOD NEW DISCOVERIES ({len(multi_method_new)})")
        print("   Words confirmed by 2+ methods, NOT already known as Etruscan")
        print("-" * 70)

        for r in multi_method_new[:25]:
            status = "📗 SEMI-KNOWN" if r.semi_known else "📘 NEW"
            print(f"\n  {r.word.upper():20} [{r.total_methods} methods] conf={r.confidence:.2f} {status}")
            print(f"    Methods: {', '.join(r.methods_confirmed)}")

            if r.phonotactic_features:
                print(f"    Phonotactic: {', '.join(r.phonotactic_features[:3])}")
            if r.inscription_match:
                print(f"    Inscription: {r.inscription_match} = '{r.inscription_meaning}'")
            if r.proto_form:
                print(f"    Proto-Tyrsenian: {r.proto_form}")
            if r.lemnian_parallel:
                print(f"    Lemnian parallel: {r.lemnian_parallel}")
            if r.raetic_parallel:
                print(f"    Raetic parallel: {r.raetic_parallel}")
            if r.semantic_domain != "GENERAL":
                print(f"    Semantic domain: {r.semantic_domain} (prob={r.semantic_probability:.2f})")

        # Report semi-known now confirmed
        print(f"\n\n📗 SEMI-KNOWN NOW MULTI-METHOD CONFIRMED ({len(semi_known_confirmed)})")
        print("   Words suspected of Etruscan origin, now systematically verified")
        print("-" * 70)

        for r in semi_known_confirmed:
            print(f"\n  {r.word.upper():20} [{r.total_methods} methods] conf={r.confidence:.2f}")
            print(f"    Methods: {', '.join(r.methods_confirmed)}")
            if r.phonotactic_features:
                print(f"    Phonotactic: {', '.join(r.phonotactic_features[:3])}")

        # Validate known loans
        print(f"\n\n✓ KNOWN LOANS VALIDATED ({len(multi_method_known)})")
        print("   Already-accepted Etruscan loans confirmed by our methodology")
        print("-" * 70)

        for r in multi_method_known[:10]:
            print(f"  {r.word:20} [{r.total_methods} methods] {', '.join(r.methods_confirmed)}")

        # Summary statistics
        print("\n\n" + "=" * 70)
        print("SUMMARY STATISTICS")
        print("=" * 70)
        print(f"  Total words analyzed: {len(self.test_words)}")
        print(f"  Words with 1+ method confirmation: {len(results)}")
        print(f"  Multi-method (2+) confirmations: {len([r for r in results if r.total_methods >= 2])}")
        print(f"    - Known loans validated: {len(multi_method_known)}")
        print(f"    - Semi-known confirmed: {len(semi_known_confirmed)}")
        print(f"    - Potentially NEW: {len([r for r in multi_method_new if not r.semi_known])}")
        print(f"  Single-method hits: {len(single_method)}")

        # Method effectiveness
        print("\n  Method hit rates:")
        for method in ["PHONOTACTIC", "INSCRIPTION", "SEMANTIC", "PROTO", "LEMNIAN", "RAETIC"]:
            count = len([r for r in results if method in r.methods_confirmed])
            print(f"    {method:12}: {count} hits")


def main():
    print("🔬 Systematic Multi-Method Verification")
    print("   Applying HARENA methodology to all candidates\n")

    verifier = SystematicVerifier()

    print(f"\nAnalyzing {len(verifier.test_words)} candidate words...")
    results = verifier.verify_all()

    verifier.print_report(results)

    # Save results
    output_file = Path("results/verified_candidates.json")
    output_data = {
        "method": "systematic_multi_method_verification",
        "total_analyzed": len(verifier.test_words),
        "multi_method_confirmed": len([r for r in results if r.total_methods >= 2]),
        "candidates": [
            {
                "word": r.word,
                "methods": r.methods_confirmed,
                "total_methods": r.total_methods,
                "confidence": r.confidence,
                "known_loan": r.known_loan,
                "semi_known": r.semi_known,
                "potentially_new": r.potentially_new,
                "phonotactic_score": r.phonotactic_score,
                "phonotactic_features": r.phonotactic_features,
                "inscription_match": r.inscription_match,
                "inscription_meaning": r.inscription_meaning,
                "semantic_domain": r.semantic_domain,
                "proto_form": r.proto_form,
                "lemnian_parallel": r.lemnian_parallel,
                "raetic_parallel": r.raetic_parallel,
            }
            for r in results if r.total_methods >= 2
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    print("\n✅ Verification complete!")


if __name__ == "__main__":
    main()
