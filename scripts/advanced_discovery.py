#!/usr/bin/env python3
"""Advanced Etruscan word discovery using new analysis methods.

This script combines four advanced approaches to find genuinely new
Etruscan vocabulary:

1. Inscription cross-reference - match inscription words to Latin
2. Semantic domain analysis - Etruscan cultural field detection
3. Phonotactic fingerprinting - language-specific sound patterns
4. Proto-Tyrsenian reconstruction - ancestral form prediction

Usage:
    python scripts/advanced_discovery.py --all
    python scripts/advanced_discovery.py --inscriptions
    python scripts/advanced_discovery.py --domains
    python scripts/advanced_discovery.py --phonotactic
    python scripts/advanced_discovery.py --proto
"""

import argparse
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import CORPUS_DIR, DATA_DIR
from etruscan_miner.analysis import (
    InscriptionMatcher,
    SemanticDomainClassifier,
    EtruscanDomain,
    PhonotacticFingerprinter,
    ProtoTyrsenianReconstructor,
)


@dataclass
class AdvancedCandidate:
    """A candidate from advanced analysis."""
    word: str
    confidence: float
    method: str
    evidence: str
    semantic_domain: str = ""
    phonotactic_score: float = 0.0
    proto_form: str = ""
    inscription_freq: int = 0
    latin_sources: int = 0
    is_known_loan: bool = False


