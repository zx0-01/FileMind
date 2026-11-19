from __future__ import annotations

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .core import (
    apply_organization, find_duplicates, human_size, largest_files,
    organization_plan, scan_folder, search_files, write_report,
)

app = typer.Typer(
    name="filemind",
    help="A smart, safe terminal file manager.",
    no_args_is_help=True,
    add_completion=True,
)
console = Console()
error_console = Console(stderr=True)


def fail(message: str) -> None:
    error_console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(1)


def show_header(subtitle: str) -> None:
    console.print(Panel.fit(
        f"[bold bright_magenta]F I L E M I N D[/bold bright_magenta] [dim]v{__version__}[/dim]\n"
        f"[white]{subtitle}[/white]\n[dim]by zx0-01[/dim]",
        border_style="bright_magenta",
    ))


@app.callback()
def main() -> None:
    """FileMind — understand and organize your files safely."""


@app.command()
def scan(path: Path = typer.Argument(..., exists=True, file_okay=False, readable=True)) -> None:
    """Show a summary of a folder and its file types."""
    try:
        data = scan_folder(path)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header("Folder overview")
    console.print(f"[dim]Location:[/dim] {data['root']}")
    console.print(
        f"\n[bold]{data['files']:,}[/bold] files  "
        f"[bold bright_cyan]{human_size(data['total_bytes'])}[/bold bright_cyan] total  "
        f"[dim]{data['errors']} read errors[/dim]\n"
    )
    table = Table(box=None, header_style="bold bright_magenta")
    table.add_column("CATEGORY")
    table.add_column("FILES", justify="right")
    table.add_column("SIZE", justify="right")
    for category, values in data["categories"].items():
        table.add_row(category, f"{values['count']:,}", human_size(values["bytes"]))
    console.print(table)


@app.command()
def largest(
    path: Path = typer.Argument(..., exists=True, file_okay=False),
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=500, help="Number of files to show."),
) -> None:
    """Find the largest files in a folder."""
    try:
        items = largest_files(path, limit)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header(f"Top {limit} largest files")
    table = Table(box=None, header_style="bold bright_magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("SIZE", justify="right")
    table.add_column("FILE")
    for index, (file_path, size) in enumerate(items, 1):
        table.add_row(str(index), human_size(size), str(file_path))
    console.print(table)


@app.command()
def duplicates(path: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Find identical files using SHA-256 checksums."""
    try:
        groups = find_duplicates(path)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header("Duplicate finder")
    if not groups:
        console.print("[green]No duplicate files found.[/green]")
        return
    for index, group in enumerate(groups, 1):
        total = sum(p.stat().st_size for p in group if p.exists())
        console.print(Panel(
            "\n".join(str(p) for p in group),
            title=f"[bold]Group {index}[/bold] · {human_size(total)} across {len(group)} copies",
            border_style="yellow",
        ))
    console.print(f"[bold]{len(groups)}[/bold] duplicate groups found. No files were changed.")


@app.command()
def search(
    path: Path = typer.Argument(..., exists=True, file_okay=False),
    query: str = typer.Argument(..., help="Text to find in filenames."),
    extension: str | None = typer.Option(None, "--ext", help="Optional extension, e.g. .pdf"),
) -> None:
    """Search filenames recursively."""
    try:
        results = search_files(path, query, extension)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header(f"Search: {query}")
    if not results:
        console.print("[yellow]No matching files.[/yellow]")
        return
    for result in results:
        console.print(f"[bright_cyan]•[/bright_cyan] {result}")
    console.print(f"\n[dim]{len(results)} result(s)[/dim]")


@app.command()
def organize(
    path: Path = typer.Argument(..., exists=True, file_okay=False),
    apply: bool = typer.Option(False, "--apply", help="Actually move files. Without this, only preview."),
) -> None:
    """Preview file organization by type; use --apply to move files."""
    try:
        plan = organization_plan(path)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header("Organization plan")
    if not plan:
        console.print("[green]Nothing to organize in this folder.[/green]")
        return
    table = Table(box=None, header_style="bold bright_magenta")
    table.add_column("FROM")
    table.add_column("TO")
    for source, destination in plan:
        table.add_row(source.name, str(destination.relative_to(path.expanduser().resolve())))
    console.print(table)
    if not apply:
        console.print(f"\n[yellow]Preview only:[/yellow] {len(plan)} file(s) would be moved.")
        console.print("Run [bold]filemind organize PATH --apply[/bold] to confirm.")
        return
    confirm = typer.confirm(f"Move {len(plan)} file(s)?", default=False)
    if not confirm:
        console.print("[yellow]Cancelled. No files were moved.[/yellow]")
        raise typer.Exit()
    moved, errors = apply_organization(plan)
    console.print(f"\n[green]Moved {moved} file(s).[/green]")
    for error in errors:
        console.print(f"[red]Could not move:[/red] {error}")


@app.command()
def report(
    path: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path = typer.Option(Path("filemind-report.json"), "--output", "-o"),
) -> None:
    """Export a folder scan report to JSON."""
    try:
        data = scan_folder(path)
        write_report(data, output)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    show_header("Report exported")
    console.print(f"[green]Saved:[/green] {output.expanduser().resolve()}")


if __name__ == "__main__":
    app()
