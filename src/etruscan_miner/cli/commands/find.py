"""Find Etruscan candidates in texts.

This command merges the functionality of the old `mine` and `discover` commands
into a unified interface for extracting Etruscan word candidates.

Modes:
- Basic pattern matching: `etruscan find --text "..."`
- Corpus mining: `etruscan find --corpus latin_library`
- Advanced discovery: `etruscan find --corpus all --advanced`
"""

import json
import re
import click
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from ...config import CORPUS_CACHE_DIR, DB_PATH, TARGET_WORKS
from ...corpus.github_corpus import GitHubCorpusReader
from ...corpus.greek_texts import GreekCorpusClient, GREEK_WORKS
from ...corpus.latin_library import LatinLibraryClient, LATIN_LIBRARY_URLS
from ...corpus.perseus import PerseusClient, TextPassage
from ...corpus.text_cache import WorkCache
from ...db.models import Author, Candidate, Passage, Work
from ...db.repository import Repository
from ...patterns.extractor import GlossExtractor
from ..utils import print_stats


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


@click.command()
@click.option("--text", "-t", help="Analyze a single text string")
@click.option("--file", "-f", type=click.Path(exists=True, path_type=Path),
              help="Analyze text from a file")
@click.option("--corpus", "-c", type=click.Choice([
    "github", "latin_library", "greek",
    "lat_perseus", "grc_perseus", "lacus_curtius",
    "all", "all_latin", "all_greek"
]), help="Corpus source to search")
@click.option("--greek-work", type=click.Choice(list(GREEK_WORKS.keys())),
              help="Specific Greek work to mine (use with --corpus greek)")
@click.option("--work", "-w", help="Specific work to mine (from TARGET_WORKS)")
@click.option("--min-confidence", "-m", type=float, default=0.50,
              help="Minimum pattern confidence (default: 0.50)")
@click.option("--advanced", "-a", is_flag=True,
              help="Enable advanced discovery methods (phonotactic, semantic)")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              help="Output file for results (JSON)")
@click.option("--show", "-s", type=click.Choice(["pending", "reviewing", "accepted", "rejected"]),
              help="Show candidates by status instead of mining")
@click.option("--stats", is_flag=True, help="Show mining statistics")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def find(text: str, file: Path, corpus: str, greek_work: str, work: str,
         min_confidence: float, advanced: bool, output: Path,
         show: str, stats: bool, verbose: bool):
    """Find Etruscan word candidates in texts.

    Uses pattern matching to find phrases like "Tusci vocant X" that indicate
    Etruscan vocabulary. Results are stored in the database for analysis.

    \b
    Examples:
        etruscan find --text "Tusci vocant subulo"
        etruscan find --corpus latin_library
        etruscan find --corpus all --advanced
        etruscan find --show pending
    """
    if stats:
        if not DB_PATH.exists():
            raise click.ClickException("Database not found. Run 'etruscan db setup' first.")
        repo = Repository(DB_PATH)
        print_stats(repo.get_stats())
        return

    extractor = GlossExtractor(min_confidence=min_confidence)

    # Direct text analysis
    if text:
        _find_in_text(text, extractor, min_confidence, advanced, output, verbose)
        return

    # File analysis
    if file:
        input_text = file.read_text()
        _find_in_text(input_text, extractor, min_confidence, advanced, output, verbose,
                      source=str(file))
        return

    # Database required for corpus mining
    if not DB_PATH.exists():
        raise click.ClickException("Database not found. Run 'etruscan db setup' first.")

    repo = Repository(DB_PATH)
    cache = WorkCache()

    # Show existing candidates
    if show:
        _show_candidates(repo, show)
        return

    # Corpus mining
    if corpus:
        total_scanned = 0
        total_found = 0

        if corpus in ["github", "all", "all_latin"]:
            scanned, found = _mine_github_corpus(repo, extractor, min_confidence)
            total_scanned += scanned
            total_found += found

        if corpus in ["latin_library", "all", "all_latin"]:
            scanned, found = _mine_latin_library(repo, extractor, min_confidence)
            total_scanned += scanned
            total_found += found

        if corpus in ["lat_perseus", "all", "all_latin"]:
            scanned, found = _mine_github_repo(
                repo, extractor, "lat_text_perseus", "latin", min_confidence,
                extensions=(".xml",),
            )
            total_scanned += scanned
            total_found += found

        if corpus in ["lacus_curtius", "all", "all_latin"]:
            scanned, found = _mine_github_repo(
                repo, extractor, "latin_text_lacus_curtius", "latin", min_confidence
            )
            total_scanned += scanned
            total_found += found

        if corpus in ["greek", "all", "all_greek"]:
            scanned, found = _mine_greek_corpus(repo, extractor, min_confidence, greek_work)
            total_scanned += scanned
            total_found += found

        if corpus in ["grc_perseus", "all", "all_greek"]:
            scanned, found = _mine_github_repo(
                repo, extractor, "grc_text_perseus", "greek", min_confidence,
                extensions=(".txt", ".xml"),
            )
            total_scanned += scanned
            total_found += found

        click.echo(f"\nTotal: Scanned {total_scanned} texts, found {total_found} candidates")

        # Run advanced discovery if requested
        if advanced and total_found > 0:
            click.echo("\nRunning advanced discovery methods...")
            _run_advanced_discovery(repo)

    elif work:
        scanned, found = _mine_from_cache(work, repo, cache, extractor, min_confidence)
        click.echo(f"\nResults: Scanned {scanned} passages, found {found} candidates")

    else:
        click.echo("Specify --text, --file, --corpus, or --work. Use 'etruscan find --help'.")


