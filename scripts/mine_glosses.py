#!/usr/bin/env python3
"""Mine glosses from corpus texts using pattern matching."""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import CORPUS_CACHE_DIR, DB_PATH, TARGET_WORKS
from etruscan_miner.corpus.github_corpus import GitHubCorpusReader
from etruscan_miner.corpus.greek_texts import GreekCorpusClient, GREEK_WORKS
from etruscan_miner.corpus.latin_library import LatinLibraryClient, LATIN_LIBRARY_URLS
from etruscan_miner.corpus.perseus import PerseusClient, TextPassage
from etruscan_miner.corpus.text_cache import WorkCache
from etruscan_miner.db.models import Author, Candidate, Passage, Work
from etruscan_miner.db.repository import Repository
from etruscan_miner.patterns.extractor import GlossExtractor


@dataclass
class TextItem:
    """A text item to mine, with metadata for DB storage."""

    text: str
    reference: str
    author: str
    title: str
    urn: str
    priority: str = "LOW"
    source_url: str = ""
    language: str = "latin"


def mine_texts(
    repo: Repository,
    extractor: GlossExtractor,
    texts: Iterator[TextItem],
    source_name: str,
    total_count: Optional[int] = None,
    min_confidence: float = 0.0,
    progress_interval: int = 50,
) -> tuple[int, int]:
    """Generic mining function for any corpus source.

    Args:
        repo: Database repository
        extractor: Gloss extractor
        texts: Iterator of TextItem objects to mine
        source_name: Name for progress messages (e.g., "Latin Library")
        total_count: Total number of texts (for progress %, optional)
        min_confidence: Minimum pattern confidence
        progress_interval: How often to print progress

    Returns:
        Tuple of (texts_scanned, candidates_found)
    """
    scanned = 0
    found = 0

    total_str = f"/{total_count}" if total_count else ""
    print(f"\nMining {source_name}...")

    # Cache for authors and works to avoid repeated DB lookups
    author_cache: dict[str, int] = {}
    work_cache: dict[str, int] = {}

    for item in texts:
        scanned += 1

        # Get or create author
        if item.author not in author_cache:
            author = Author(
                name=item.author,
                description=f"Author from {source_name}",
            )
            author_cache[item.author] = repo.insert_author(author)
        author_id = author_cache[item.author]

        # Get or create work
        work_key = f"{item.author}:{item.title}"
        if work_key not in work_cache:
            work = Work(
                author_id=author_id,
                title=item.title,
                urn=item.urn,
                priority=item.priority,
            )
            work_cache[work_key] = repo.insert_work(work)
        work_id = work_cache[work_key]

        # Extract glosses
        result = extractor.extract(item.text, language=item.language)

        if result.found_glosses:
            # Store passage
            db_passage = Passage(
                work_id=work_id,
                reference=item.reference,
                text_latin=item.text[:10000],
                text_normalized=item.text[:10000].lower(),
                source_url=item.source_url,
            )
            passage_id = repo.insert_passage(db_passage)

            # Store each candidate
            for match in result.get_high_confidence_matches(min_confidence):
                candidate = Candidate(
                    passage_id=passage_id,
                    mining_run_id=None,
                    etruscan_word=match.etruscan_word,
                    etruscan_normalized=match.etruscan_word.lower(),
                    meaning_proposed=match.meaning_hint,
                    context_before=match.context_before,
                    context_after=match.context_after,
                    full_match=match.full_match,
                    pattern_confidence=match.confidence,
                    status="pending",
                )
                repo.insert_candidate(candidate)
                found += 1

        if scanned % progress_interval == 0:
            print(f"  Scanned {scanned}{total_str} texts, found {found} candidates")

    print(f"  {source_name}: Scanned {scanned} texts, found {found} candidates")
    return scanned, found


