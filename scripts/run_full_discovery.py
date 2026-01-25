#!/usr/bin/env python3
"""Run full discovery pipeline on all corpus sources.

This script runs the complete Etruscan word discovery pipeline across
all available corpus sources and produces a comprehensive report.

Usage:
    # Run full discovery
    python scripts/run_full_discovery.py

    # Run on specific sources
    python scripts/run_full_discovery.py --sources latin_library,perseus

    # Export results
    python scripts/run_full_discovery.py --output results/discoveries.json

    # High confidence only
    python scripts/run_full_discovery.py --min-confidence 0.70
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import CORPUS_DIR, DATA_DIR
from etruscan_miner.discovery import DiscoveryPipeline, run_full_discovery


def extract_text_from_html(html: str) -> str:
    """Extract text from HTML, removing tags.

    Args:
        html: HTML content

    Returns:
        Plain text
    """
    import re
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_corpus_texts(sources: list[str] = None) -> list[tuple[str, str, str]]:
    """Load all corpus texts.

    Args:
        sources: List of sources to load (or all if None)

    Returns:
        List of (text, source, author) tuples
    """
    texts = []
    all_sources = sources or ["latin_library", "perseus", "greek", "github"]

    # Latin Library (HTML files)
    if "latin_library" in all_sources:
        ll_dir = CORPUS_DIR / "latin_library"
        if ll_dir.exists():
            for f in ll_dir.glob("*.html"):
                try:
                    html = f.read_text(encoding='utf-8', errors='ignore')
                    # Simple HTML to text extraction
                    text = extract_text_from_html(html)
                    if len(text) > 100:
                        author = guess_author(f.stem)
                        texts.append((text, f"latin_library:{f.stem}", author))
                except Exception as e:
                    print(f"  Warning: Could not read {f}: {e}")

    # Perseus
    if "perseus" in all_sources:
        perseus_dir = CORPUS_DIR / "perseus"
        if perseus_dir.exists():
            for f in perseus_dir.glob("*.xml"):
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                    author = guess_author(f.stem)
                    texts.append((text, f"perseus:{f.stem}", author))
                except Exception as e:
                    print(f"  Warning: Could not read {f}: {e}")

    # Greek
    if "greek" in all_sources:
        greek_dir = CORPUS_DIR / "greek"
        if greek_dir.exists():
            for f in greek_dir.glob("*.json"):
                try:
                    with open(f) as fp:
                        data = json.load(fp)
                    if isinstance(data, dict):
                        text = data.get("text", "") or json.dumps(data)
                    else:
                        text = str(data)
                    author = guess_author(f.stem)
                    texts.append((text, f"greek:{f.stem}", author))
                except Exception as e:
                    print(f"  Warning: Could not read {f}: {e}")

    # GitHub/CLTK
    if "github" in all_sources:
        github_dir = CORPUS_DIR / "github"
        if github_dir.exists():
            # Only process a subset - too many files
            count = 0
            for f in github_dir.rglob("*.txt"):
                if count >= 100:  # Limit for performance
                    break
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                    if len(text) > 500:  # Skip tiny files
                        author = guess_author(f.stem)
                        texts.append((text, f"github:{f.stem}", author))
                        count += 1
                except Exception:
                    pass

    return texts


def guess_author(filename: str) -> str:
    """Guess author from filename.

    Args:
        filename: Source filename

    Returns:
        Author name or 'unknown'
    """
    filename_lower = filename.lower()

    author_patterns = {
        "varro": "varro",
        "festus": "festus",
        "isidor": "isidore",
        "livy": "livy",
        "livius": "livy",
        "pliny": "pliny",
        "plinius": "pliny",
        "virgil": "virgil",
        "vergil": "virgil",
        "cicero": "cicero",
        "servius": "servius",
        "macrobius": "macrobius",
        "suetonius": "suetonius",
        "dionysius": "dionysius",
        "strabo": "strabo",
        "ovid": "ovid",
    }

    for pattern, author in author_patterns.items():
        if pattern in filename_lower:
            return author

    return "unknown"


def run_discovery_on_corpus(
    texts: list[tuple[str, str, str]],
    min_confidence: float = 0.40
) -> dict:
    """Run discovery on all corpus texts.

    Args:
        texts: List of (text, source, author) tuples
        min_confidence: Minimum confidence threshold

    Returns:
        Discovery results summary
    """
    pipeline = DiscoveryPipeline(min_confidence=min_confidence)

    all_candidates = defaultdict(lambda: {
        "confidence": 0.0,
        "sources": [],
        "methods": set(),
        "support": [],
        "meaning": "",
    })

    total_texts = len(texts)
    print(f"\n📚 Processing {total_texts} texts...")

    for i, (text, source, author) in enumerate(texts):
        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{total_texts}...")

        try:
            result = pipeline.discover(
                text=text,
                source=source,
                author=author,
                language="greek" if "greek" in source else "latin"
            )

            for candidate in result.candidates:
                key = candidate.normalized
                entry = all_candidates[key]

                # Update with best confidence
                if candidate.confidence > entry["confidence"]:
                    entry["confidence"] = candidate.confidence
                    entry["meaning"] = candidate.meaning_hint

                # Accumulate sources and methods
                if source not in entry["sources"]:
                    entry["sources"].append(source)
                entry["methods"].update(m.name for m in candidate.methods)
                entry["support"].extend(candidate.cross_linguistic_support)

        except Exception as e:
            print(f"   Warning: Error processing {source}: {e}")

    # Convert to serializable format
    results = []
    for word, data in all_candidates.items():
        results.append({
            "word": word,
            "confidence": data["confidence"],
            "sources_count": len(data["sources"]),
            "sources": data["sources"][:5],  # Limit for readability
            "methods": list(data["methods"]),
            "cross_linguistic_support": list(set(data["support"]))[:3],
            "meaning": data["meaning"],
        })

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "timestamp": datetime.now().isoformat(),
        "texts_processed": total_texts,
        "unique_candidates": len(results),
        "high_confidence": len([r for r in results if r["confidence"] >= 0.70]),
        "medium_confidence": len([r for r in results if 0.50 <= r["confidence"] < 0.70]),
        "candidates": results,
    }


def print_results(results: dict, verbose: bool = False):
    """Print discovery results.

    Args:
        results: Discovery results dict
        verbose: Show extra details
    """
    print("\n" + "=" * 60)
    print("FULL CORPUS DISCOVERY RESULTS")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"   Texts processed: {results['texts_processed']}")
    print(f"   Unique candidates: {results['unique_candidates']}")
    print(f"   High confidence (≥0.70): {results['high_confidence']}")
    print(f"   Medium confidence (0.50-0.69): {results['medium_confidence']}")

    candidates = results["candidates"]

    # High confidence
    high = [c for c in candidates if c["confidence"] >= 0.70]
    if high:
        print(f"\n🌟 HIGH CONFIDENCE CANDIDATES ({len(high)}):")
        print("-" * 50)
        for c in high[:20]:
            print(f"  {c['word']:20} {c['confidence']:.2f}  ({c['sources_count']} sources)")
            if c["meaning"]:
                print(f"                       → {c['meaning']}")
            if c["cross_linguistic_support"]:
                print(f"                       ✓ {', '.join(c['cross_linguistic_support'])}")
        if len(high) > 20:
            print(f"  ... and {len(high) - 20} more")

    # Medium confidence
    medium = [c for c in candidates if 0.50 <= c["confidence"] < 0.70]
    if medium and verbose:
        print(f"\n⭐ MEDIUM CONFIDENCE CANDIDATES ({len(medium)}):")
        print("-" * 50)
        for c in medium[:15]:
            methods = ", ".join(c["methods"][:2])
            print(f"  {c['word']:20} {c['confidence']:.2f}  [{methods}]")
        if len(medium) > 15:
            print(f"  ... and {len(medium) - 15} more")

    # New discoveries (not known loanwords)
    known_loans = {
        "histrio", "persona", "haruspex", "lanista", "subulo",
        "atrium", "lucumo", "lar", "mantisa", "mundus", "balteus",
        "catena", "fenestra", "satelles", "spurius", "elementum"
    }

    potential_new = [c for c in high if c["word"].lower() not in known_loans]
    if potential_new:
        print(f"\n🔬 POTENTIAL NEW DISCOVERIES ({len(potential_new)}):")
        print("-" * 50)
        for c in potential_new[:10]:
            print(f"  {c['word']:20} {c['confidence']:.2f}")
            if c["cross_linguistic_support"]:
                print(f"                       Support: {', '.join(c['cross_linguistic_support'])}")


def main():
    parser = argparse.ArgumentParser(
        description="Run full discovery pipeline on corpus"
    )
    parser.add_argument(
        "--sources",
        type=str,
        help="Comma-separated list of sources (latin_library,perseus,greek,github)"
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
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Parse sources
    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]

    print("🔍 Etruscan Word Discovery Pipeline")
    print("=" * 40)

    # Load corpus
    print("\n📂 Loading corpus texts...")
    texts = load_corpus_texts(sources)
    print(f"   Loaded {len(texts)} texts")

    if not texts:
        print("❌ No corpus texts found. Run download_all_texts.py first.")
        sys.exit(1)

    # Run discovery
    results = run_discovery_on_corpus(texts, args.min_confidence)

    # Print results
    print_results(results, args.verbose)

    # Save results
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

    print("\n✅ Discovery complete!")


if __name__ == "__main__":
    main()
