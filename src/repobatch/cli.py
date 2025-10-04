"""Main CLI application for repobatch."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Annotated

from rich.console import Console
from rich.table import Table
import typer

from repobatch import __version__
from repobatch.discovery import discover_projects
from repobatch.executor import (
    git_has_changes,
    read_file_from_project,
    run_batch,
    run_command,
)
from repobatch.models import Project


app = typer.Typer(
    name="repobatch",
    help="Batch operations manager for multiple projects",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"repobatch version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Repobatch - Batch operations for multiple projects."""


def _get_filtered_projects(
    root: Path,
    python: bool,
    non_python: bool,
    copier: bool,
    git: bool,
    name: str | None,
    has_file: str | None,
    max_depth: int = 2,
) -> list[Project]:
    """Get projects filtered by given criteria."""
    projects = discover_projects(root, max_depth=max_depth)

    return [
        p
        for p in projects
        if p.matches_filters(
            python_only=python,
            non_python_only=non_python,
            copier_only=copier,
            git_only=git,
            name_pattern=name,
            has_file=has_file,
        )
    ]


@app.command()
def list(
    root: Annotated[Path, typer.Argument(help="Root directory to search")] = Path.cwd(),
    python: Annotated[
        bool, typer.Option("--python", help="Only Python projects")
    ] = False,
    non_python: Annotated[
        bool, typer.Option("--non-python", help="Only non-Python projects")
    ] = False,
    copier: Annotated[
        bool, typer.Option("--copier", help="Only copier-managed projects")
    ] = False,
    git: Annotated[bool, typer.Option("--git", help="Only git repositories")] = False,
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    has_file: Annotated[
        str | None, typer.Option("--has-file", help="Only projects with this file")
    ] = None,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
) -> None:
    """List all discovered projects."""
    projects = _get_filtered_projects(
        root, python, non_python, copier, git, name, has_file, max_depth
    )

    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return

    table = Table(title="Discovered Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Type", style="green")
    table.add_column("Git", justify="center")
    table.add_column("Copier", justify="center", style="blue")
    table.add_column("Template", style="yellow")

    for project in sorted(projects, key=lambda p: p.name):
        proj_type = "Python" if project.is_python else "Other"

        # Git status with dirty/clean indication
        if not project.is_git:
            git_status = "✗"
        elif git_has_changes(project):
            git_status = "🚧"  # Under construction - dirty
        else:
            git_status = "✅"  # Clean

        copier_status = project.copier_version or "✗" if project.has_copier else "✗"
        template = project.copier_template or "-" if project.has_copier else "-"

        table.add_row(
            project.name,
            str(project.path),
            proj_type,
            git_status,
            copier_status,
            template,
        )

    console.print(table)
    console.print(f"\n[bold]Total projects:[/bold] {len(projects)}")


@app.command()
def versions(
    root: Annotated[Path, typer.Argument(help="Root directory to search")] = Path.cwd(),
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
) -> None:
    """Show copier template versions across projects."""
    projects = _get_filtered_projects(
        root, False, False, True, False, name, None, max_depth
    )

    if not projects:
        console.print("[yellow]No copier-managed projects found[/yellow]")
        return

    table = Table(title="Copier Template Versions")
    table.add_column("Project", style="cyan")
    table.add_column("Version", style="blue")
    table.add_column("Template", style="yellow")

    for project in sorted(projects, key=lambda p: p.name):
        table.add_row(
            project.name,
            project.copier_version or "unknown",
            project.copier_template or "unknown",
        )

    console.print(table)
    console.print(f"\n[bold]Total projects:[/bold] {len(projects)}")


