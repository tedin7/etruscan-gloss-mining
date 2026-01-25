#!/usr/bin/env python3
"""Script for discovering new Etruscan words using the full pipeline.

This script runs all discovery methods on texts to find new Etruscan
vocabulary that may not have been previously identified.

Usage:
    # Discover from a single text
    python scripts/discover_new_words.py --text "Tusci vocant subulo quod nos tibicinem"

    # Discover from a file
    python scripts/discover_new_words.py --file data/corpus/latin_library/varro_ll.txt

    # Discover from corpus
    python scripts/discover_new_words.py --corpus latin_library --author varro

    # Export results
    python scripts/discover_new_words.py --corpus all --output results/new_discoveries.json

    # Show high-confidence candidates only
    python scripts/discover_new_words.py --corpus all --min-confidence 0.70
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.discovery import DiscoveryPipeline, run_full_discovery


def main():
    parser = argparse.ArgumentParser(
        description="Discover new Etruscan words using the full pipeline"
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Text to analyze directly"
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="File to analyze"
    )
    parser.add_argument(
        "--corpus", "-c",
        type=str,
        choices=["latin_library", "perseus", "greek", "all"],
        help="Corpus to analyze"
    )
    parser.add_argument(
        "--author", "-a",
        type=str,
        help="Author name for reliability weighting"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.40,
        help="Minimum confidence threshold (default: 0.40)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Get text to analyze
    if args.text:
        text = args.text
        source = "command line"
    elif args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        text = args.file.read_text()
        source = str(args.file)
    elif args.corpus:
        # Load from corpus
        print(f"Loading corpus: {args.corpus}")
        text, source = load_corpus(args.corpus)
    else:
        print("Error: Must specify --text, --file, or --corpus")
        parser.print_help()
        sys.exit(1)

    # Run discovery
    print(f"\n🔍 Running discovery pipeline...")
    print(f"   Source: {source[:50]}..." if len(source) > 50 else f"   Source: {source}")
    print(f"   Text length: {len(text):,} characters")
    print(f"   Min confidence: {args.min_confidence}")

    result = run_full_discovery(
        text=text,
        source=source,
        author=args.author,
        min_confidence=args.min_confidence
    )

    # Output results
    print(f"\n✅ Discovery complete!")
    print(f"   Methods used: {result.total_methods_used}")
    print(f"   Candidates found: {len(result.candidates)}")
    print(f"   - High confidence (≥0.70): {result.high_confidence_count}")
    print(f"   - Medium confidence (0.50-0.69): {result.medium_confidence_count}")
    print(f"   - Low confidence (<0.50): {result.low_confidence_count}")

    if args.format == "json":
        output = format_json(result)
    elif args.format == "markdown":
        output = format_markdown(result)
    else:
        output = format_text(result, verbose=args.verbose)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
        print(f"\n📄 Results saved to: {args.output}")
    else:
        print("\n" + output)


def load_corpus(corpus_name: str) -> tuple[str, str]:
    """Load text from a corpus.

    Args:
        corpus_name: Corpus to load

    Returns:
        Tuple of (text, source)
    """
    from etruscan_miner.config import CORPUS_DIR

    texts = []
    source_parts = []

    if corpus_name in ["latin_library", "all"]:
        ll_dir = CORPUS_DIR / "latin_library"
        if ll_dir.exists():
            for f in list(ll_dir.glob("*.txt"))[:10]:  # Limit for demo
                texts.append(f.read_text())
                source_parts.append(f.stem)

    if corpus_name in ["perseus", "all"]:
        perseus_dir = CORPUS_DIR / "perseus"
        if perseus_dir.exists():
            for f in list(perseus_dir.glob("*.xml"))[:10]:
                texts.append(f.read_text())
                source_parts.append(f.stem)

    if not texts:
        # Return sample text for demo
        texts = ["""
        Tusci vocant subulo quod nos tibicinem dicimus. Histrio enim Tuscum
        nomen est, ab Istria unde hi ludi primum inveniri. Haruspex quoque
        vocabulum Etruscum est. Lanista gladiatorum magister, quem Etrusci
        sic vocant. Persona a personando dicta, quam Tusci larva appellant.
        """]
        source_parts = ["sample_text"]

    return "\n\n".join(texts), ", ".join(source_parts[:5])


def format_text(result, verbose: bool = False) -> str:
    """Format results as text.

    Args:
        result: DiscoveryResult
        verbose: Include extra details

    Returns:
        Formatted text
    """
    lines = ["=" * 60, "DISCOVERY RESULTS", "=" * 60, ""]

    if not result.candidates:
        lines.append("No candidates found above confidence threshold.")
        return "\n".join(lines)

    # Group by confidence level
    high = [c for c in result.candidates if c.confidence >= 0.70]
    medium = [c for c in result.candidates if 0.50 <= c.confidence < 0.70]
    low = [c for c in result.candidates if c.confidence < 0.50]

    if high:
        lines.append("🌟 HIGH CONFIDENCE (≥0.70):")
        lines.append("-" * 40)
        for c in high:
            lines.append(f"  {c.word:20} {c.confidence:.2f}")
            if c.meaning_hint:
                lines.append(f"                       Meaning: {c.meaning_hint}")
            if c.cross_linguistic_support:
                lines.append(f"                       Support: {', '.join(c.cross_linguistic_support)}")
            if verbose and c.context:
                lines.append(f"                       Context: {c.context[:80]}...")
        lines.append("")

    if medium:
        lines.append("⭐ MEDIUM CONFIDENCE (0.50-0.69):")
        lines.append("-" * 40)
        for c in medium:
            lines.append(f"  {c.word:20} {c.confidence:.2f}")
            if verbose and c.notes:
                lines.append(f"                       {c.notes}")
        lines.append("")

    if low:
        lines.append("○ LOW CONFIDENCE (<0.50):")
        lines.append("-" * 40)
        for c in low[:10]:  # Limit low confidence
            lines.append(f"  {c.word:20} {c.confidence:.2f}")
        if len(low) > 10:
            lines.append(f"  ... and {len(low) - 10} more")
        lines.append("")

    return "\n".join(lines)


def format_json(result) -> str:
    """Format results as JSON.

    Args:
        result: DiscoveryResult

    Returns:
        JSON string
    """
    data = {
        "summary": {
            "total_candidates": len(result.candidates),
            "high_confidence": result.high_confidence_count,
            "medium_confidence": result.medium_confidence_count,
            "low_confidence": result.low_confidence_count,
            "methods_used": result.total_methods_used,
        },
        "candidates": [
            {
                "word": c.word,
                "confidence": c.confidence,
                "methods": [m.name for m in c.methods],
                "meaning_hint": c.meaning_hint,
                "cross_linguistic_support": c.cross_linguistic_support,
                "phonotactic_score": c.phonotactic_score,
                "source": c.source,
                "context": c.context[:200] if c.context else "",
            }
            for c in result.candidates
        ]
    }
    return json.dumps(data, indent=2)


def format_markdown(result) -> str:
    """Format results as Markdown.

    Args:
        result: DiscoveryResult

    Returns:
        Markdown string
    """
    lines = ["# Etruscan Discovery Results", ""]

    lines.append("## Summary")
    lines.append(f"- **Total candidates:** {len(result.candidates)}")
    lines.append(f"- **High confidence (≥0.70):** {result.high_confidence_count}")
    lines.append(f"- **Medium confidence (0.50-0.69):** {result.medium_confidence_count}")
    lines.append(f"- **Low confidence (<0.50):** {result.low_confidence_count}")
    lines.append("")

    if result.candidates:
        lines.append("## Candidates")
        lines.append("")
        lines.append("| Word | Confidence | Methods | Support |")
        lines.append("|------|------------|---------|---------|")

        for c in result.candidates[:30]:  # Limit for readability
            methods = ", ".join(m.name for m in c.methods[:2])
            support = ", ".join(c.cross_linguistic_support[:2]) if c.cross_linguistic_support else "-"
            lines.append(f"| {c.word} | {c.confidence:.2f} | {methods} | {support} |")

        if len(result.candidates) > 30:
            lines.append(f"| ... | ... | ... | ({len(result.candidates) - 30} more) |")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