def _find_in_text(
    text: str,
    extractor: GlossExtractor,
    min_confidence: float,
    advanced: bool,
    output: Optional[Path],
    verbose: bool,
    source: str = "command line",
):
    """Find candidates in a single text string."""
    click.echo(f"\nSource: {source}")
    click.echo(f"Text length: {len(text):,} characters")
    click.echo(f"Min confidence: {min_confidence}")

    result = extractor.extract(text)

    click.echo(f"\nPatterns applied: {result.patterns_applied}")
    click.echo(f"Matches found: {len(result.matches)}")

    candidates = []

    for match in result.matches:
        if match.confidence >= min_confidence:
            candidates.append({
                "word": match.etruscan_word,
                "pattern": match.pattern_name,
                "confidence": match.confidence,
                "full_match": match.full_match,
                "context_before": match.context_before,
                "context_after": match.context_after,
                "meaning_hint": match.meaning_hint,
            })

            click.echo(f"\n  Word: {match.etruscan_word}")
            click.echo(f"  Pattern: {match.pattern_name}")
            click.echo(f"  Confidence: {match.confidence:.2f}")
            if verbose:
                click.echo(f"  Full match: {match.full_match}")
                click.echo(f"  Context: ...{match.context_before} [{match.full_match}] {match.context_after}...")

    if advanced and candidates:
        click.echo("\n" + "=" * 60)
        click.echo("Advanced Analysis")
        click.echo("=" * 60)
        candidates = _analyze_with_advanced_methods(candidates, text)

    if output and candidates:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            json.dump({
                "source": source,
                "candidates": candidates,
            }, f, indent=2)
        click.echo(f"\nResults saved to: {output}")


def _analyze_with_advanced_methods(candidates: list[dict], text: str) -> list[dict]:
    """Apply advanced discovery methods to candidates."""
    try:
        from ...validation.unified import UnifiedValidator
        validator = UnifiedValidator()

        for candidate in candidates:
            word = candidate["word"]
            context = f"{candidate.get('context_before', '')} {candidate.get('full_match', '')} {candidate.get('context_after', '')}"

            score = validator.validate(word, context, candidate["confidence"])

            candidate["unified_score"] = score.final_score
            candidate["methods_confirmed"] = score.methods_confirmed
            candidate["confirmed_methods"] = score.get_confirmed_methods()
            candidate["recommendation"] = score.recommendation

            if score.inscription_match:
                candidate["inscription_match"] = score.inscription_match
            if score.lemnian_parallel:
                candidate["lemnian_parallel"] = score.lemnian_parallel
            if score.raetic_parallel:
                candidate["raetic_parallel"] = score.raetic_parallel

            click.echo(f"\n  {word}: score={score.final_score:.2f}, methods={score.methods_confirmed}")
            if score.get_confirmed_methods():
                click.echo(f"    Confirmed by: {', '.join(score.get_confirmed_methods())}")

    except Exception as e:
        click.echo(f"  Advanced analysis failed: {e}")

    return candidates


