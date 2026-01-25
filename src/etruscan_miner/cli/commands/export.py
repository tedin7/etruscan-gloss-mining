"""Export results command."""

import click
from datetime import datetime
from pathlib import Path

from ...config import DB_PATH, PROJECT_ROOT
from ...db.repository import Repository
from ...export.csv_export import CSVExporter
from ...export.json_export import JSONExporter
from ...export.markdown import MarkdownExporter
from ..utils import print_stats


@click.command()
@click.option("--format", "-f", "output_format",
              type=click.Choice(["markdown", "csv", "json"]),
              default="markdown", help="Export format (default: markdown)")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              help="Output path (file or directory depending on format)")
@click.option("--type", "-t", "data_type", default="report",
              help="Data type: glosses, vocabulary, candidates, report, complete, web, all")
@click.option("--include-validations", is_flag=True,
              help="Include validation details (JSON only)")
def export(output_format: str, output: Path, data_type: str, include_validations: bool):
    """Export mining results in various formats.

    \b
    Data types:
      glosses     - Verified glosses
      vocabulary  - Known vocabulary
      candidates  - All candidates
      report      - Findings report (markdown)
      complete    - Complete database (JSON)
      web         - Web-friendly format (JSON)
      all         - All data (CSV)
    """
    if not DB_PATH.exists():
        raise click.ClickException("Database not found. Run 'etruscan db setup' first.")

    repo = Repository(DB_PATH)
    results_dir = _ensure_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        if output_format == "markdown":
            output_path = results_dir / f"{data_type}_{timestamp}.md"
        elif output_format == "csv":
            output_path = results_dir
        elif output_format == "json":
            output_path = results_dir / f"{data_type}_{timestamp}.json"

    # Export
    if output_format == "markdown":
        _export_markdown(repo, output_path, data_type)
    elif output_format == "csv":
        _export_csv(repo, output_path, data_type)
    elif output_format == "json":
        _export_json(repo, output_path, data_type, include_validations)

    # Show stats
    print_stats(repo.get_stats())


def _ensure_results_dir() -> Path:
    """Ensure results directory exists."""
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def _export_markdown(repo: Repository, output: Path, report_type: str):
    """Export to Markdown."""
    exporter = MarkdownExporter(repo)

    if report_type == "glosses":
        count = exporter.export_verified_glosses(output)
        click.echo(f"Exported {count} verified glosses to {output}")
    elif report_type == "candidates":
        count = exporter.export_candidates(output)
        click.echo(f"Exported {count} candidates to {output}")
    elif report_type == "report":
        exporter.export_findings_report(output)
        click.echo(f"Exported findings report to {output}")
    else:
        click.echo(f"Unknown report type: {report_type}")


def _export_csv(repo: Repository, output_dir: Path, data_type: str):
    """Export to CSV."""
    exporter = CSVExporter(repo)

    if data_type == "all":
        results = exporter.export_all(output_dir)
        click.echo("Exported CSV files:")
        for filename, count in results.items():
            click.echo(f"  {filename}: {count} records")
    elif data_type == "glosses":
        output = output_dir / "verified_glosses.csv"
        count = exporter.export_verified_glosses(output)
        click.echo(f"Exported {count} glosses to {output}")
    elif data_type == "vocabulary":
        output = output_dir / "vocabulary.csv"
        count = exporter.export_vocabulary(output)
        click.echo(f"Exported {count} vocabulary words to {output}")
    elif data_type == "candidates":
        output = output_dir / "candidates.csv"
        count = exporter.export_candidates(output)
        click.echo(f"Exported {count} candidates to {output}")


def _export_json(repo: Repository, output: Path, data_type: str, include_validations: bool):
    """Export to JSON."""
    exporter = JSONExporter(repo)

    if data_type == "complete":
        results = exporter.export_complete_database(output)
        click.echo(f"Exported complete database to {output}")
        for section, count in results.items():
            click.echo(f"  {section}: {count}")
    elif data_type == "glosses":
        count = exporter.export_verified_glosses(output)
        click.echo(f"Exported {count} glosses to {output}")
    elif data_type == "vocabulary":
        count = exporter.export_vocabulary(output)
        click.echo(f"Exported {count} vocabulary words to {output}")
    elif data_type == "candidates":
        count = exporter.export_candidates(output, include_validations=include_validations)
        click.echo(f"Exported {count} candidates to {output}")
    elif data_type == "web":
        count = exporter.export_for_web(output)
        click.echo(f"Exported {count} items for web to {output}")