@app.command()
def run(
    command: Annotated[str, typer.Argument(help="Command to run")],
    root: Annotated[
        Path, typer.Option("--root", help="Root directory to search")
    ] = Path.cwd(),
    python: Annotated[
        bool, typer.Option("--python", help="Only Python projects")
    ] = False,
    non_python: Annotated[
        bool, typer.Option("--non-python", help="Only non-Python projects")
    ] = False,
    copier: Annotated[
        bool, typer.Option("--copier", help="Only copier-managed projects")
    ] = False,
    git: Annotated[bool, typer.Option("--git", help="Only git repositories")] = False,
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    has_file: Annotated[
        str | None, typer.Option("--has-file", help="Only projects with this file")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Command timeout in seconds")
    ] = 300,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show command output")
    ] = False,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", "-j", help="Run in parallel with N workers"),
    ] = None,
) -> None:
    """Run a command in multiple projects."""
    projects = _get_filtered_projects(
        root, python, non_python, copier, git, name, has_file, max_depth
    )

    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return

    console.print(
        f"[bold]Running command in {len(projects)} projects:[/bold] {command}\n"
    )

    parallel = max_workers is not None
    result = run_batch(
        projects,
        command,
        timeout=timeout,
        parallel=parallel,
        max_workers=max_workers or 4,
    )

    # Show results
    for cmd_result in result.results:
        status = "✓" if cmd_result.success else "✗"
        style = "green" if cmd_result.success else "red"

        console.print(f"[{style}]{status}[/{style}] {cmd_result.project.name}")

        if verbose or not cmd_result.success:
            if cmd_result.output:
                console.print(f"  [dim]{cmd_result.output.strip()}[/dim]")
            if cmd_result.error:
                console.print(f"  [red]{cmd_result.error.strip()}[/red]")

    # Summary
    console.print()
    console.print("[bold]Summary:[/bold]")
    console.print(f"  Total: {result.total}")
    console.print(f"  [green]Successful: {result.successful}[/green]")
    console.print(f"  [red]Failed: {result.failed}[/red]")

    if result.failed > 0:
        sys.exit(1)


@app.command()
def status(
    root: Annotated[Path, typer.Argument(help="Root directory to search")] = Path.cwd(),
    uncommitted: Annotated[
        bool, typer.Option("--uncommitted", help="Only show projects with changes")
    ] = False,
    python: Annotated[
        bool, typer.Option("--python", help="Only Python projects")
    ] = False,
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
) -> None:
    """Show git status across projects."""
    projects = _get_filtered_projects(
        root, python, False, False, True, name, None, max_depth
    )

    if not projects:
        console.print("[yellow]No git repositories found[/yellow]")
        return

    table = Table(title="Git Status")
    table.add_column("Project", style="cyan")
    table.add_column("Status", style="green")

    projects_with_changes = []

    for project in sorted(projects, key=lambda p: p.name):
        has_changes = git_has_changes(project)

        if uncommitted and not has_changes:
            continue

        status_text = "Modified" if has_changes else "Clean"
        status_style = "yellow" if has_changes else "green"

        table.add_row(
            project.name,
            f"[{status_style}]{status_text}[/{status_style}]",
        )

        if has_changes:
            projects_with_changes.append(project)

    console.print(table)
    console.print(f"\n[bold]Projects with changes:[/bold] {len(projects_with_changes)}")


@app.command()
def show(
    file_path: Annotated[str, typer.Argument(help="Relative file path to show")],
    root: Annotated[
        Path, typer.Option("--root", help="Root directory to search")
    ] = Path.cwd(),
    python: Annotated[
        bool, typer.Option("--python", help="Only Python projects")
    ] = False,
    copier: Annotated[
        bool, typer.Option("--copier", help="Only copier-managed projects")
    ] = False,
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
) -> None:
    """Show a specific file across multiple projects."""
    projects = _get_filtered_projects(
        root, python, False, copier, False, name, file_path, max_depth
    )

    if not projects:
        console.print(f"[yellow]No projects found with file: {file_path}[/yellow]")
        return

    console.print(f"[bold]Showing file:[/bold] {file_path}\n")

    for project in sorted(projects, key=lambda p: p.name):
        content = read_file_from_project(project, file_path)

        if content is not None:
            console.print(f"[cyan]{'=' * 60}[/cyan]")
            console.print(
                f"[cyan bold]{project.name}[/cyan bold] - {project.path / file_path}"
            )
            console.print(f"[cyan]{'=' * 60}[/cyan]")
            console.print(content)
            console.print()


@app.command()
def test(
    root: Annotated[
        Path, typer.Option("--root", help="Root directory to search")
    ] = Path.cwd(),
    python: Annotated[bool, typer.Option("--python", help="Only Python projects")] = True,
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Test timeout in seconds")
    ] = 600,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show test output")
    ] = False,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", "-j", help="Run tests in parallel with N workers"),
    ] = None,
) -> None:
    """Run tests across multiple projects."""
    # Look for projects with pytest
    projects = _get_filtered_projects(
        root, python, False, False, False, name, "pyproject.toml", max_depth
    )

    if not projects:
        console.print("[yellow]No Python projects found[/yellow]")
        return

    console.print(f"[bold]Running tests in {len(projects)} projects[/bold]\n")

    # Try pytest first, fall back to python -m pytest
    parallel = max_workers is not None
    result = run_batch(
        projects,
        "pytest",
        timeout=timeout,
        parallel=parallel,
        max_workers=max_workers or 4,
    )

    # Show results
    for cmd_result in result.results:
        status = "✓" if cmd_result.success else "✗"
        style = "green" if cmd_result.success else "red"

        console.print(f"[{style}]{status}[/{style}] {cmd_result.project.name}")

        if verbose or not cmd_result.success:
            if cmd_result.output:
                console.print(f"  [dim]{cmd_result.output.strip()}[/dim]")
            if cmd_result.error:
                console.print(f"  [red]{cmd_result.error.strip()}[/red]")

    # Summary
    console.print()
    console.print("[bold]Test Summary:[/bold]")
    console.print(f"  Total: {result.total}")
    console.print(f"  [green]Passed: {result.successful}[/green]")
    console.print(f"  [red]Failed: {result.failed}[/red]")

    if result.failed > 0:
        console.print("\n[bold red]Failed projects:[/bold red]")
        for project in result.failed_projects:
            console.print(f"  • {project.name}")
        sys.exit(1)


