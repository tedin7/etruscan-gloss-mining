#!/usr/bin/env python3
"""Mine glosses from corpus texts using pattern matching."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH, TARGET_WORKS
from etruscan_miner.corpus.perseus import PerseusClient, TextPassage
from etruscan_miner.corpus.text_cache import WorkCache
from etruscan_miner.db.models import Author, Candidate, Passage, Work
from etruscan_miner.db.repository import Repository
from etruscan_miner.patterns.extractor import GlossExtractor


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
    work_id = ensure_work_in_db(repo, work_key)
    work_info = TARGET_WORKS[work_key]

    # Start mining run
    run_id = repo.start_mining_run(work_id=work_id, pattern_id=None)

    candidates_found = 0
    passages_scanned = 0

    print(f"\nMining {work_info['title']}...")
    print(f"  Passages: {len(passages)}")

    for i, text_passage in enumerate(passages):
        passages_scanned += 1

        # Extract glosses
        result = extractor.extract(text_passage.text)

        if result.found_glosses:
            # Store passage
            db_passage = Passage(
                work_id=work_id,
                reference=text_passage.reference,
                text_latin=text_passage.text,
                text_normalized=text_passage.text.lower(),
                source_url=text_passage.source_url,
            )
            passage_id = repo.insert_passage(db_passage)

            # Store each candidate
            for match in result.get_high_confidence_matches(min_confidence):
                candidate = Candidate(
                    passage_id=passage_id,
                    mining_run_id=run_id,
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
                candidates_found += 1

        if (i + 1) % 100 == 0:
            print(f"  Scanned {i + 1}/{len(passages)} passages, found {candidates_found} candidates")

    # Complete mining run
    repo.complete_mining_run(run_id, passages_scanned, candidates_found)

    return passages_scanned, candidates_found


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
        print(f"Work {work_key} not in cache. Run download_corpus.py first.")
        return 0, 0

    return mine_work(work_key, repo, extractor, passages, min_confidence)


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
        "--all",
        "-a",
        action="store_true",
        help="Mine all cached works",
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

    if args.work:
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
