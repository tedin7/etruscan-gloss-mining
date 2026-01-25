"""Unified CLI for Etruscan Miner.

Usage:
    etruscan <command> [options]

Commands:
    db        Database operations (setup, stats, reset, import-seeds)
    corpus    Download and manage corpus texts
    find      Find Etruscan candidates in texts (patterns + advanced discovery)
    analyze   Analyze candidates with unified 9-method scoring
    train     Train ML models
    export    Export results
"""

import click

from .commands import analyze, corpus, db, export, find, train


@click.group()
@click.version_option(version="0.1.0", prog_name="etruscan")
def cli():
    """Etruscan word discovery and analysis toolkit.

    Find Etruscan glosses from ancient Latin and Greek texts using pattern
    matching, then analyze candidates against known vocabulary, inscriptions,
    and cross-linguistic parallels.
    """
    pass


# Register command groups
cli.add_command(db.db)
cli.add_command(corpus.corpus)
cli.add_command(find.find)
cli.add_command(analyze.analyze)
cli.add_command(train.train)
cli.add_command(export.export)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
