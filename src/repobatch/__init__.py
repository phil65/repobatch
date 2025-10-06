"""RepoBatch: CLI project manager for batch operations"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("repobatch")
__title__ = "RepoBatch"
__description__ = "CLI project manager for batch operations"
__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2025 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/repobatch"

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
