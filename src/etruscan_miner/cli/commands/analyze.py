"""Analyze Etruscan candidates with unified 9-method scoring.

This command merges the functionality of the old `validate` and `verify` commands
into a unified analysis interface with all 9 validation methods:

1. Pattern - confidence from pattern matching
2. Cross-reference - matches against known vocabulary
3. Linguistic - Etruscan phonotactic rules
4. Phonotactic - fingerprinting for substrate detection
5. Context - contextual coherence (rule-based or ML)
6. Inscription - matches against CIEW corpus
7. Semantic - domain classification
8. Lemnian - parallels with Lemnian
9. Raetic - parallels with Raetic inscriptions
"""

import json
import click
from pathlib import Path
from typing import Optional

from ...config import DB_PATH
from ...db.repository import Repository
from ...validation.unified import UnifiedValidator, UnifiedScore
from ..utils import print_stats


@click.command()
@click.option("--word", "-w", help="Analyze a single word")
@click.option("--status", "-s", type=click.Choice(["pending", "reviewing", "accepted", "rejected"]),
              default="pending", help="Analyze candidates by status (default: pending)")
@click.option("--limit", "-l", type=int, default=50, help="Maximum candidates to process")
@click.option("--min-score", type=float, default=0.0,
              help="Only show candidates above this score")
@click.option("--methods-required", type=int, default=0,
              help="Require at least N methods to confirm")
@click.option("--use-ml", is_flag=True,
              help="Enable ML-based classifiers (requires trained models)")
@click.option("--report", "-r", is_flag=True, help="Generate comprehensive report")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              help="Output file for results (JSON)")
@click.option("--show-accepted", is_flag=True, help="Show accepted candidates")
@click.option("--show-review", is_flag=True, help="Show candidates needing review")
@click.option("--stats", is_flag=True, help="Show analysis statistics")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze(word: str, status: str, limit: int, min_score: float,
            methods_required: int, use_ml: bool, report: bool, output: Path,
            show_accepted: bool, show_review: bool, stats: bool, verbose: bool):
    """Analyze candidates with unified 9-method scoring.

    Applies all validation methods to score candidates and provide
    recommendations (accept/review/reject).

    \b
    Examples:
        etruscan analyze --word harena
        etruscan analyze --status pending --limit 20
        etruscan analyze --report --use-ml
        etruscan analyze --methods-required 2
    """
    if not DB_PATH.exists():
        raise click.ClickException("Database not found. Run 'etruscan db setup' first.")

    repo = Repository(DB_PATH)

    if stats:
        print_stats(repo.get_stats())
        return

    if show_accepted:
        _show_by_status(repo, "accepted", limit)
        return

    if show_review:
        _show_by_status(repo, "reviewing", limit)
        return

    # Initialize unified validator
    validator = UnifiedValidator(repo, use_ml=use_ml)

    if validator.warnings:
        click.echo("Initialization warnings:")
        for warning in validator.warnings:
            click.echo(f"  - {warning}")

    # Single word analysis
    if word:
        _analyze_word(word, validator, verbose)
        return

    # Report mode
    if report:
        _generate_report(repo, validator, limit, output)
        return

    # Batch analysis of candidates
    candidates = repo.get_candidates_by_status(status)[:limit]

    if not candidates:
        click.echo(f"No {status} candidates to analyze.")
        return

    click.echo(f"\nAnalyzing {len(candidates)} {status} candidates...")
    click.echo("=" * 80)

    results = []
    for candidate in candidates:
        context = f"{candidate.context_before or ''} {candidate.full_match or ''} {candidate.context_after or ''}"
        score = validator.validate(
            candidate.etruscan_word,
            context,
            candidate.pattern_confidence or 0.5
        )
        results.append((candidate, score))

    # Filter by min_score and methods_required
    if min_score > 0:
        results = [(c, s) for c, s in results if s.final_score >= min_score]

    if methods_required > 0:
        results = [(c, s) for c, s in results if s.methods_confirmed >= methods_required]

    # Sort by score descending
    results.sort(key=lambda x: x[1].final_score, reverse=True)

    # Display results
    for candidate, score in results[:20]:
        _print_score(candidate.etruscan_word, score, verbose)

        # Update candidate status based on recommendation
        if score.recommendation == "accept" and candidate.status == "pending":
            notes = f"Auto-score: {score.final_score:.2f}, methods={score.methods_confirmed}"
            repo.update_candidate_status(candidate.id, "reviewing", notes)
        elif score.recommendation == "reject" and score.final_score < 0.3:
            notes = f"Low score: {score.final_score:.2f}"
            repo.update_candidate_status(candidate.id, "rejected", notes)

    # Print summary
    all_scores = [s for _, s in results]
    summary = validator.get_summary(all_scores)

    click.echo("\n" + "=" * 80)
    click.echo("SUMMARY")
    click.echo("=" * 80)
    click.echo(f"Analyzed: {summary['count']}")
    click.echo(f"Avg Score: {summary.get('avg_score', 0):.2f}")
    click.echo(f"High confidence: {summary['high_confidence']}")
    click.echo(f"Medium confidence: {summary['medium_confidence']}")
    click.echo(f"Low confidence: {summary['low_confidence']}")
    click.echo(f"Multi-method (2+): {summary['multi_method']}")
    click.echo(f"Recommendations: Accept={summary['recommendations']['accept']}, "
              f"Review={summary['recommendations']['review']}, "
              f"Reject={summary['recommendations']['reject']}")

    if output:
        _save_results(output, results)
        click.echo(f"\nResults saved to: {output}")


