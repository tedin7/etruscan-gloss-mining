#!/usr/bin/env python3
"""Interactive CLI tool for labeling candidate glosses.

This tool allows human annotators to label candidates as Etruscan or Latin
to create training data for the context classifier (Layer 3).

Usage:
    python scripts/label_candidates.py                    # Label all unlabeled
    python scripts/label_candidates.py --sample 50        # Label 50 candidates
    python scripts/label_candidates.py --status pending   # Only pending candidates
    python scripts/label_candidates.py --stats            # Show labeling statistics
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DATA_DIR, DB_PATH
from etruscan_miner.db.repository import Repository

# Output file for labeled data
LABELED_FILE = DATA_DIR / "labeled_candidates.json"


def load_labeled_data() -> list[dict]:
    """Load existing labeled candidates from JSON file."""
    if LABELED_FILE.exists():
        with open(LABELED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_labeled_data(data: list[dict]) -> None:
    """Save labeled candidates to JSON file."""
    with open(LABELED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_labeled_words(labeled_data: list[dict]) -> set[str]:
    """Get set of words that have already been labeled."""
    return {item["word"] for item in labeled_data}


def format_context(context_before: str, full_match: str, context_after: str) -> str:
    """Format context with the match highlighted."""
    before = (context_before or "").strip()
    after = (context_after or "").strip()
    match = (full_match or "").strip()

    # Truncate long contexts
    max_context = 80
    if len(before) > max_context:
        before = "..." + before[-max_context:]
    if len(after) > max_context:
        after = after[:max_context] + "..."

    return f"{before} [[ {match} ]] {after}"


def display_candidate(candidate, index: int, total: int) -> None:
    """Display a candidate for labeling."""
    print("\n" + "=" * 70)
    print(f"Candidate {index}/{total}")
    print("=" * 70)
    print(f"\nWord: {candidate.etruscan_word}")
    if candidate.meaning_proposed:
        print(f"Proposed meaning: {candidate.meaning_proposed}")
    print(f"Pattern confidence: {candidate.pattern_confidence:.2f}" if candidate.pattern_confidence else "")
    print(f"\nContext:")
    print(format_context(
        candidate.context_before,
        candidate.full_match,
        candidate.context_after
    ))
    print()


def prompt_label() -> Optional[str]:
    """Prompt user for label. Returns 'etruscan', 'latin', or None for skip/quit."""
    print("[E]truscan / [L]atin / [S]kip / [Q]uit")
    while True:
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            return None

        if choice in ("e", "etruscan"):
            return "etruscan"
        elif choice in ("l", "latin"):
            return "latin"
        elif choice in ("s", "skip"):
            return "skip"
        elif choice in ("q", "quit"):
            return None
        else:
            print("Invalid choice. Enter E, L, S, or Q.")


def label_candidates(
    repo: Repository,
    sample_size: Optional[int] = None,
    status: str = "pending"
) -> None:
    """Interactive labeling session.

    Args:
        repo: Database repository
        sample_size: Number of candidates to label (None = all)
        status: Status filter for candidates
    """
    # Load existing labeled data
    labeled_data = load_labeled_data()
    already_labeled = get_labeled_words(labeled_data)

    # Get candidates from database
    all_candidates = repo.get_candidates_by_status(status)

    # Filter out already labeled
    candidates = [c for c in all_candidates if c.etruscan_word not in already_labeled]

    if not candidates:
        if already_labeled:
            print(f"\nAll {len(all_candidates)} candidates have been labeled.")
        else:
            print(f"\nNo candidates found with status '{status}'.")
        return

    # Apply sample limit
    if sample_size and sample_size < len(candidates):
        candidates = candidates[:sample_size]

    total = len(candidates)
    labeled_count = 0
    skipped_count = 0

    print(f"\nLabeling session started.")
    print(f"Previously labeled: {len(already_labeled)}")
    print(f"Candidates to label: {total}")
    print("\nPress Ctrl+C at any time to save and exit.\n")

    try:
        for i, candidate in enumerate(candidates, 1):
            display_candidate(candidate, i, total)

            label = prompt_label()

            if label is None:
                # Quit
                print("\nQuitting...")
                break
            elif label == "skip":
                skipped_count += 1
                continue
            else:
                # Record the label
                labeled_entry = {
                    "word": candidate.etruscan_word,
                    "context_before": candidate.context_before or "",
                    "context_after": candidate.context_after or "",
                    "full_match": candidate.full_match or "",
                    "label": label,
                    "labeled_at": datetime.now().isoformat(),
                    "candidate_id": candidate.id,
                    "pattern_confidence": candidate.pattern_confidence,
                }
                labeled_data.append(labeled_entry)
                labeled_count += 1

                # Save after each label (for safety)
                save_labeled_data(labeled_data)

                print(f"Labeled as: {label.upper()}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")

    finally:
        # Save final state
        save_labeled_data(labeled_data)

        # Print summary
        print("\n" + "=" * 70)
        print("Session Summary")
        print("=" * 70)
        print(f"Labeled this session: {labeled_count}")
        print(f"Skipped this session: {skipped_count}")
        print(f"Total labeled: {len(labeled_data)}")
        print(f"Saved to: {LABELED_FILE}")


def show_stats() -> None:
    """Show labeling statistics."""
    labeled_data = load_labeled_data()

    if not labeled_data:
        print("\nNo labeled data yet. Run without --stats to start labeling.")
        return

    # Count labels
    etruscan_count = sum(1 for item in labeled_data if item["label"] == "etruscan")
    latin_count = sum(1 for item in labeled_data if item["label"] == "latin")

    print("\n" + "=" * 50)
    print("Labeling Statistics")
    print("=" * 50)
    print(f"Total labeled:   {len(labeled_data)}")
    print(f"  Etruscan:      {etruscan_count} ({100*etruscan_count/len(labeled_data):.1f}%)")
    print(f"  Latin:         {latin_count} ({100*latin_count/len(labeled_data):.1f}%)")
    print(f"\nData file: {LABELED_FILE}")

    # Show some examples
    print("\nRecent labels:")
    for item in labeled_data[-5:]:
        print(f"  {item['word']:20} -> {item['label']}")


def show_progress(repo: Repository) -> None:
    """Show progress toward labeling goal."""
    labeled_data = load_labeled_data()
    all_candidates = repo.get_candidates_by_status("pending")

    labeled_words = get_labeled_words(labeled_data)
    remaining = sum(1 for c in all_candidates if c.etruscan_word not in labeled_words)

    print(f"\nProgress: {len(labeled_data)} labeled, {remaining} remaining")

    if labeled_data:
        etruscan = sum(1 for d in labeled_data if d["label"] == "etruscan")
        latin = sum(1 for d in labeled_data if d["label"] == "latin")
        print(f"Balance: {etruscan} Etruscan, {latin} Latin")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive tool for labeling candidate glosses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/label_candidates.py                  # Label all unlabeled candidates
  python scripts/label_candidates.py --sample 50      # Label 50 candidates
  python scripts/label_candidates.py --status reviewing  # Label candidates in review
  python scripts/label_candidates.py --stats          # Show statistics
        """
    )
    parser.add_argument(
        "--sample", "-n",
        type=int,
        help="Number of candidates to label (default: all unlabeled)",
    )
    parser.add_argument(
        "--status", "-s",
        choices=["pending", "reviewing", "accepted", "rejected"],
        default="pending",
        help="Status of candidates to label (default: pending)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show labeling statistics and exit",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show labeling progress and exit",
    )

    args = parser.parse_args()

    # Check database exists
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run 'python scripts/setup_database.py' first.")
        sys.exit(1)

    repo = Repository(DB_PATH)

    if args.stats:
        show_stats()
    elif args.progress:
        show_progress(repo)
    else:
        label_candidates(repo, args.sample, args.status)


if __name__ == "__main__":
    main()