def _run_advanced_discovery(repo: Repository):
    """Run advanced discovery methods on pending candidates."""
    try:
        from ...validation.unified import UnifiedValidator
        validator = UnifiedValidator(repo)

        candidates = repo.get_candidates_by_status("pending")[:50]
        if not candidates:
            click.echo("  No pending candidates to analyze")
            return

        enhanced = 0
        for candidate in candidates:
            context = f"{candidate.context_before or ''} {candidate.full_match or ''} {candidate.context_after or ''}"
            score = validator.validate(
                candidate.etruscan_word,
                context,
                candidate.pattern_confidence or 0.5
            )

            if score.methods_confirmed >= 2:
                enhanced += 1
                # Update candidate notes with advanced analysis
                notes = f"Multi-method: {score.methods_confirmed} methods, score={score.final_score:.2f}"
                repo.update_candidate_status(candidate.id, "reviewing", notes)

        click.echo(f"  Enhanced {enhanced} candidates with multi-method confirmation")

    except Exception as e:
        click.echo(f"  Advanced discovery failed: {e}")


def _show_candidates(repo: Repository, status: str, limit: int = 20):
    """Show candidates from database."""
    candidates = repo.get_candidates_by_status(status)

    click.echo(f"\n{status.upper()} candidates ({len(candidates)} total, showing {min(len(candidates), limit)}):")
    click.echo("-" * 80)

    for candidate in candidates[:limit]:
        click.echo(f"\n  ID: {candidate.id}")
        click.echo(f"  Word: {candidate.etruscan_word}")
        click.echo(f"  Pattern: {candidate.pattern_confidence:.2f}")
        click.echo(f"  Match: {candidate.full_match}")
        click.echo(f"  Context: ...{(candidate.context_before or '')[:50]} | {(candidate.context_after or '')[:50]}...")


def _mine_texts(
    repo: Repository,
    extractor: GlossExtractor,
    texts: Iterator[TextItem],
    source_name: str,
    total_count: Optional[int] = None,
    min_confidence: float = 0.0,
    progress_interval: int = 50,
) -> tuple[int, int]:
    """Generic mining function for any corpus source."""
    scanned = 0
    found = 0

    total_str = f"/{total_count}" if total_count else ""
    click.echo(f"\nMining {source_name}...")

    author_cache: dict[str, int] = {}
    work_cache: dict[str, int] = {}

    for item in texts:
        scanned += 1

        if item.author not in author_cache:
            author = Author(
                name=item.author,
                description=f"Author from {source_name}",
            )
            author_cache[item.author] = repo.insert_author(author)
        author_id = author_cache[item.author]

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

        result = extractor.extract(item.text, language=item.language)

        if result.found_glosses:
            db_passage = Passage(
                work_id=work_id,
                reference=item.reference,
                text_latin=item.text[:10000],
                text_normalized=item.text[:10000].lower(),
                source_url=item.source_url,
            )
            passage_id = repo.insert_passage(db_passage)

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
            click.echo(f"  Scanned {scanned}{total_str} texts, found {found} candidates")

    click.echo(f"  {source_name}: Scanned {scanned} texts, found {found} candidates")
    return scanned, found


