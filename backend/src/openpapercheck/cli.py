"""
OpenPaperCheck CLI (Typer) — Fast, honest retraction and reference-list checker.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from openpapercheck import __version__
from openpapercheck.core.crossref import CrossrefClient
from openpapercheck.core.doi import normalize_doi
from openpapercheck.core.models import (
    CitationTiming,
    PaperPublicState,
    determine_paper_state,
    evaluate_citation_timing,
)
from openpapercheck.core.storage import (
    MANIFEST_FILE,
    SNAPSHOT_FILE,
    check_reference_dois,
    get_data_dir,
    get_manifest,
    get_retraction,
    has_snapshot,
)

app = typer.Typer(
    name="opc",
    help="OpenPaperCheck — Honest scholarly retraction and reference-list checker.",
    no_args_is_help=True,
)
console = Console()

SNAPSHOT_DOWNLOAD_URL = (
    "https://github.com/UtkarshSingh-09/OpenPaperCheck/releases/download/data-latest"
)


def print_freshness_footer(as_of_date: str, rows_count: int | None = None) -> None:
    """Print the mandatory standardized data freshness footer across all check outputs."""
    records_str = f"{rows_count:,} records" if rows_count else "verified snapshot"
    console.print(
        f"\n[dim]Data as of: {as_of_date} ({records_str}) • Sources: Crossref API, Retraction Watch[/dim]\n"
        "[dim]Disclaimer: This tool reports external facts. Absence of a flag is not endorsement. "
        "Every claim links to an authority.[/dim]"
    )


def check_stale_snapshot(as_of_date: str) -> None:
    """Warn user if their local snapshot is older than 30 days."""
    try:
        as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        days_old = (datetime.now(timezone.utc).date() - as_of_dt).days
        if days_old > 30:
            console.print(
                f"[bold yellow]⚠ Warning:[/bold yellow] Local retraction snapshot is {days_old} days old (updated {as_of_date}).\n"
                "Run [bold cyan]opc update[/bold cyan] to refresh with the latest retraction records.\n"
            )
    except Exception:
        pass


def get_state_badge(state: PaperPublicState) -> tuple[str, str]:
    """Return (badge_markup, border_color) for a given PaperPublicState."""
    if state == PaperPublicState.RETRACTED_EXTERNAL:
        return "[bold white on red] RETRACTED EXTERNAL [/bold white on red]", "red"
    elif state == PaperPublicState.NEEDS_REVIEW:
        return "[bold black on yellow] NEEDS REVIEW [/bold black on yellow]", "yellow"
    elif state == PaperPublicState.NO_FLAGS_FOUND:
        return "[bold white on green] NO FLAGS FOUND [/bold white on green]", "green"
    elif state == PaperPublicState.INSUFFICIENT_DATA:
        return (
            "[bold black on bright_yellow] INSUFFICIENT DATA [/bold black on bright_yellow]",
            "bright_yellow",
        )
    return "[bold white on blue] UNKNOWN [/bold white on blue]", "blue"


@app.command()
def version():
    """Print the current OpenPaperCheck version."""
    console.print(f"[bold cyan]OpenPaperCheck[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def update(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-download even if snapshot is up to date."
    ),
):
    """Download or update the local Retraction Watch SQLite database snapshot."""
    manifest_url = f"{SNAPSHOT_DOWNLOAD_URL}/manifest.json"
    snapshot_url = f"{SNAPSHOT_DOWNLOAD_URL}/retraction_records.sqlite.gz"
    data_dir = get_data_dir()

    console.print("[dim]Checking for latest snapshot manifest from GitHub Releases...[/dim]")
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(manifest_url)
            if resp.status_code == 404:
                console.print(
                    "[yellow]Remote snapshot release asset not found yet (development mode).[/yellow]\n"
                    "If you are developing locally, run [bold]opc snapshot build --sample[/bold] to generate a local snapshot."
                )
                return
            resp.raise_for_status()
            remote_manifest = resp.json()
    except Exception as e:
        console.print(f"[red]Error fetching manifest:[/red] {e}")
        return

    local_manifest = get_manifest()
    remote_sha = remote_manifest.get("sha256")

    if not force and local_manifest and local_manifest.get("sha256") == remote_sha:
        as_of = local_manifest.get("as_of", "unknown")
        console.print(
            f"[green]✓ Local snapshot is already up to date[/green] (data as of [bold]{as_of}[/bold])."
        )
        return

    console.print(
        f"New snapshot available (as of {remote_manifest.get('as_of', 'latest')}). Downloading..."
    )
    gz_path = data_dir / "retraction_records.sqlite.gz"

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}")
    ) as progress:
        task = progress.add_task("Downloading compressed database...", total=None)
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                with client.stream("GET", snapshot_url) as stream:
                    stream.raise_for_status()
                    with open(gz_path, "wb") as f:
                        for chunk in stream.iter_bytes(chunk_size=8192):
                            f.write(chunk)
            progress.update(task, description="Decompressing snapshot...")

            # Verify checksum
            with open(gz_path, "rb") as f:
                computed_sha = hashlib.sha256(f.read()).hexdigest()

            if remote_sha and computed_sha != remote_sha:
                console.print("[red]Checksum verification failed! Aborting update.[/red]")
                gz_path.unlink(missing_ok=True)
                return

            # Decompress into SQLite file
            with gzip.open(gz_path, "rb") as f_in:
                with open(data_dir / "retraction_records.sqlite", "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Save manifest
            with open(data_dir / "manifest.json", "w", encoding="utf-8") as f:
                json.dump(remote_manifest, f, indent=2)

            gz_path.unlink(missing_ok=True)
            console.print("[bold green]✓ Snapshot successfully updated![/bold green]")
        except Exception as e:
            console.print(f"[red]Failed to download snapshot:[/red] {e}")


@app.command()
def check(
    doi: str = typer.Argument(..., help="DOI of the paper to inspect (e.g. 10.1038/nature12373)"),
    email: str | None = typer.Option(
        None, "--email", "-e", help="Contact email for Crossref polite pool"
    ),
):
    """Inspect a paper and its reference list for retractions."""
    canonical_doi = normalize_doi(doi)
    if not canonical_doi:
        console.print(
            f"[bold red]Error:[/bold red] '{doi}' is not a valid DOI syntax.\n"
            "[dim]Standard DOIs begin with '10.' followed by registrant code and suffix, e.g. '10.1038/nature12373'[/dim]"
        )
        raise typer.Exit(code=1)

    manifest = get_manifest() or {}
    as_of_date = manifest.get("as_of", "local database")
    rows_count = manifest.get("rows_count")

    if not has_snapshot():
        console.print(
            "[bold yellow]Warning:[/bold yellow] No local retraction snapshot found.\n"
            "Run [bold cyan]opc update[/bold cyan] to download the database, or [bold cyan]opc snapshot build --sample[/bold cyan] for local dev."
        )
    elif "as_of" in manifest:
        check_stale_snapshot(manifest["as_of"])

    # 1. Fetch paper metadata & references from Crossref
    with console.status("[dim]Fetching metadata and bibliography from Crossref...[/dim]"):
        client = CrossrefClient(mailto=email)
        try:
            work = client.get_work(canonical_doi)
        except httpx.TimeoutException as e:
            console.print(
                f"[bold red]Connection timed out[/bold red] while querying Crossref API for '{canonical_doi}'.\n"
                "[dim]Crossref may be experiencing high load. Please retry or provide --email for polite pool priority.[/dim]"
            )
            raise typer.Exit(code=1) from e
        except httpx.RequestError as e:
            console.print(
                f"[bold red]Network error querying Crossref API:[/bold red] {e}\n"
                "[dim]Unable to reach api.crossref.org. Check your internet connection or DNS settings.[/dim]"
            )
            raise typer.Exit(code=1) from e
        except Exception as e:
            console.print(f"[bold red]Unexpected error querying Crossref:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    if not work:
        console.print(
            f"[bold red]DOI not found in Crossref (HTTP 404):[/bold red] {canonical_doi}\n"
            "[dim]Please check for typographical errors, confirm with the publisher, or check if the work is a preprint hosted outside Crossref.[/dim]"
        )
        raise typer.Exit(code=1)

    # 2. Check retraction status of the target paper itself
    paper_retraction = None
    if has_snapshot():
        paper_retraction = get_retraction(canonical_doi)

    # 3. Process reference list with 3-tier honesty rule
    refs_meta = work["references"]
    deposit_status = refs_meta["deposit_status"]
    with_doi = refs_meta["with_doi"]
    without_doi = refs_meta["without_doi"]
    total_listed = refs_meta["total_listed"]

    ref_dois = [r["doi"] for r in with_doi]
    retracted_refs_map = check_reference_dois(ref_dois) if has_snapshot() else {}

    # 4. Deterministically evaluate public state
    paper_state = determine_paper_state(paper_retraction, refs_meta, retracted_refs_map)
    state_badge, border_color = get_state_badge(paper_state)

    title = work["title"]
    journal = work["journal"]
    pub_date = work.get("publication_date") or "Unknown"

    if paper_retraction:
        status_text = (
            f"{state_badge}\n"
            f"[bold white on red] RETRACTED [/bold white on red] "
            f"according to Retraction Watch (Record #{paper_retraction['rw_record_id']}, {paper_retraction['retraction_date']})\n"
            f"[yellow]Reasons:[/yellow] {', '.join(paper_retraction['reasons'])}"
        )
    elif len(retracted_refs_map) > 0:
        status_text = (
            f"{state_badge}\n"
            f"[bold yellow]Flagged references detected:[/bold yellow] {len(retracted_refs_map)} retracted paper(s) cited in bibliography"
        )
    elif deposit_status in ("restricted", "missing"):
        status_text = (
            f"{state_badge}\n"
            f"[yellow]Reference deposit status: {deposit_status}[/yellow] — complete bibliography could not be audited"
        )
    else:
        status_text = (
            f"{state_badge}\n"
            f"[bold green]No retractions or flagged references recorded[/bold green]"
        )

    console.print(
        Panel(
            f"[bold]{title}[/bold]\n[dim]{journal} • Published: {pub_date}[/dim]\n\n{status_text}",
            title=f"Paper: {canonical_doi}",
            border_style=border_color,
        )
    )

    if deposit_status == "missing":
        console.print("[yellow]Notice:[/yellow] No references were deposited for this work in Crossref.")
        print_freshness_footer(as_of_date, rows_count)
        return
    elif deposit_status == "restricted":
        console.print(
            f"[bold yellow]Notice:[/bold yellow] Crossref lists {total_listed} references for this work, "
            "but the publisher has [italic]restricted open access[/italic] to the reference list."
        )
        print_freshness_footer(as_of_date, rows_count)
        return

    retracted_count = len(retracted_refs_map)
    clean_count = len(with_doi) - retracted_count

    tree = Tree(f"[bold]References ({total_listed} total listed):[/bold]")

    # Tier 1: Checked with DOIs
    doi_branch = tree.add(f"[green]✓ {len(with_doi)} checked via deposited DOIs[/green]")
    if clean_count > 0:
        doi_branch.add(f"[dim]{clean_count} no flags recorded in Retraction Watch[/dim]")

    if retracted_count > 0:
        retracted_branch = doi_branch.add(
            f"[bold red]⚠ {retracted_count} listed as retracted:[/bold red]"
        )
        for r in with_doi:
            r_doi = r["doi"]
            if r_doi in retracted_refs_map:
                ret_info = retracted_refs_map[r_doi]
                ret_date = ret_info.get("retraction_date") or "date unknown"
                nature = ret_info.get("nature") or "Retraction"
                nature_label = "Retracted" if nature.lower() == "retraction" else nature
                # Check if cited before or after retraction
                timing = evaluate_citation_timing(pub_date, ret_date)
                timing_note = ""
                if timing == CitationTiming.CITED_AFTER_RETRACTION:
                    timing_note = "[bold red](Cited AFTER retraction)[/bold red]"
                elif timing == CitationTiming.CITED_BEFORE_RETRACTION:
                    timing_note = "[cyan](Cited BEFORE retraction occurred)[/cyan]"

                reasons_str = f" — {', '.join(ret_info['reasons'])}" if ret_info["reasons"] else ""
                retracted_branch.add(
                    f"#{r['position']} [underline]{r_doi}[/underline] ({nature_label}: {ret_date}) {timing_note}{reasons_str}"
                )

    # Tier 2: Unstructured / Without DOIs
    if without_doi:
        tree.add(
            f"[yellow]ℹ {len(without_doi)} without DOIs[/yellow] "
            "[dim](Unstructured text; could not be checked offline)[/dim]"
        )

    console.print(tree)
    print_freshness_footer(as_of_date, rows_count)


# Evaluation Subcommands
eval_app = typer.Typer(
    name="eval",
    help="Evaluate accuracy and verification against golden benchmarks.",
    no_args_is_help=False,
)
app.add_typer(eval_app, name="eval")


@eval_app.command(name="golden")
def eval_golden(
    fixture: Path = typer.Option(
        Path("tests/fixtures/golden_dois.json"),
        "--fixture",
        "-f",
        help="Path to golden DOIs fixture JSON",
    ),
    email: str | None = typer.Option(None, "--email", "-e", help="Email for polite pool"),
):
    """Run automated verification of golden set DOIs against local database snapshot."""
    if not fixture.is_file():
        # Fallback to relative test directory
        alt = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_dois.json"
        if alt.is_file():
            fixture = alt
        else:
            console.print(f"[bold red]Error:[/bold red] Golden fixture not found at {fixture}")
            raise typer.Exit(code=1)

    with open(fixture, encoding="utf-8") as f:
        golden_set = json.load(f)

    if not has_snapshot():
        console.print("[bold red]Error:[/bold red] No local snapshot found. Run 'opc snapshot build' first.")
        raise typer.Exit(code=1)

    manifest = get_manifest() or {}
    as_of = manifest.get("as_of", "unknown")
    rows = manifest.get("rows_count", 0)

    console.print(
        Panel(
            f"[bold]Evaluating {len(golden_set)} Golden Set DOIs[/bold]\n"
            f"[dim]Snapshot: {as_of} ({rows:,} records)[/dim]",
            title="OpenPaperCheck Automated Evaluation",
            border_style="cyan",
        )
    )

    client = CrossrefClient(mailto=email)
    table = Table(title="Golden Set Evaluation Results", show_lines=True)
    table.add_column("DOI", style="cyan", no_wrap=True)
    table.add_column("Expected State", style="bold")
    table.add_column("Actual State", style="bold")
    table.add_column("Timing / Note", style="dim")
    table.add_column("Status", justify="center")

    passed = 0
    failed = 0

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}")
    ) as progress:
        task = progress.add_task("Verifying golden DOIs...", total=len(golden_set))

        for item in golden_set:
            raw_doi = item["doi"]
            canonical = normalize_doi(raw_doi)
            expected = item.get("expected_state")
            expected_scenario = item.get("timing_scenario")

            progress.update(task, description=f"Evaluating {canonical}...")

            # 1. Check local snapshot
            paper_retraction = get_retraction(canonical)

            # 2. Check metadata
            timing_note = "-"
            try:
                work = client.get_work(canonical)
            except Exception:
                work = None

            if work:
                refs_meta = work["references"]
                ref_dois = [r["doi"] for r in refs_meta.get("with_doi", [])]
                ret_refs = check_reference_dois(ref_dois)
                actual_state = determine_paper_state(paper_retraction, refs_meta, ret_refs)

                # Check timing scenario if applicable
                pub_date = work.get("publication_date")
                timing_note = ""
                for r in refs_meta.get("with_doi", []):
                    r_doi = r["doi"]
                    if r_doi in ret_refs:
                        ret_date = ret_refs[r_doi].get("retraction_date")
                        timing = evaluate_citation_timing(pub_date, ret_date)
                        timing_note = timing.value
            else:
                actual_state = (
                    PaperPublicState.RETRACTED_EXTERNAL
                    if paper_retraction
                    else PaperPublicState.INSUFFICIENT_DATA
                )

            # Match criteria
            state_match = actual_state.value == expected
            timing_match = True
            if expected_scenario:
                timing_match = timing_note == expected_scenario

            if state_match and timing_match:
                status_str = "[bold green]PASS[/bold green]"
                passed += 1
            else:
                status_str = "[bold red]FAIL[/bold red]"
                failed += 1

            table.add_row(
                canonical,
                expected,
                actual_state.value,
                timing_note,
                status_str,
            )
            progress.advance(task)

    console.print(table)
    pass_rate = (passed / len(golden_set)) * 100
    color = "green" if failed == 0 else "red"
    console.print(
        Panel(
            f"Total Evaluated: [bold]{len(golden_set)}[/bold] | "
            f"Passed: [bold green]{passed}[/bold green] | "
            f"Failed: [bold red]{failed}[/bold red] | "
            f"Pass Rate: [bold {color}]{pass_rate:.1f}%[/bold {color}]",
            border_style=color,
        )
    )

    if failed > 0:
        raise typer.Exit(code=1)


# Snapshot Builder Subcommands
snapshot_app = typer.Typer(
    name="snapshot",
    help="Build or manage local SQLite snapshots (for developers).",
    no_args_is_help=False,
)
app.add_typer(snapshot_app, name="snapshot")


@snapshot_app.callback(invoke_without_command=True)
def snapshot_default(
    ctx: typer.Context,
    sample: bool = typer.Option(False, "--sample", help="Use bundled small sample fixture"),
    csv: Path | None = typer.Option(None, "--csv", help="Path to raw Retraction Watch CSV"),
):
    """Build a local SQLite snapshot (for developers)."""
    if ctx.invoked_subcommand is None:
        from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

        build_sqlite_snapshot(csv_path=csv, use_sample=sample)


@snapshot_app.command(name="build")
def snapshot_build(
    sample: bool = typer.Option(False, "--sample", help="Use bundled small sample fixture"),
    csv: Path | None = typer.Option(None, "--csv", help="Path to raw Retraction Watch CSV"),
):
    """Compile Retraction Watch data into an indexed SQLite database snapshot."""
    from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

    build_sqlite_snapshot(csv_path=csv, use_sample=sample)


# Ingest Subcommands
ingest_app = typer.Typer(
    name="ingest",
    help="Ingest external scholarly datasets (Retraction Watch, Crossref).",
    no_args_is_help=True,
)
app.add_typer(ingest_app, name="ingest")


@ingest_app.command(name="rw")
def ingest_rw(
    csv: Path | None = typer.Option(None, "--csv", "-c", help="Path to Retraction Watch CSV"),
    sample: bool = typer.Option(False, "--sample", "-s", help="Use bundled sample records"),
):
    """Ingest Retraction Watch CSV data and build verified local snapshot."""
    from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

    build_sqlite_snapshot(csv_path=csv, use_sample=sample)


if __name__ == "__main__":
    app()
