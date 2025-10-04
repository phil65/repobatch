"""Core models for repobatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class Project:
    """Represents a discovered project."""

    path: Path
    name: str
    is_git: bool = False
    is_python: bool = False
    has_copier: bool = False
    copier_version: str | None = None
    copier_template: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path) -> Project:
        """Discover project metadata from a path.

        Args:
            path: Path to the project directory

        Returns:
            Project instance with discovered metadata
        """
        name = path.name

        # Handle permission errors gracefully
        try:
            is_git = (path / ".git").exists()
        except (PermissionError, OSError):
            is_git = False

        try:
            is_python = (path / "pyproject.toml").exists()
        except (PermissionError, OSError):
            is_python = False

        try:
            has_copier = (path / ".copier-answers.yml").exists()
        except (PermissionError, OSError):
            has_copier = False

        copier_version = None
        copier_template = None

        if has_copier:
            copier_version, copier_template = cls._read_copier_info(
                path / ".copier-answers.yml"
            )

        return cls(
            path=path,
            name=name,
            is_git=is_git,
            is_python=is_python,
            has_copier=has_copier,
            copier_version=copier_version,
            copier_template=copier_template,
        )

    @staticmethod
    def _read_copier_info(copier_file: Path) -> tuple[str | None, str | None]:
        """Read version and template from copier answers file.

        Args:
            copier_file: Path to .copier-answers.yml

        Returns:
            Tuple of (version, template)
        """
        if not copier_file.exists():
            return None, None

        version = None
        template = None

        with copier_file.open() as f:
            for line in f:
                line = line.strip()
                if line.startswith("_commit:"):
                    version = line.split(":", 1)[1].strip()
                elif line.startswith("_src_path:"):
                    template = line.split(":", 1)[1].strip()

        return version, template

    def matches_filters(
        self,
        *,
        python_only: bool = False,
        non_python_only: bool = False,
        copier_only: bool = False,
        git_only: bool = False,
        name_pattern: str | None = None,
        has_file: str | None = None,
    ) -> bool:
        """Check if project matches given filters.

        Args:
            python_only: Only match Python projects
            non_python_only: Only match non-Python projects
            copier_only: Only match copier-managed projects
            git_only: Only match git repositories
            name_pattern: Pattern to match project name against
            has_file: File that must exist in project

        Returns:
            True if project matches all filters
        """
        if python_only and not self.is_python:
            return False
        if non_python_only and self.is_python:
            return False
        if copier_only and not self.has_copier:
            return False
        if git_only and not self.is_git:
            return False

        if name_pattern:
            import fnmatch

            if not fnmatch.fnmatch(self.name, name_pattern):
                return False

        if has_file:
            try:
                if not (self.path / has_file).exists():
                    return False
            except (PermissionError, OSError):
                return False

        return True


@dataclass
class CommandResult:
    """Result of running a command in a project."""

    project: Project
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0


@dataclass
class BatchResult:
    """Results from a batch operation across multiple projects."""

    results: list[CommandResult]
    total: int
    successful: int
    failed: int

    @classmethod
    def from_results(cls, results: Sequence[CommandResult]) -> BatchResult:
        """Create BatchResult from a list of CommandResults.

        Args:
            results: List of command results

        Returns:
            BatchResult with aggregated statistics
        """
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return cls(
            results=list(results),
            total=len(results),
            successful=successful,
            failed=failed,
        )

    @property
    def failed_projects(self) -> list[Project]:
        """Get list of projects where commands failed."""
        return [r.project for r in self.results if not r.success]

    @property
    def successful_projects(self) -> list[Project]:
        """Get list of projects where commands succeeded."""
        return [r.project for r in self.results if r.success]