def _analyze_word(word: str, validator: UnifiedValidator, verbose: bool):
    """Analyze a single word interactively."""
    click.echo(f"\n{'='*60}")
    click.echo(f"ANALYZING: {word.upper()}")
    click.echo(f"{'='*60}")

    score = validator.validate(word)

    click.echo(f"\nFinal Score: {score.final_score:.2f}")
    click.echo(f"Confidence: {score.confidence_level.upper()}")
    click.echo(f"Recommendation: {score.recommendation.upper()}")
    click.echo(f"Methods confirmed: {score.methods_confirmed}/9")

    if score.known_loan:
        click.echo("\nStatus: KNOWN ETRUSCAN LOAN")

    click.echo(f"\n{'='*60}")
    click.echo("COMPONENT SCORES")
    click.echo(f"{'='*60}")

    scores_table = [
        ("Pattern", score.pattern_score),
        ("Cross-Reference", score.cross_ref_score),
        ("Linguistic", score.linguistic_score),
        ("Phonotactic", score.phonotactic_score),
        ("Context", score.context_score),
        ("Inscription", score.inscription_score),
        ("Semantic", score.semantic_score),
        ("Lemnian", score.lemnian_score),
        ("Raetic", score.raetic_score),
    ]

    for name, value in scores_table:
        bar = "#" * int(value * 20) + "-" * (20 - int(value * 20))
        status = "OK" if value >= 0.5 else "  "
        click.echo(f"  {name:15} [{bar}] {value:.2f} {status}")

    confirmed = score.get_confirmed_methods()
    if confirmed:
        click.echo(f"\nConfirmed by: {', '.join(confirmed)}")

    if verbose or score.methods_confirmed > 0:
        click.echo(f"\n{'='*60}")
        click.echo("DETAILS")
        click.echo(f"{'='*60}")

        if score.cross_ref_match:
            click.echo(f"  Cross-Reference: {score.cross_ref_match} = '{score.cross_ref_meaning}'")
            click.echo(f"    Match type: {score.cross_ref_type}")

        if score.inscription_match:
            click.echo(f"  Inscription: {score.inscription_match} = '{score.inscription_meaning}'")
            if score.inscription_domain:
                click.echo(f"    Domain: {score.inscription_domain}")

        if score.semantic_domain:
            click.echo(f"  Semantic: domain={score.semantic_domain}, prob={score.semantic_probability:.2f}")

        if score.lemnian_parallel:
            click.echo(f"  Lemnian: parallel={score.lemnian_parallel}")

        if score.raetic_parallel:
            click.echo(f"  Raetic: parallel={score.raetic_parallel}")

        if score.phonotactic_features:
            click.echo(f"  Phonotactic features: {', '.join(score.phonotactic_features[:5])}")

        if score.linguistic_positives:
            click.echo(f"  Linguistic positives: {', '.join(score.linguistic_positives[:3])}")

        if score.linguistic_issues:
            click.echo(f"  Linguistic issues: {', '.join(score.linguistic_issues[:3])}")


def _print_score(word: str, score: UnifiedScore, verbose: bool):
    """Print a single score result."""
    click.echo(f"\n{word}")
    click.echo(f"  Score: {score.final_score:.2f} ({score.confidence_level})")
    click.echo(f"  Methods: {score.methods_confirmed}/9 confirmed")

    if verbose:
        click.echo(f"  Pattern: {score.pattern_score:.2f} | "
                  f"CrossRef: {score.cross_ref_score:.2f} | "
                  f"Ling: {score.linguistic_score:.2f} | "
                  f"Phono: {score.phonotactic_score:.2f}")
        click.echo(f"  Context: {score.context_score:.2f} | "
                  f"Inscr: {score.inscription_score:.2f} | "
                  f"Sem: {score.semantic_score:.2f} | "
                  f"Lem: {score.lemnian_score:.2f} | "
                  f"Rae: {score.raetic_score:.2f}")

    confirmed = score.get_confirmed_methods()
    if confirmed:
        click.echo(f"  Confirmed by: {', '.join(confirmed)}")

    click.echo(f"  Recommendation: {score.recommendation.upper()}")

    if score.ml_rejection_reason:
        click.echo(f"  ML Rejection: {score.ml_rejection_reason}")