def ensure_work_in_db(repo: Repository, work_key: str) -> int:
    """Ensure work and author exist in database.

    Args:
        repo: Database repository
        work_key: Key from TARGET_WORKS

    Returns:
        Work ID
    """
    work_info = TARGET_WORKS[work_key]

    # Create or get author
    author = Author(
        name=work_info["author"],
        description=f"Author of {work_info['title']}",
    )
    author_id = repo.insert_author(author)

    # Create or get work
    work = Work(
        author_id=author_id,
        title=work_info["title"],
        urn=work_info.get("urn"),
        priority=work_info["priority"],
    )
    work_id = repo.insert_work(work)

    return work_id


def mine_work(
    work_key: str,
    repo: Repository,
    extractor: GlossExtractor,
    passages: list[TextPassage],
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine a single work for Etruscan glosses.

    Args:
        work_key: Work identifier
        repo: Database repository
        extractor: Gloss extractor
        passages: Text passages to mine
        min_confidence: Minimum pattern confidence

    Returns:
        Tuple of (passages_scanned, candidates_found)
    """
    work_info = TARGET_WORKS[work_key]

    def iter_passages():
        for p in passages:
            yield TextItem(
                text=p.text,
                reference=p.reference,
                author=work_info["author"],
                title=work_info["title"],
                urn=work_info.get("urn", ""),
                priority=work_info["priority"],
                source_url=p.source_url or "",
            )

    return mine_texts(
        repo, extractor, iter_passages(),
        source_name=work_info["title"],
        total_count=len(passages),
        min_confidence=min_confidence,
        progress_interval=100,
    )


def mine_from_cache(
    work_key: str,
    repo: Repository,
    cache: WorkCache,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine a work from cache.

    Args:
        work_key: Work identifier
        repo: Database repository
        cache: Work cache
        extractor: Gloss extractor
        min_confidence: Minimum pattern confidence

    Returns:
        Tuple of (passages_scanned, candidates_found)
    """
    work_info = TARGET_WORKS.get(work_key)
    if not work_info:
        print(f"Unknown work: {work_key}")
        return 0, 0

    urn = work_info.get("urn")
    if not urn:
        print(f"Work {work_key} has no URN")
        return 0, 0

    passages = cache.get_work(urn)
    if not passages:
        print(f"Work {work_key} not in cache. Run download_all_texts.py first.")
        return 0, 0

    return mine_work(work_key, repo, extractor, passages, min_confidence)


def mine_github_corpus(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine the GitHub CLTK Latin Library corpus."""
    reader = GitHubCorpusReader()
    total_files = reader.count_files()

    if total_files == 0:
        print("No GitHub corpus files found. Run download_all_texts.py --github first.")
        return 0, 0

    def iter_github_texts():
        for github_text in reader.iter_texts():
            yield TextItem(
                text=github_text.text,
                reference=f"{github_text.author}/{github_text.filename}",
                author=github_text.author,
                title=github_text.title,
                urn=f"github:{github_text.filename}",
                priority="LOW",
                source_url=str(github_text.file_path),
            )

    return mine_texts(
        repo, extractor, iter_github_texts(),
        source_name="GitHub CLTK corpus",
        total_count=total_files,
        min_confidence=min_confidence,
        progress_interval=200,
    )


def mine_latin_library(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine the Latin Library cached texts."""
    client = LatinLibraryClient()
    cached_files = list(client.cache_dir.glob("*.html"))

    if not cached_files:
        print("No Latin Library cache found. Run download_all_texts.py --latin-library first.")
        return 0, 0

    def iter_latin_library():
        for cache_file in cached_files:
            text_id = cache_file.stem
            text = client.get_text(text_id)
            if text and text.text:
                yield TextItem(
                    text=text.text,
                    reference=f"{text.author}/{text.title}",
                    author=text.author,
                    title=text.title,
                    urn=f"latinlibrary:{text_id}",
                    priority="HIGH",
                    source_url=text.source_url,
                )

    return mine_texts(
        repo, extractor, iter_latin_library(),
        source_name="Latin Library",
        total_count=len(cached_files),
        min_confidence=min_confidence,
        progress_interval=20,
    )


def mine_greek_corpus(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
    work_key: str = None,
) -> tuple[int, int]:
    """Mine Greek texts from Perseus for Etruscan glosses."""
    greek_dir = CORPUS_CACHE_DIR / "greek"

    # Check for cached Greek texts first
    if greek_dir.exists():
        cached_files = list(greek_dir.glob("*.json"))
        if cached_files:
            return mine_greek_from_cache(
                repo, extractor, min_confidence, work_key
            )

    # Fall back to live download
    return mine_greek_live(repo, extractor, min_confidence, work_key)


def mine_greek_from_cache(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
    work_key: str = None,
) -> tuple[int, int]:
    """Mine Greek texts from cached JSON files."""
    greek_dir = CORPUS_CACHE_DIR / "greek"

    works_to_mine = {work_key: GREEK_WORKS[work_key]} if work_key else GREEK_WORKS

    total_scanned = 0
    total_found = 0

    for key, work_info in works_to_mine.items():
        cache_path = greek_dir / f"{key}.json"
        if not cache_path.exists():
            print(f"  {key}: not cached, skipping")
            continue

        with open(cache_path, "r", encoding="utf-8") as f:
            passages = json.load(f)

        def iter_passages():
            for p in passages:
                yield TextItem(
                    text=p["text"],
                    reference=p["reference"],
                    author=work_info["author"],
                    title=work_info["title"],
                    urn=work_info["urn"],
                    priority=work_info["priority"],
                    source_url=p.get("source_url", ""),
                    language="greek",
                )

        scanned, found = mine_texts(
            repo, extractor, iter_passages(),
            source_name=work_info["title"],
            total_count=len(passages),
            min_confidence=min_confidence,
            progress_interval=50,
        )
        total_scanned += scanned
        total_found += found

    print(f"\nGreek corpus total: Scanned {total_scanned} passages, found {total_found} candidates")
    return total_scanned, total_found


def mine_greek_live(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
    work_key: str = None,
) -> tuple[int, int]:
    """Mine Greek texts by fetching live from Perseus."""
    client = GreekCorpusClient()

    works_to_mine = {work_key: GREEK_WORKS[work_key]} if work_key else GREEK_WORKS

    total_scanned = 0
    total_found = 0

    for key, work_info in works_to_mine.items():
        print(f"\nFetching {work_info['title']} by {work_info['author']}...")

        # Fetch passages (prioritize Etruscan-relevant books)
        if key == "dionysius_ant_rom":
            passages = client.fetch_dionysius_book5()
        elif key == "strabo_geography":
            passages = client.fetch_strabo_book5()
        else:
            passages = client.fetch_work(key, max_passages=200)

        if not passages:
            print(f"  No passages fetched for {work_info['title']}")
            continue

        def iter_passages():
            for p in passages:
                yield TextItem(
                    text=p.text,
                    reference=p.reference,
                    author=work_info["author"],
                    title=work_info["title"],
                    urn=work_info["urn"],
                    priority=work_info["priority"],
                    source_url=p.source_url or "",
                    language="greek",
                )

        scanned, found = mine_texts(
            repo, extractor, iter_passages(),
            source_name=work_info["title"],
            total_count=len(passages),
            min_confidence=min_confidence,
            progress_interval=50,
        )
        total_scanned += scanned
        total_found += found

    print(f"\nGreek corpus total: Scanned {total_scanned} passages, found {total_found} candidates")
    return total_scanned, total_found


def mine_text(
    text: str,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
):
    """Mine a single text string (for testing).

    Args:
        text: Text to mine
        extractor: Gloss extractor
        min_confidence: Minimum confidence
    """
    result = extractor.extract(text)

    print(f"\nText: {text[:100]}...")
    print(f"Patterns applied: {result.patterns_applied}")
    print(f"Matches found: {len(result.matches)}")

    for match in result.matches:
        print(f"\n  Word: {match.etruscan_word}")
        print(f"  Pattern: {match.pattern_name}")
        print(f"  Confidence: {match.confidence:.2f}")
        print(f"  Full match: {match.full_match}")
        print(f"  Context: ...{match.context_before} [{match.full_match}] {match.context_after}...")


def show_candidates(repo: Repository, status: str = "pending", limit: int = 20):
    """Show candidates from database.

    Args:
        repo: Database repository
        status: Status to filter by
        limit: Maximum candidates to show
    """
    candidates = repo.get_candidates_by_status(status)

    print(f"\n{status.upper()} candidates ({len(candidates)} total, showing {min(len(candidates), limit)}):")
    print("-" * 80)

    for candidate in candidates[:limit]:
        print(f"\n  ID: {candidate.id}")
        print(f"  Word: {candidate.etruscan_word}")
        print(f"  Pattern: {candidate.pattern_confidence:.2f}")
        print(f"  Match: {candidate.full_match}")
        print(f"  Context: ...{candidate.context_before[:50]} | {candidate.context_after[:50]}...")


def main():
    parser = argparse.ArgumentParser(description="Mine Etruscan glosses from corpus texts")
    parser.add_argument(
        "--work",
        "-w",
        help="Work to mine (from TARGET_WORKS)",
    )
    parser.add_argument(
        "--corpus",
        choices=["github", "latin_library", "greek", "all"],
        help="Mine from a specific corpus source",
    )
    parser.add_argument(
        "--greek-work",
        choices=list(GREEK_WORKS.keys()),
        help="Specific Greek work to mine (use with --corpus greek)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Mine all cached works (legacy option)",
    )
    parser.add_argument(
        "--text",
        "-t",
        help="Mine a single text string (for testing)",
    )
    parser.add_argument(
        "--min-confidence",
        "-c",
        type=float,
        default=0.70,
        help="Minimum pattern confidence (default: 0.70)",
    )
    parser.add_argument(
        "--show",
        "-s",
        choices=["pending", "reviewing", "accepted", "rejected"],
        help="Show candidates by status",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show mining statistics",
    )

    args = parser.parse_args()

    repo = Repository(DB_PATH)
    cache = WorkCache()
    extractor = GlossExtractor(min_confidence=args.min_confidence)

    if args.text:
        mine_text(args.text, extractor, args.min_confidence)
        return

    if args.show:
        show_candidates(repo, args.show)
        return

    if args.stats:
        stats = repo.get_stats()
        print("\nDatabase statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count}")
        return

    if args.corpus:
        total_scanned = 0
        total_found = 0

        if args.corpus in ["github", "all"]:
            scanned, found = mine_github_corpus(repo, extractor, args.min_confidence)
            total_scanned += scanned
            total_found += found

        if args.corpus in ["latin_library", "all"]:
            scanned, found = mine_latin_library(repo, extractor, args.min_confidence)
            total_scanned += scanned
            total_found += found

        if args.corpus in ["greek", "all"]:
            scanned, found = mine_greek_corpus(
                repo, extractor, args.min_confidence, args.greek_work
            )
            total_scanned += scanned
            total_found += found

        print(f"\nTotal: Scanned {total_scanned} files, found {total_found} candidates")

    elif args.work:
        scanned, found = mine_from_cache(
            args.work, repo, cache, extractor, args.min_confidence
        )
        print(f"\nResults: Scanned {scanned} passages, found {found} candidates")

    elif args.all:
        total_scanned = 0
        total_found = 0

        for work_key, work_info in TARGET_WORKS.items():
            if work_info.get("urn"):
                scanned, found = mine_from_cache(
                    work_key, repo, cache, extractor, args.min_confidence
                )
                total_scanned += scanned
                total_found += found

        print(f"\nTotal: Scanned {total_scanned} passages, found {total_found} candidates")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
