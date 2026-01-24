#!/usr/bin/env python3
"""Import seed data from markdown files into the database."""

import re
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH, PROJECT_ROOT
from etruscan_miner.db.models import EtruscanWord, VerifiedGloss
from etruscan_miner.db.repository import Repository


def parse_ancient_glosses(content: str) -> list[VerifiedGloss]:
    """Parse ANCIENT_GLOSSES_VERIFIED.md and extract glosses."""
    glosses = []

    # Pattern to match numbered entries like "### 1. **aisar / aesar / ais** = "dei / dio""
    entry_pattern = re.compile(
        r"###\s+\d+\.\s+\*\*([^*]+)\*\*\s*=\s*[\"']([^\"']+)[\"']",
        re.MULTILINE
    )

    # Find all entries
    for match in entry_pattern.finditer(content):
        word_part = match.group(1).strip()
        meaning = match.group(2).strip()

        # Handle multiple word variants (e.g., "aisar / aesar / ais")
        words = [w.strip() for w in word_part.split("/")]

        # Get context after this match to find source info
        start_pos = match.end()
        next_match = entry_pattern.search(content, start_pos)
        end_pos = next_match.start() if next_match else len(content)
        context = content[start_pos:end_pos]

        # Extract source author
        source_author = None
        source_match = re.search(r"\*\*Fonte[^:]*:\*\*\s*([^\n]+)", context)
        if source_match:
            source_text = source_match.group(1).strip()
            # Try to extract author name
            if "Svetonio" in source_text or "Suetonius" in source_text:
                source_author = "Suetonius"
            elif "Varrone" in source_text or "Varro" in source_text:
                source_author = "Varro"
            elif "Livio" in source_text or "Livy" in source_text:
                source_author = "Livy"
            elif "Isidoro" in source_text or "Isidore" in source_text:
                source_author = "Isidore"
            elif "Festo" in source_text or "Festus" in source_text:
                source_author = "Festus"
            elif "Plinio" in source_text or "Pliny" in source_text:
                source_author = "Pliny"
            else:
                source_author = source_text.split(",")[0].split("(")[0].strip()

        # Extract citation
        citation = None
        citation_match = re.search(r"\*\*Citazione:\*\*\s*[\"']([^\"']+)[\"']", context)
        if citation_match:
            citation = citation_match.group(1).strip()

        # Extract reliability
        reliability = 3  # default
        stars = context.count("⭐")
        if stars >= 5:
            reliability = 5
        elif stars >= 4:
            reliability = 4
        elif stars >= 3:
            reliability = 3
        elif stars >= 2:
            reliability = 2
        elif stars >= 1:
            reliability = 1

        # Create gloss for each word variant
        for word in words:
            word = word.strip()
            if not word:
                continue
            gloss = VerifiedGloss(
                etruscan_word=word,
                etruscan_normalized=word.lower(),
                meaning=meaning,
                source_author=source_author,
                source_quote=citation,
                reliability=reliability,
                is_seed=True,
            )
            glosses.append(gloss)

    return glosses


def parse_forni_consensus(content: str) -> list[EtruscanWord]:
    """Parse CONSENSUS_GLOSSES_FORNI.md and extract vocabulary."""
    words = []

    # Pattern for table rows: | # | **word** | "meaning" |
    table_pattern = re.compile(
        r"\|\s*\d+\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*[\"']?([^|\"']+)[\"']?\s*\|",
        re.MULTILINE
    )

    # Track which section we're in
    current_category = "basic"
    sections = {
        "LESSICO BASE CON SIGNIFICATO CERTO": "basic",
        "LESSICO NON-BASE CON SIGNIFICATO CERTO": "non-basic",
        "MORFEMI LEGATI": "morpheme",
        "LESSICO BASE CON SIGNIFICATO DUBBIO": "basic-uncertain",
        "LESSICO NON-BASE CON SIGNIFICATO DUBBIO": "non-basic-uncertain",
    }

    lines = content.split("\n")
    for i, line in enumerate(lines):
        # Check for section headers
        for section_name, category in sections.items():
            if section_name in line:
                current_category = category
                break

        # Match table rows
        match = table_pattern.match(line)
        if match:
            word_text = match.group(1).strip()
            meaning = match.group(2).strip()

            # Handle word variants
            word_variants = [w.strip() for w in re.split(r"[,/]", word_text)]

            # Determine if meaning is uncertain
            uncertain = "uncertain" in current_category or "?" in meaning

            for word in word_variants:
                if not word or word == "-":
                    continue
                # Clean up word (remove suffixes like (-))
                word = re.sub(r"\s*\([^)]*\)\s*$", "", word).strip()
                word = word.strip("-").strip()

                if not word:
                    continue

                vocab = EtruscanWord(
                    word=word,
                    word_normalized=word.lower(),
                    meaning=meaning,
                    meaning_uncertain=uncertain,
                    category=current_category.replace("-uncertain", ""),
                    source="Forni",
                    reliability=4 if not uncertain else 3,
                )
                words.append(vocab)

    return words


def import_seeds():
    """Import all seed data into the database."""
    repo = Repository(DB_PATH)

    # Import ancient glosses
    ancient_glosses_path = PROJECT_ROOT / "ANCIENT_GLOSSES_VERIFIED.md"
    if ancient_glosses_path.exists():
        print(f"Parsing {ancient_glosses_path.name}...")
        with open(ancient_glosses_path, encoding="utf-8") as f:
            content = f.read()
        glosses = parse_ancient_glosses(content)
        print(f"  Found {len(glosses)} glosses")

        imported = 0
        for gloss in glosses:
            try:
                repo.insert_verified_gloss(gloss)
                imported += 1
            except Exception as e:
                print(f"  Warning: Could not import {gloss.etruscan_word}: {e}")
        print(f"  Imported {imported} verified glosses")
    else:
        print(f"Warning: {ancient_glosses_path} not found")

    # Import Forni consensus vocabulary
    forni_path = PROJECT_ROOT / "CONSENSUS_GLOSSES_FORNI.md"
    if forni_path.exists():
        print(f"\nParsing {forni_path.name}...")
        with open(forni_path, encoding="utf-8") as f:
            content = f.read()
        words = parse_forni_consensus(content)
        print(f"  Found {len(words)} vocabulary words")

        imported = 0
        for word in words:
            try:
                repo.insert_vocabulary(word)
                imported += 1
            except Exception as e:
                print(f"  Warning: Could not import {word.word}: {e}")
        print(f"  Imported {imported} vocabulary words")
    else:
        print(f"Warning: {forni_path} not found")

    # Print final stats
    print("\nFinal database statistics:")
    stats = repo.get_stats()
    for table, count in stats.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    import_seeds()