@app.command()
def update(
    root: Annotated[
        Path, typer.Option("--root", help="Root directory to search")
    ] = Path.cwd(),
    name: Annotated[
        str | None, typer.Option("--name", help="Filter by name pattern")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be done without doing it")
    ] = False,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Maximum directory depth to search")
    ] = 1,
) -> None:
    """Update all copier-managed projects."""
    projects = _get_filtered_projects(
        root, False, False, True, False, name, None, max_depth
    )

    if not projects:
        console.print("[yellow]No copier-managed projects found[/yellow]")
        return

    console.print(f"[bold]Updating {len(projects)} copier projects[/bold]\n")

    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    problem_projects = []

    for project in projects:
        console.print(f"[cyan]{'=' * 60}[/cyan]")
        console.print(f"[cyan bold]{project.name}[/cyan bold] - {project.path}")
        console.print(f"[cyan]{'=' * 60}[/cyan]")

        if dry_run:
            console.print("[dim]Would update this project[/dim]")
            continue

        # Check if it's a git repository
        if not project.is_git:
            console.print("[yellow]⚠ Not a git repository, skipping[/yellow]")
            problem_projects.append((project, "not a git repo"))
            continue

        # Check for unstaged changes
        stashed = False
        if git_has_changes(project):
            console.print("📦 Unstaged changes detected, stashing...")
            result = run_command(
                project,
                ["git", "stash", "push", "-u", "-m", "Auto-stash before copier update"],
                shell=False,
            )
            if result.success:
                stashed = True
            else:
                console.print("[red]✗ Failed to stash changes[/red]")
                problem_projects.append((project, "stash failed"))
                continue
        else:
            console.print("✓ Working directory clean")

        # Run copier update
        console.print("🔄 Running copier update...")
        result = run_command(
            project,
            ["copier", "update", "--trust", "--defaults", str(project.path)],
            shell=False,
            timeout=600,
        )

        if result.success:
            console.print("[green]✓ Copier update successful[/green]")

            # Check for merge conflicts
            conflict_check = run_command(
                project,
                ["git", "diff", "--name-only", "--diff-filter=U"],
                shell=False,
            )

            if conflict_check.success and conflict_check.output.strip():
                console.print("[red]✗ Merge conflicts detected[/red]")
                problem_projects.append((project, "merge conflicts"))
                console.print("⚠ Leaving stash intact, please resolve conflicts manually")
            # No conflicts, unstash if we stashed
            elif stashed:
                console.print("📤 Unstashing changes...")
                unstash_result = run_command(
                    project, ["git", "stash", "pop"], shell=False
                )
                if unstash_result.success:
                    console.print("[green]✓ Changes unstashed successfully[/green]")
                else:
                    console.print("[red]✗ Failed to unstash changes[/red]")
                    problem_projects.append((project, "unstash failed"))
        else:
            console.print("[red]✗ Copier update failed[/red]")
            if result.error:
                console.print(f"[red]{result.error}[/red]")
            problem_projects.append((project, "copier update failed"))

            # Try to unstash anyway if we stashed
            if stashed:
                console.print("📤 Attempting to unstash...")
                run_command(project, ["git", "stash", "pop"], shell=False)

        console.print()

    # Summary
    console.print()
    console.print("[bold]Update Summary:[/bold]")
    console.print(f"  Total projects: {len(projects)}")
    console.print(
        f"  [green]Successfully updated: {len(projects) - len(problem_projects)}[/green]"
    )
    console.print(f"  [red]Problems: {len(problem_projects)}[/red]")

    if problem_projects:
        console.print("\n[bold red]Projects with problems:[/bold red]")
        for project, reason in problem_projects:
            console.print(f"  [red]✗[/red] {project.name} ({reason})")
        sys.exit(1)


def cli_main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    cli_main()