def extract_text_from_html(html: str) -> str:
    """Extract text from HTML."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = re.sub(r'&\w+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_corpus_text() -> str:
    """Load all corpus text."""
    texts = []

    # Latin Library
    latin_dir = CORPUS_DIR / "latin_library"
    if latin_dir.exists():
        for f in latin_dir.glob("*.html"):
            try:
                html = f.read_text(encoding='utf-8', errors='ignore')
                text = extract_text_from_html(html)
                texts.append(text)
            except Exception:
                pass

    return "\n\n".join(texts)


def run_inscription_analysis() -> list[AdvancedCandidate]:
    """Run inscription cross-reference analysis."""
    print("\n" + "=" * 60)
    print("APPROACH 1: INSCRIPTION CROSS-REFERENCE")
    print("=" * 60)
    print("Matching Etruscan inscription vocabulary against Latin texts...")

    matcher = InscriptionMatcher()
    candidates = matcher.get_new_loan_candidates()

    results = []
    print(f"\nFound {len(candidates)} potential new loans from inscriptions:\n")

    for match in candidates[:25]:
        print(f"  {match.etruscan_word:15} → {match.latin_word:15} "
              f"({match.match_type}, conf={match.confidence:.2f})")
        if match.semantic_field:
            print(f"                    Domain: {match.semantic_field}")
        if match.notes:
            print(f"                    {match.notes}")

        results.append(AdvancedCandidate(
            word=match.latin_word,
            confidence=match.confidence,
            method="inscription_crossref",
            evidence=f"Matches Etr. {match.etruscan_word} ({match.notes})",
            semantic_domain=match.semantic_field,
            inscription_freq=match.frequency_in_inscriptions,
            latin_sources=match.frequency_in_latin,
        ))

    return results


def run_semantic_analysis() -> list[AdvancedCandidate]:
    """Run semantic domain analysis."""
    print("\n" + "=" * 60)
    print("APPROACH 2: SEMANTIC DOMAIN ANALYSIS")
    print("=" * 60)
    print("Finding words in Etruscan cultural domains...")

    classifier = SemanticDomainClassifier()
    corpus_text = load_corpus_text()

    # Extract unique words
    words = set(re.findall(r'\b[a-zA-Z]{4,15}\b', corpus_text.lower()))

    # Filter common Latin
    common = {
        'quod', 'quid', 'quae', 'qui', 'quem', 'esse', 'sunt', 'erat',
        'enim', 'autem', 'tamen', 'igitur', 'etiam', 'quia', 'unde',
        'ante', 'post', 'inter', 'super', 'contra', 'propter',
        'omnis', 'omnes', 'magna', 'magno', 'multa', 'multi',
    }
    words = words - common

    # Classify each word
    results = []
    high_prob = []

    for word in words:
        classification = classifier.classify_word(word, corpus_text[:5000])
        if classification.loan_probability >= 0.6:
            high_prob.append(classification)

    # Sort by probability
    high_prob.sort(key=lambda c: c.loan_probability, reverse=True)

    print(f"\nFound {len(high_prob)} words in high-probability domains:\n")

    # Show by domain
    domain_words = {}
    for c in high_prob[:50]:
        domain = c.primary_domain.name
        if domain not in domain_words:
            domain_words[domain] = []
        domain_words[domain].append(c)

    for domain, words_list in sorted(domain_words.items(),
                                      key=lambda x: -classifier.domain_loan_probability.get(
                                          EtruscanDomain[x[0]], 0)):
        print(f"\n  {domain} (base prob: {classifier.domain_loan_probability.get(EtruscanDomain[domain], 0):.0%}):")
        for c in words_list[:5]:
            print(f"    {c.word:20} prob={c.loan_probability:.2f}")
            results.append(AdvancedCandidate(
                word=c.word,
                confidence=c.loan_probability,
                method="semantic_domain",
                evidence=f"Domain: {domain}",
                semantic_domain=domain,
            ))

    return results


def run_phonotactic_analysis() -> list[AdvancedCandidate]:
    """Run phonotactic fingerprinting."""
    print("\n" + "=" * 60)
    print("APPROACH 3: PHONOTACTIC FINGERPRINTING")
    print("=" * 60)
    print("Finding words with Etruscan-like phonology...")

    fingerprinter = PhonotacticFingerprinter()
    corpus_text = load_corpus_text()

    # Analyze text
    fingerprints = fingerprinter.analyze_text(corpus_text)

    # Get substrate candidates
    candidates = [f for f in fingerprints if f.substrate_probability >= 0.5]

    print(f"\nFound {len(candidates)} words with Etruscan-like phonology:\n")

    results = []
    for fp in candidates[:30]:
        print(f"  {fp.word:20} Etr={fp.etruscan_score:.2f} Lat={fp.latin_score:.2f} "
              f"Substrate={fp.substrate_probability:.2f}")
        if fp.etruscan_features:
            print(f"                      Features: {', '.join(fp.etruscan_features[:3])}")

        results.append(AdvancedCandidate(
            word=fp.word,
            confidence=fp.substrate_probability,
            method="phonotactic",
            evidence=f"Etruscan features: {', '.join(fp.etruscan_features[:3])}",
            phonotactic_score=fp.etruscan_score,
        ))

    return results


def run_proto_reconstruction() -> list[AdvancedCandidate]:
    """Run Proto-Tyrsenian reconstruction."""
    print("\n" + "=" * 60)
    print("APPROACH 4: PROTO-TYRSENIAN RECONSTRUCTION")
    print("=" * 60)
    print("Matching Latin words to reconstructed Proto-Tyrsenian forms...")

    reconstructor = ProtoTyrsenianReconstructor()

    # Get high-confidence reconstructions
    proto_forms = reconstructor.get_high_confidence_reconstructions()
    print(f"\nUsing {len(proto_forms)} reconstructed Proto-Tyrsenian forms:\n")

    for pf in proto_forms[:10]:
        attestations = []
        if pf.etruscan_reflex:
            attestations.append(f"Etr: {pf.etruscan_reflex}")
        if pf.lemnian_reflex:
            attestations.append(f"Lem: {pf.lemnian_reflex}")
        if pf.raetic_reflex:
            attestations.append(f"Rae: {pf.raetic_reflex}")
        print(f"  {pf.proto_form:12} = '{pf.meaning}' ({', '.join(attestations)})")

    # Find Latin matches
    all_matches = reconstructor.find_all_latin_loans()

    print(f"\nFound {len(all_matches)} potential Latin loans from Proto-Tyrsenian:\n")

    results = []
    for match in all_matches[:20]:
        print(f"  {match.latin_word:20} < {match.proto_form:12} "
              f"({match.match_type}, conf={match.confidence:.2f})")
        if match.phonetic_changes:
            print(f"                      Changes: {', '.join(match.phonetic_changes)}")

        results.append(AdvancedCandidate(
            word=match.latin_word,
            confidence=match.confidence,
            method="proto_tyrsenian",
            evidence=f"< {match.proto_form}",
            proto_form=match.proto_form,
        ))

    return results


def combine_results(results_list: list[list[AdvancedCandidate]]) -> list[AdvancedCandidate]:
    """Combine results from all methods."""
    # Aggregate by word
    word_data = {}

    for results in results_list:
        for candidate in results:
            word = candidate.word.lower()
            if word not in word_data:
                word_data[word] = {
                    "word": candidate.word,
                    "methods": [],
                    "max_confidence": 0.0,
                    "evidence": [],
                    "semantic_domain": "",
                    "phonotactic_score": 0.0,
                    "proto_form": "",
                    "inscription_freq": 0,
                }

            data = word_data[word]
            data["methods"].append(candidate.method)
            data["max_confidence"] = max(data["max_confidence"], candidate.confidence)
            if candidate.evidence:
                data["evidence"].append(candidate.evidence)
            if candidate.semantic_domain:
                data["semantic_domain"] = candidate.semantic_domain
            if candidate.phonotactic_score:
                data["phonotactic_score"] = candidate.phonotactic_score
            if candidate.proto_form:
                data["proto_form"] = candidate.proto_form
            if candidate.inscription_freq:
                data["inscription_freq"] = candidate.inscription_freq

    # Convert to candidates with boosted scores for multi-method hits
    combined = []
    for word, data in word_data.items():
        num_methods = len(set(data["methods"]))

        # Boost confidence for words found by multiple methods
        boosted_conf = data["max_confidence"]
        if num_methods >= 2:
            boosted_conf = min(1.0, boosted_conf * 1.2)
        if num_methods >= 3:
            boosted_conf = min(1.0, boosted_conf * 1.1)

        combined.append(AdvancedCandidate(
            word=data["word"],
            confidence=boosted_conf,
            method="+".join(sorted(set(data["methods"]))),
            evidence=" | ".join(data["evidence"][:3]),
            semantic_domain=data["semantic_domain"],
            phonotactic_score=data["phonotactic_score"],
            proto_form=data["proto_form"],
            inscription_freq=data["inscription_freq"],
        ))

    # Sort by confidence
    combined.sort(key=lambda c: c.confidence, reverse=True)
    return combined


def print_final_results(candidates: list[AdvancedCandidate]):
    """Print final combined results."""
    print("\n" + "=" * 60)
    print("COMBINED RESULTS - HIGHEST PROBABILITY NEW DISCOVERIES")
    print("=" * 60)

    # Known loans to exclude
    known = {
        'histrio', 'persona', 'haruspex', 'lanista', 'subulo',
        'atrium', 'lucumo', 'lar', 'catena', 'fenestra',
        'balteus', 'mantisa', 'satelles', 'spurius', 'elementum',
        'histriones', 'haruspices', 'personae', 'lanistae',
    }

    # Filter to truly new candidates
    new_candidates = [c for c in candidates if c.word.lower() not in known]

    # Multi-method hits (highest priority)
    multi_method = [c for c in new_candidates if '+' in c.method]

    print(f"\n🌟 MULTI-METHOD CANDIDATES ({len(multi_method)} found by 2+ methods):\n")
    for c in multi_method[:15]:
        print(f"  {c.word:20} conf={c.confidence:.2f} [{c.method}]")
        print(f"                      {c.evidence[:70]}")
        print()

    # High confidence single method
    single_high = [c for c in new_candidates
                   if '+' not in c.method and c.confidence >= 0.7]

    print(f"\n⭐ HIGH CONFIDENCE SINGLE-METHOD ({len(single_high)}):\n")
    for c in single_high[:15]:
        print(f"  {c.word:20} conf={c.confidence:.2f} [{c.method}]")
        if c.semantic_domain:
            print(f"                      Domain: {c.semantic_domain}")
        if c.proto_form:
            print(f"                      Proto: {c.proto_form}")

    # Summary stats
    print("\n" + "-" * 60)
    print("SUMMARY:")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  Multi-method hits: {len(multi_method)}")
    print(f"  High confidence (>0.7): {len([c for c in new_candidates if c.confidence >= 0.7])}")
    print(f"  Known loans excluded: {len([c for c in candidates if c.word.lower() in known])}")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Etruscan word discovery"
    )
    parser.add_argument("--all", action="store_true", help="Run all methods")
    parser.add_argument("--inscriptions", action="store_true", help="Inscription cross-reference")
    parser.add_argument("--domains", action="store_true", help="Semantic domain analysis")
    parser.add_argument("--phonotactic", action="store_true", help="Phonotactic fingerprinting")
    parser.add_argument("--proto", action="store_true", help="Proto-Tyrsenian reconstruction")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")

    args = parser.parse_args()

    # Default to all if nothing specified
    if not any([args.inscriptions, args.domains, args.phonotactic, args.proto]):
        args.all = True

    print("🔬 Advanced Etruscan Word Discovery")
    print("=" * 60)

    all_results = []

    if args.all or args.inscriptions:
        all_results.append(run_inscription_analysis())

    if args.all or args.domains:
        all_results.append(run_semantic_analysis())

    if args.all or args.phonotactic:
        all_results.append(run_phonotactic_analysis())

    if args.all or args.proto:
        all_results.append(run_proto_reconstruction())

    # Combine if multiple methods run
    if len(all_results) > 1:
        combined = combine_results(all_results)
        print_final_results(combined)

        # Save results
        if args.output:
            output_data = {
                "method": "advanced_discovery",
                "candidates": [asdict(c) for c in combined],
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")

    print("\n✅ Advanced discovery complete!")


if __name__ == "__main__":
    main()
