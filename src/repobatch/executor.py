"""Command execution functionality."""

from __future__ import annotations

import asyncio
import subprocess
from typing import TYPE_CHECKING

from repobatch.models import BatchResult, CommandResult


if TYPE_CHECKING:
    from collections.abc import Sequence

    from repobatch.models import Project


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
    except Exception as e:  # noqa: BLE001
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
    parallel: bool = False,
    max_workers: int = 4,
) -> BatchResult:
    """Run a command across multiple projects.

    Args:
        projects: List of projects to run command in
        command: Command to execute
        shell: Whether to run command in shell
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        continue_on_error: Continue with other projects if one fails
        parallel: Run commands in parallel using asyncio
        max_workers: Maximum number of parallel workers (only used if parallel=True)

    Returns:
        BatchResult with all execution results
    """
    if parallel:
        return asyncio.run(
            _run_batch_async(
                projects,
                command,
                shell=shell,
                timeout=timeout,
                capture_output=capture_output,
                max_workers=max_workers,
            )
        )

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


async def _run_command_async(
    project: Project,
    command: str | list[str],
    *,
    shell: bool = True,
    timeout: int | None = 300,
    capture_output: bool = True,
) -> CommandResult:
    """Run a command asynchronously in a project directory.

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
        if shell and isinstance(command, str):
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=project.path,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
            )
        else:
            cmd_list = command if isinstance(command, list) else [command]
            proc = await asyncio.create_subprocess_exec(
                *cmd_list,
                cwd=project.path,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
            )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            return CommandResult(
                project=project,
                success=proc.returncode == 0,
                output=stdout.decode() if capture_output and stdout else "",
                error=stderr.decode() if capture_output and stderr else "",
                exit_code=proc.returncode or 0,
            )

        except TimeoutError:
            proc.kill()
            await proc.wait()
            return CommandResult(
                project=project,
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1,
            )

    except Exception as e:  # noqa: BLE001
        return CommandResult(
            project=project,
            success=False,
            output="",
            error=str(e),
            exit_code=-1,
        )


async def _run_batch_async(
    projects: Sequence[Project],
    command: str | list[str],
    *,
    shell: bool = True,
    timeout: int | None = 300,
    capture_output: bool = True,
    max_workers: int = 4,
) -> BatchResult:
    """Run commands in parallel across multiple projects.

    Args:
        projects: List of projects to run command in
        command: Command to execute
        shell: Whether to run command in shell
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        max_workers: Maximum number of parallel workers

    Returns:
        BatchResult with all execution results
    """
    semaphore = asyncio.Semaphore(max_workers)

    async def _run_with_semaphore(project: Project) -> CommandResult:
        async with semaphore:
            return await _run_command_async(
                project,
                command,
                shell=shell,
                timeout=timeout,
                capture_output=capture_output,
            )

    tasks = [_run_with_semaphore(project) for project in projects]
    results = await asyncio.gather(*tasks)

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
    except Exception:  # noqa: BLE001
        return None
