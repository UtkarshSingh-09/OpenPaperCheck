"""
OpenPaperCheck CLI (Typer) — Fast, honest retraction and reference-list checker.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from openpapercheck import __version__
from openpapercheck.core.crossref import CrossrefClient
from openpapercheck.core.doi import normalize_doi
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
                with open(SNAPSHOT_FILE, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Save manifest
            with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
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
        console.print(f"[bold red]Error:[/bold red] '{doi}' is not a valid DOI.")
        raise typer.Exit(code=1)

    if not has_snapshot():
        console.print(
            "[bold yellow]Warning:[/bold yellow] No local retraction snapshot found.\n"
            "Run [bold cyan]opc update[/bold cyan] to download the database, or [bold cyan]opc snapshot build --sample[/bold cyan] for local dev."
        )

    # 1. Fetch paper metadata & references from Crossref
    with console.status("[dim]Fetching metadata and bibliography from Crossref...[/dim]"):
        client = CrossrefClient(mailto=email)
        try:
            work = client.get_work(canonical_doi)
        except Exception as e:
            console.print(f"[bold red]Network error querying Crossref:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    if not work:
        console.print(f"[bold red]DOI not found in Crossref:[/bold red] {canonical_doi}")
        raise typer.Exit(code=1)

    # 2. Check retraction status of the target paper itself
    paper_retraction = None
    if has_snapshot():
        paper_retraction = get_retraction(canonical_doi)

    manifest = get_manifest() or {}
    as_of_date = manifest.get("as_of", "local database")

    # Render header panel
    title = work["title"]
    journal = work["journal"]
    pub_date = work.get("publication_date") or "Unknown"

    if paper_retraction:
        status_text = (
            f"[bold white on red] RETRACTED [/bold white on red] "
            f"according to Retraction Watch (Record #{paper_retraction['rw_record_id']}, {paper_retraction['retraction_date']})\n"
            f"[yellow]Reasons:[/yellow] {', '.join(paper_retraction['reasons'])}"
        )
    else:
        status_text = (
            f"[bold green]No retraction recorded[/bold green] for this paper (as of {as_of_date})"
        )

    console.print(
        Panel(
            f"[bold]{title}[/bold]\n[dim]{journal} • Published: {pub_date}[/dim]\n\n{status_text}",
            title=f"Paper: {canonical_doi}",
            border_style="red" if paper_retraction else "blue",
        )
    )

    # 3. Process reference list with 3-tier honesty rule
    refs_meta = work["references"]
    deposit_status = refs_meta["deposit_status"]
    with_doi = refs_meta["with_doi"]
    without_doi = refs_meta["without_doi"]
    total_listed = refs_meta["total_listed"]

    if deposit_status == "missing":
        console.print("[yellow]Notice:[/yellow] No references were deposited for this work.")
        return
    elif deposit_status == "restricted":
        console.print(
            f"[bold yellow]Notice:[/bold yellow] Crossref lists {total_listed} references for this work, "
            "but the publisher has [italic]restricted open access[/italic] to the reference list."
        )
        return

    # Check references with DOIs against local database
    ref_dois = [r["doi"] for r in with_doi]
    retracted_refs_map = check_reference_dois(ref_dois) if has_snapshot() else {}

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
                # Check if cited before or after retraction
                timing_note = ""
                if pub_date and ret_date != "date unknown":
                    if pub_date > ret_date:
                        timing_note = "[bold red](Cited AFTER retraction)[/bold red]"
                    else:
                        timing_note = "[cyan](Cited BEFORE retraction occurred)[/cyan]"

                reasons_str = f" — {', '.join(ret_info['reasons'])}" if ret_info["reasons"] else ""
                retracted_branch.add(
                    f"#{r['position']} [underline]{r_doi}[/underline] (Retracted: {ret_date}) {timing_note}{reasons_str}"
                )

    # Tier 2: Unstructured / Without DOIs
    if without_doi:
        tree.add(
            f"[yellow]ℹ {len(without_doi)} without DOIs[/yellow] "
            "[dim](Unstructured text; could not be checked offline)[/dim]"
        )

    console.print(tree)
    console.print(
        "\n[dim]Disclaimer: This tool reports external facts. Absence of a flag is not endorsement. "
        "Every claim links to an authority.[/dim]"
    )


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
