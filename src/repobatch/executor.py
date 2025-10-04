"""Command execution functionality."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from repobatch.models import BatchResult, CommandResult, Project


if TYPE_CHECKING:
    from collections.abc import Sequence


def run_command(
    project: Project,
    command: str | list[str],
    *,
    shell: bool = True,
    timeout: int | None = 300,
    capture_output: bool = True,
) -> CommandResult:
    """Run a command in a project directory.

    Args:
        project: Project to run command in
        command: Command to execute (string or list of args)
        shell: Whether to run command in shell
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        CommandResult with execution details
    """
    try:
        result = subprocess.run(
            command,
            cwd=project.path,
            shell=shell,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False,
        )

        return CommandResult(
            project=project,
            success=result.returncode == 0,
            output=result.stdout if capture_output else "",
            error=result.stderr if capture_output else "",
            exit_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        return CommandResult(
            project=project,
            success=False,
            output="",
            error=f"Command timed out after {timeout} seconds",
            exit_code=-1,
        )
    except Exception as e:
        return CommandResult(
            project=project,
            success=False,
            output="",
            error=str(e),
            exit_code=-1,
        )


def run_batch(
    projects: Sequence[Project],
    command: str | list[str],
    *,
    shell: bool = True,
    timeout: int | None = 300,
    capture_output: bool = True,
    continue_on_error: bool = True,
) -> BatchResult:
    """Run a command across multiple projects.

    Args:
        projects: List of projects to run command in
        command: Command to execute
        shell: Whether to run command in shell
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        continue_on_error: Continue with other projects if one fails

    Returns:
        BatchResult with all execution results
    """
    results = []

    for project in projects:
        result = run_command(
            project,
            command,
            shell=shell,
            timeout=timeout,
            capture_output=capture_output,
        )
        results.append(result)

        if not continue_on_error and not result.success:
            break

    return BatchResult.from_results(results)


def git_status(project: Project) -> CommandResult:
    """Get git status for a project.

    Args:
        project: Project to check

    Returns:
        CommandResult with git status output
    """
    if not project.is_git:
        return CommandResult(
            project=project,
            success=False,
            output="",
            error="Not a git repository",
            exit_code=-1,
        )

    return run_command(project, ["git", "status", "--porcelain"], shell=False)


def git_has_changes(project: Project) -> bool:
    """Check if project has uncommitted changes.

    Args:
        project: Project to check

    Returns:
        True if there are uncommitted changes
    """
    result = git_status(project)
    return result.success and bool(result.output.strip())


def read_file_from_project(project: Project, file_path: str) -> str | None:
    """Read a file from a project directory.

    Args:
        project: Project to read from
        file_path: Relative path to file

    Returns:
        File contents or None if file doesn't exist
    """
    full_path = project.path / file_path
    if not full_path.exists():
        return None

    try:
        return full_path.read_text()
    except Exception:
        return None
