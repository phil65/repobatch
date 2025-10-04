"""Project discovery functionality."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from repobatch.models import Project


if TYPE_CHECKING:
    from collections.abc import Iterator


def discover_projects(
    root_path: Path,
    *,
    max_depth: int = 2,
    exclude_patterns: list[str] | None = None,
) -> list[Project]:
    """Discover all projects under a root path.

    Args:
        root_path: Root directory to search
        max_depth: Maximum directory depth to search
        exclude_patterns: List of directory names to exclude

    Returns:
        List of discovered projects
    """
    if exclude_patterns is None:
        exclude_patterns = [
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".tox",
        ]

    projects = []
    seen_dirs = set()

    for project_dir in _walk_directories(root_path, max_depth, exclude_patterns):
        # Avoid duplicates
        if project_dir in seen_dirs:
            continue

        # Check if this looks like a project root
        if _is_project_root(project_dir):
            seen_dirs.add(project_dir)
            projects.append(Project.from_path(project_dir))

    return projects


def _walk_directories(
    root: Path,
    max_depth: int,
    exclude_patterns: list[str],
) -> Iterator[Path]:
    """Walk directory tree yielding directories up to max_depth.

    Args:
        root: Root directory to walk
        max_depth: Maximum depth to traverse
        exclude_patterns: Directory names to skip

    Yields:
        Directory paths
    """

    def _walk(path: Path, current_depth: int) -> Iterator[Path]:
        if current_depth > max_depth:
            return

        try:
            for item in path.iterdir():
                if not item.is_dir():
                    continue

                # Skip excluded directories
                if item.name in exclude_patterns or item.name.startswith("."):
                    continue

                yield item

                # Recurse into subdirectories
                yield from _walk(item, current_depth + 1)

        except PermissionError:
            # Skip directories we can't access
            pass

    yield from _walk(root, 0)


def _is_project_root(path: Path) -> bool:
    """Check if a directory looks like a project root.

    Args:
        path: Directory to check

    Returns:
        True if directory appears to be a project root
    """
    # Markers that indicate a project root
    project_markers = [
        ".git",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        ".copier-answers.yml",
    ]

    for marker in project_markers:
        try:
            if (path / marker).exists():
                return True
        except (PermissionError, OSError):
            # Skip markers we can't access
            continue

    return False


def find_copier_projects(root_path: Path) -> list[Project]:
    """Find all copier-managed projects.

    Args:
        root_path: Root directory to search

    Returns:
        List of projects with .copier-answers.yml
    """
    projects = discover_projects(root_path)
    return [p for p in projects if p.has_copier]


def find_python_projects(root_path: Path) -> list[Project]:
    """Find all Python projects.

    Args:
        root_path: Root directory to search

    Returns:
        List of projects with pyproject.toml
    """
    projects = discover_projects(root_path)
    return [p for p in projects if p.is_python]


def find_git_projects(root_path: Path) -> list[Project]:
    """Find all git repositories.

    Args:
        root_path: Root directory to search

    Returns:
        List of git repositories
    """
    projects = discover_projects(root_path)
    return [p for p in projects if p.is_git]
