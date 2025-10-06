"""Repobatch - Batch operations manager for multiple projects."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("repobatch")

from repobatch.discovery import (
    discover_projects,
    find_copier_projects,
    find_git_projects,
    find_python_projects,
)
from repobatch.executor import (
    git_has_changes,
    git_status,
    read_file_from_project,
    run_batch,
    run_command,
)
from repobatch.models import BatchResult, CommandResult, Project


__all__ = [
    "BatchResult",
    "CommandResult",
    "Project",
    "__version__",
    "discover_projects",
    "find_copier_projects",
    "find_git_projects",
    "find_python_projects",
    "git_has_changes",
    "git_status",
    "read_file_from_project",
    "run_batch",
    "run_command",
]