def _mine_from_cache(
    work_key: str,
    repo: Repository,
    cache: WorkCache,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine a work from cache."""
    work_info = TARGET_WORKS.get(work_key)
    if not work_info:
        click.echo(f"Unknown work: {work_key}")
        return 0, 0

    urn = work_info.get("urn")
    if not urn:
        click.echo(f"Work {work_key} has no URN")
        return 0, 0

    passages = cache.get_work(urn)
    if not passages:
        click.echo(f"Work {work_key} not in cache. Run 'etruscan corpus download' first.")
        return 0, 0

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

    return _mine_texts(
        repo, extractor, iter_passages(),
        source_name=work_info["title"],
        total_count=len(passages),
        min_confidence=min_confidence,
        progress_interval=100,
    )


def _mine_github_repo(
    repo: Repository,
    extractor: GlossExtractor,
    repo_name: str,
    language: str = "latin",
    min_confidence: float = 0.0,
    extensions: tuple = (".txt",),
) -> tuple[int, int]:
    """Mine any GitHub CLTK corpus repository."""
    corpus_dir = CORPUS_CACHE_DIR / "github" / repo_name

    if not corpus_dir.exists():
        click.echo(f"No {repo_name} found. Clone it first.")
        return 0, 0

    files = []
    for ext in extensions:
        files.extend(corpus_dir.rglob(f"*{ext}"))
    files = [f for f in files if "_eng" not in f.name.lower()]
    files = sorted(files)

    if not files:
        click.echo(f"No files found in {repo_name}")
        return 0, 0

    def strip_xml(text: str) -> str:
        text = re.sub(r'<\?[^?]*\?>', '', text)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def iter_texts():
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                if path.suffix == ".xml":
                    text = strip_xml(text)
                else:
                    text = re.sub(r"\s+", " ", text).strip()

                if len(text) < 100:
                    continue

                relative = path.relative_to(corpus_dir)
                parts = list(relative.parts)
                author = parts[0].title() if len(parts) > 1 else "Unknown"
                title = path.stem

                yield TextItem(
                    text=text,
                    reference=f"{author}/{path.name}",
                    author=author,
                    title=title,
                    urn=f"{repo_name}:{path.name}",
                    priority="LOW",
                    source_url=str(path),
                    language=language,
                )
            except Exception as e:
                click.echo(f"Error reading {path}: {e}")
                continue

    return _mine_texts(
        repo, extractor, iter_texts(),
        source_name=repo_name,
        total_count=len(files),
        min_confidence=min_confidence,
        progress_interval=200,
    )


def _mine_github_corpus(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine the GitHub CLTK Latin Library corpus."""
    return _mine_github_repo(
        repo, extractor, "lat_text_latin_library", "latin", min_confidence
    )


def _mine_latin_library(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
) -> tuple[int, int]:
    """Mine the Latin Library cached texts."""
    client = LatinLibraryClient()
    cached_files = list(client.cache_dir.glob("*.html"))

    if not cached_files:
        click.echo("No Latin Library cache found. Run 'etruscan corpus download --source latin_library' first.")
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

    return _mine_texts(
        repo, extractor, iter_latin_library(),
        source_name="Latin Library",
        total_count=len(cached_files),
        min_confidence=min_confidence,
        progress_interval=20,
    )


def _mine_greek_corpus(
    repo: Repository,
    extractor: GlossExtractor,
    min_confidence: float = 0.0,
    work_key: str = None,
) -> tuple[int, int]:
    """Mine Greek texts from Perseus for Etruscan glosses."""
    greek_dir = CORPUS_CACHE_DIR / "greek"

    if greek_dir.exists():
        cached_files = list(greek_dir.glob("*.json"))
        if cached_files:
            return _mine_greek_from_cache(repo, extractor, min_confidence, work_key)

    return _mine_greek_live(repo, extractor, min_confidence, work_key)


def _mine_greek_from_cache(
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
            click.echo(f"  {key}: not cached, skipping")
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

        scanned, found = _mine_texts(
            repo, extractor, iter_passages(),
            source_name=work_info["title"],
            total_count=len(passages),
            min_confidence=min_confidence,
            progress_interval=50,
        )
        total_scanned += scanned
        total_found += found

    click.echo(f"\nGreek corpus total: Scanned {total_scanned} passages, found {total_found} candidates")
    return total_scanned, total_found


def _mine_greek_live(
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
        click.echo(f"\nFetching {work_info['title']} by {work_info['author']}...")

        if key == "dionysius_ant_rom":
            passages = client.fetch_dionysius_book5()
        elif key == "strabo_geography":
            passages = client.fetch_strabo_book5()
        else:
            passages = client.fetch_work(key, max_passages=200)

        if not passages:
            click.echo(f"  No passages fetched for {work_info['title']}")
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

        scanned, found = _mine_texts(
            repo, extractor, iter_passages(),
            source_name=work_info["title"],
            total_count=len(passages),
            min_confidence=min_confidence,
            progress_interval=50,
        )
        total_scanned += scanned
        total_found += found

    click.echo(f"\nGreek corpus total: Scanned {total_scanned} passages, found {total_found} candidates")
    return total_scanned, total_found