def _show_by_status(repo: Repository, status: str, limit: int):
    """Show candidates by status."""
    candidates = repo.get_candidates_by_status(status)[:limit]

    click.echo(f"\n{'='*60}")
    click.echo(f"{status.upper()} Candidates ({len(candidates)} total)")
    click.echo(f"{'='*60}")

    for c in candidates:
        click.echo(f"\n  {c.etruscan_word}")
        click.echo(f"    Pattern confidence: {c.pattern_confidence:.2f}")
        click.echo(f"    Match: {c.full_match}")
        if c.reviewer_notes:
            click.echo(f"    Notes: {c.reviewer_notes}")


def _generate_report(repo: Repository, validator: UnifiedValidator, limit: int, output: Optional[Path]):
    """Generate comprehensive verification report."""
    click.echo("\n" + "=" * 70)
    click.echo("COMPREHENSIVE ANALYSIS REPORT")
    click.echo("=" * 70)

    # Analyze all status types
    all_results = []

    for status in ["pending", "reviewing", "accepted"]:
        candidates = repo.get_candidates_by_status(status)[:limit]
        for candidate in candidates:
            context = f"{candidate.context_before or ''} {candidate.full_match or ''} {candidate.context_after or ''}"
            score = validator.validate(
                candidate.etruscan_word,
                context,
                candidate.pattern_confidence or 0.5
            )
            all_results.append((candidate, score, status))

    # Categorize results
    multi_method_new = [(c, s) for c, s, st in all_results
                        if s.methods_confirmed >= 2 and not s.known_loan]
    multi_method_known = [(c, s) for c, s, st in all_results
                          if s.methods_confirmed >= 2 and s.known_loan]
    single_method = [(c, s) for c, s, st in all_results
                     if s.methods_confirmed == 1]
    no_confirmation = [(c, s) for c, s, st in all_results
                       if s.methods_confirmed == 0]

    click.echo(f"\nMULTI-METHOD NEW DISCOVERIES ({len(multi_method_new)})")
    click.echo("-" * 70)

    for candidate, score in sorted(multi_method_new, key=lambda x: x[1].final_score, reverse=True)[:25]:
        click.echo(f"\n  {candidate.etruscan_word.upper():20} [{score.methods_confirmed} methods] "
                  f"score={score.final_score:.2f}")
        click.echo(f"    Methods: {', '.join(score.get_confirmed_methods())}")

        if score.inscription_match:
            click.echo(f"    Inscription: {score.inscription_match} = '{score.inscription_meaning}'")
        if score.lemnian_parallel:
            click.echo(f"    Lemnian: {score.lemnian_parallel}")
        if score.raetic_parallel:
            click.echo(f"    Raetic: {score.raetic_parallel}")

    click.echo(f"\n\nKNOWN LOANS VALIDATED ({len(multi_method_known)})")
    click.echo("-" * 70)

    for candidate, score in sorted(multi_method_known, key=lambda x: x[1].final_score, reverse=True)[:10]:
        click.echo(f"  {candidate.etruscan_word:20} [{score.methods_confirmed} methods] "
                  f"{', '.join(score.get_confirmed_methods())}")

    # Summary statistics
    click.echo("\n\n" + "=" * 70)
    click.echo("SUMMARY STATISTICS")
    click.echo("=" * 70)
    click.echo(f"  Total analyzed: {len(all_results)}")
    click.echo(f"  Multi-method (2+): {len(multi_method_new) + len(multi_method_known)}")
    click.echo(f"    - Known loans validated: {len(multi_method_known)}")
    click.echo(f"    - Potentially NEW: {len(multi_method_new)}")
    click.echo(f"  Single-method: {len(single_method)}")
    click.echo(f"  No confirmation: {len(no_confirmation)}")

    # Method hit rates
    click.echo("\n  Method hit rates:")
    method_counts = {
        "PATTERN": 0, "CROSS_REF": 0, "LINGUISTIC": 0,
        "PHONOTACTIC": 0, "CONTEXT": 0, "INSCRIPTION": 0,
        "SEMANTIC": 0, "LEMNIAN": 0, "RAETIC": 0,
    }

    for _, score, _ in all_results:
        for method in score.get_confirmed_methods():
            method_counts[method] = method_counts.get(method, 0) + 1

    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        click.echo(f"    {method:12}: {count} hits")

    # Save to file if requested
    if output:
        output_data = {
            "summary": {
                "total_analyzed": len(all_results),
                "multi_method_new": len(multi_method_new),
                "multi_method_known": len(multi_method_known),
                "single_method": len(single_method),
                "no_confirmation": len(no_confirmation),
            },
            "method_counts": method_counts,
            "candidates": [
                {
                    "word": c.etruscan_word,
                    "status": st,
                    **s.to_dict(),
                }
                for c, s, st in all_results
                if s.methods_confirmed >= 2
            ],
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)
        click.echo(f"\nReport saved to: {output}")


def _save_results(output: Path, results: list[tuple]):
    """Save analysis results to JSON file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "candidates": [
            {
                "word": candidate.etruscan_word,
                "pattern_match": candidate.full_match,
                **score.to_dict(),
            }
            for candidate, score in results
        ]
    }

    with open(output, 'w') as f:
        json.dump(output_data, f, indent=2)
