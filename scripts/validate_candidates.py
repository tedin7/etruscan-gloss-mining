#!/usr/bin/env python3
"""Validate candidate glosses using the validation pipeline."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH
from etruscan_miner.db.repository import Repository
from etruscan_miner.validation.cross_reference import CrossReferenceChecker
from etruscan_miner.validation.linguistic import LinguisticValidator
from etruscan_miner.validation.scorer import ValidationPipeline


def validate_word(word: str, repo: Repository):
    """Validate a single word interactively.

    Args:
        word: Word to validate
        repo: Database repository
    """
    cross_ref = CrossReferenceChecker(repo)
    linguistic = LinguisticValidator()

    print(f"\n{'='*60}")
    print(f"Validating: {word}")
    print(f"{'='*60}")

    # Cross-reference
    cr_result = cross_ref.check(word)
    print(f"\nCross-Reference:")
    print(f"  Score: {cr_result.score:.2f}")
    print(f"  Match type: {cr_result.match_type}")
    if cr_result.matched_word:
        print(f"  Matched: {cr_result.matched_word} = '{cr_result.matched_meaning}'")
    print(f"  Details: {cr_result.details}")

    # Linguistic
    ling_result = linguistic.validate(word)
    print(f"\nLinguistic Plausibility:")
    print(f"  Score: {ling_result.score:.2f}")
    print(f"  Plausibility: {ling_result.plausibility}")
    if ling_result.positive_features:
        print(f"  Positives: {', '.join(ling_result.positive_features)}")
    if ling_result.issues:
        print(f"  Issues: {', '.join(ling_result.issues)}")

    # Combined score (without pattern/context)
    combined = (cr_result.score * 0.5) + (ling_result.score * 0.5)
    print(f"\nCombined Score: {combined:.2f}")
    if combined >= 0.7:
        print("  Verdict: LIKELY ETRUSCAN")
    elif combined >= 0.5:
        print("  Verdict: POSSIBLY ETRUSCAN")
    else:
        print("  Verdict: UNLIKELY ETRUSCAN")


def validate_pending(repo: Repository, limit: int = 100, status: str = "pending"):
    """Validate pending candidates.

    Args:
        repo: Database repository
        limit: Maximum candidates to process
        status: Status to filter by
    """
    pipeline = ValidationPipeline(repo)

    if status == "pending":
        print(f"\nValidating up to {limit} pending candidates...")
        results = pipeline.validate_pending(limit)
    else:
        candidates = repo.get_candidates_by_status(status)[:limit]
        results = [pipeline.validate_candidate(c) for c in candidates]

    if not results:
        print("No candidates to validate.")
        return

    # Print results
    print(f"\n{'='*80}")
    print(f"Validated {len(results)} candidates")
    print(f"{'='*80}")

    # Sort by overall score descending
    results.sort(key=lambda x: x.overall_score, reverse=True)

    for result in results[:20]:  # Show top 20
        print(f"\n{result.word}")
        print(f"  Overall: {result.overall_score:.2f} ({result.confidence_level})")
        print(f"  Pattern: {result.pattern_score:.2f} | "
              f"CrossRef: {result.cross_ref_score:.2f} | "
              f"Linguistic: {result.linguistic_score:.2f} | "
              f"Context: {result.context_score:.2f}")
        print(f"  Recommendation: {result.recommendation.upper()}")
        if result.cross_ref_result and result.cross_ref_result.matched_word:
            print(f"  Match: {result.cross_ref_result.matched_word} "
                  f"({result.cross_ref_result.match_type})")

    # Print summary
    summary = pipeline.get_summary(results)
    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")
    print(f"Total: {summary['count']}")
    print(f"Avg Overall Score: {summary['avg_overall']:.2f}")
    print(f"Confidence levels: High={summary['high_confidence']}, "
          f"Medium={summary['medium_confidence']}, "
          f"Low={summary['low_confidence']}")
    print(f"Recommendations: Accept={summary['recommendations']['accept']}, "
          f"Review={summary['recommendations']['review']}, "
          f"Reject={summary['recommendations']['reject']}")


def show_accepted(repo: Repository, limit: int = 50):
    """Show accepted candidates.

    Args:
        repo: Database repository
        limit: Maximum to show
    """
    candidates = repo.get_candidates_by_status("accepted")[:limit]

    print(f"\n{'='*60}")
    print(f"Accepted Candidates ({len(candidates)} total)")
    print(f"{'='*60}")

    for c in candidates:
        print(f"\n  {c.etruscan_word}")
        print(f"    Pattern confidence: {c.pattern_confidence:.2f}")
        print(f"    Match: {c.full_match}")
        if c.reviewer_notes:
            print(f"    Notes: {c.reviewer_notes}")


def show_for_review(repo: Repository, limit: int = 50):
    """Show candidates needing review.

    Args:
        repo: Database repository
        limit: Maximum to show
    """
    candidates = repo.get_candidates_by_status("reviewing")[:limit]

    print(f"\n{'='*60}")
    print(f"Candidates for Review ({len(candidates)} total)")
    print(f"{'='*60}")

    for c in candidates:
        print(f"\n  ID={c.id}: {c.etruscan_word}")
        print(f"    Pattern: {c.pattern_confidence:.2f}")
        print(f"    Match: {c.full_match}")
        print(f"    Context: ...{c.context_before[:40]} | {c.context_after[:40]}...")


def main():
    parser = argparse.ArgumentParser(description="Validate candidate glosses")
    parser.add_argument(
        "--word",
        "-w",
        help="Validate a single word",
    )
    parser.add_argument(
        "--status",
        "-s",
        choices=["pending", "reviewing", "accepted", "rejected"],
        default="pending",
        help="Status to validate (default: pending)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum candidates to process",
    )
    parser.add_argument(
        "--show-accepted",
        action="store_true",
        help="Show accepted candidates",
    )
    parser.add_argument(
        "--show-review",
        action="store_true",
        help="Show candidates needing review",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show validation statistics",
    )

    args = parser.parse_args()

    repo = Repository(DB_PATH)

    if args.word:
        validate_word(args.word, repo)
    elif args.show_accepted:
        show_accepted(repo, args.limit)
    elif args.show_review:
        show_for_review(repo, args.limit)
    elif args.stats:
        stats = repo.get_stats()
        print("\nDatabase statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count}")
    else:
        validate_pending(repo, args.limit, args.status)


if __name__ == "__main__":
    main()
