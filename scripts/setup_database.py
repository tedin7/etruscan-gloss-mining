#!/usr/bin/env python3
"""Initialize the Etruscan gloss mining database."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH, DATA_DIR
from etruscan_miner.db.repository import Repository


def setup_database():
    """Create the database and initialize schema."""
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Read schema
    schema_path = Path(__file__).parent.parent / "src" / "etruscan_miner" / "db" / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()

    # Create database
    repo = Repository(DB_PATH)
    with repo.connection() as conn:
        conn.executescript(schema_sql)

    print(f"Database created at: {DB_PATH}")

    # Verify
    stats = repo.get_stats()
    print("\nInitial statistics:")
    for table, count in stats.items():
        print(f"  {table}: {count}")

    # Show patterns loaded
    patterns = repo.get_active_patterns()
    print(f"\nLoaded {len(patterns)} patterns:")
    for p in patterns:
        print(f"  - {p.name}: {p.description}")


if __name__ == "__main__":
    setup_database()
