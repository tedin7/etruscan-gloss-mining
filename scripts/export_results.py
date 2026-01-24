#!/usr/bin/env python3
"""Export mining results in various formats."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH, PROJECT_ROOT
from etruscan_miner.db.repository import Repository
from etruscan_miner.export.csv_export import CSVExporter
from etruscan_miner.export.json_export import JSONExporter
from etruscan_miner.export.markdown import MarkdownExporter


def ensure_results_dir() -> Path:
    """Ensure results directory exists."""
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def export_markdown(repo: Repository, output: Path, report_type: str):
    """Export to Markdown.

    Args:
        repo: Database repository
        output: Output path
        report_type: Type of report (glosses, candidates, report)
    """
    exporter = MarkdownExporter(repo)

    if report_type == "glosses":
        count = exporter.export_verified_glosses(output)
        print(f"Exported {count} verified glosses to {output}")
    elif report_type == "candidates":
        count = exporter.export_candidates(output)
        print(f"Exported {count} candidates to {output}")
    elif report_type == "report":
        exporter.export_findings_report(output)
        print(f"Exported findings report to {output}")
    else:
        print(f"Unknown report type: {report_type}")


def export_csv(repo: Repository, output_dir: Path, data_type: str):
    """Export to CSV.

    Args:
        repo: Database repository
        output_dir: Output directory
        data_type: Type of data (glosses, vocabulary, candidates, all)
    """
    exporter = CSVExporter(repo)

    if data_type == "all":
        results = exporter.export_all(output_dir)
        print("Exported CSV files:")
        for filename, count in results.items():
            print(f"  {filename}: {count} records")
    elif data_type == "glosses":
        output = output_dir / "verified_glosses.csv"
        count = exporter.export_verified_glosses(output)
        print(f"Exported {count} glosses to {output}")
    elif data_type == "vocabulary":
        output = output_dir / "vocabulary.csv"
        count = exporter.export_vocabulary(output)
        print(f"Exported {count} vocabulary words to {output}")
    elif data_type == "candidates":
        output = output_dir / "candidates.csv"
        count = exporter.export_candidates(output)
        print(f"Exported {count} candidates to {output}")


def export_json(repo: Repository, output: Path, data_type: str, include_validations: bool):
    """Export to JSON.

    Args:
        repo: Database repository
        output: Output path
        data_type: Type of data
        include_validations: Include validation details
    """
    exporter = JSONExporter(repo)

    if data_type == "complete":
        results = exporter.export_complete_database(output)
        print(f"Exported complete database to {output}")
        for section, count in results.items():
            print(f"  {section}: {count}")
    elif data_type == "glosses":
        count = exporter.export_verified_glosses(output)
        print(f"Exported {count} glosses to {output}")
    elif data_type == "vocabulary":
        count = exporter.export_vocabulary(output)
        print(f"Exported {count} vocabulary words to {output}")
    elif data_type == "candidates":
        count = exporter.export_candidates(output, include_validations=include_validations)
        print(f"Exported {count} candidates to {output}")
    elif data_type == "web":
        count = exporter.export_for_web(output)
        print(f"Exported {count} items for web to {output}")


def main():
    parser = argparse.ArgumentParser(description="Export mining results")
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Export format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path (file or directory depending on format)",
    )
    parser.add_argument(
        "--type",
        "-t",
        default="report",
        help="Data type: glosses, vocabulary, candidates, report, complete, web, all",
    )
    parser.add_argument(
        "--include-validations",
        action="store_true",
        help="Include validation details (JSON only)",
    )

    args = parser.parse_args()

    repo = Repository(DB_PATH)
    results_dir = ensure_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine output path
    if args.output:
        output = Path(args.output)
    else:
        if args.format == "markdown":
            output = results_dir / f"{args.type}_{timestamp}.md"
        elif args.format == "csv":
            output = results_dir
        elif args.format == "json":
            output = results_dir / f"{args.type}_{timestamp}.json"

    # Export
    if args.format == "markdown":
        export_markdown(repo, output, args.type)
    elif args.format == "csv":
        export_csv(repo, output, args.type)
    elif args.format == "json":
        export_json(repo, output, args.type, args.include_validations)

    # Show stats
    print("\nDatabase statistics:")
    stats = repo.get_stats()
    for table, count in stats.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    main()
