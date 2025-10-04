"""Tests for project discovery."""

from __future__ import annotations

from pathlib import Path

from repobatch.discovery import (
    _is_project_root,
    discover_projects,
    find_copier_projects,
    find_git_projects,
    find_python_projects,
)
from repobatch.models import Project


def test_is_project_root_with_git(tmp_path: Path) -> None:
    """Test that directory with .git is recognized as project root."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    assert _is_project_root(tmp_path)


def test_is_project_root_with_pyproject(tmp_path: Path) -> None:
    """Test that directory with pyproject.toml is recognized as project root."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    assert _is_project_root(tmp_path)


def test_is_project_root_with_copier(tmp_path: Path) -> None:
    """Test that directory with .copier-answers.yml is recognized as project root."""
    copier_file = tmp_path / ".copier-answers.yml"
    copier_file.write_text("_commit: v1.0.0\n")

    assert _is_project_root(tmp_path)


def test_is_project_root_empty_dir(tmp_path: Path) -> None:
    """Test that empty directory is not recognized as project root."""
    assert not _is_project_root(tmp_path)


def test_project_from_path_python(tmp_path: Path) -> None:
    """Test Project.from_path correctly identifies Python project."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    project = Project.from_path(tmp_path)

    assert project.name == tmp_path.name
    assert project.path == tmp_path
    assert project.is_python
    assert project.is_git
    assert not project.has_copier


def test_project_from_path_copier(tmp_path: Path) -> None:
    """Test Project.from_path correctly reads copier info."""
    copier_file = tmp_path / ".copier-answers.yml"
    copier_file.write_text(
        "_commit: v1.2.3\n_src_path: https://github.com/user/template.git\n"
    )

    project = Project.from_path(tmp_path)

    assert project.has_copier
    assert project.copier_version == "v1.2.3"
    assert project.copier_template == "https://github.com/user/template.git"


def test_project_matches_filters_python_only(tmp_path: Path) -> None:
    """Test project filtering by Python."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    project = Project.from_path(tmp_path)

    assert project.matches_filters(python_only=True)
    assert not project.matches_filters(non_python_only=True)


def test_project_matches_filters_name_pattern(tmp_path: Path) -> None:
    """Test project filtering by name pattern."""
    project = Project.from_path(tmp_path)

    # Create a project with predictable name
    test_dir = tmp_path / "test-project"
    test_dir.mkdir()
    project = Project.from_path(test_dir)

    assert project.matches_filters(name_pattern="test-*")
    assert project.matches_filters(name_pattern="*project")
    assert not project.matches_filters(name_pattern="other-*")


def test_project_matches_filters_has_file(tmp_path: Path) -> None:
    """Test project filtering by file existence."""
    test_file = tmp_path / "README.md"
    test_file.write_text("# Test")

    project = Project.from_path(tmp_path)

    assert project.matches_filters(has_file="README.md")
    assert not project.matches_filters(has_file="NONEXISTENT.txt")


def test_discover_projects(tmp_path: Path) -> None:
    """Test project discovery in directory tree."""
    # Create multiple projects
    project1 = tmp_path / "project1"
    project1.mkdir()
    (project1 / ".git").mkdir()

    project2 = tmp_path / "project2"
    project2.mkdir()
    (project2 / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    # Non-project directory
    other = tmp_path / "other"
    other.mkdir()

    projects = discover_projects(tmp_path)

    assert len(projects) == 2
    project_names = {p.name for p in projects}
    assert "project1" in project_names
    assert "project2" in project_names


def test_find_python_projects(tmp_path: Path) -> None:
    """Test finding only Python projects."""
    # Python project
    python_proj = tmp_path / "python-project"
    python_proj.mkdir()
    (python_proj / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    # Non-Python project
    other_proj = tmp_path / "other-project"
    other_proj.mkdir()
    (other_proj / ".git").mkdir()

    projects = find_python_projects(tmp_path)

    assert len(projects) == 1
    assert projects[0].name == "python-project"
    assert projects[0].is_python


def test_find_git_projects(tmp_path: Path) -> None:
    """Test finding only git repositories."""
    # Git project
    git_proj = tmp_path / "git-project"
    git_proj.mkdir()
    (git_proj / ".git").mkdir()

    # Non-git project
    other_proj = tmp_path / "other-project"
    other_proj.mkdir()
    (other_proj / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    projects = find_git_projects(tmp_path)

    assert len(projects) == 1
    assert projects[0].name == "git-project"
    assert projects[0].is_git


def test_find_copier_projects(tmp_path: Path) -> None:
    """Test finding only copier-managed projects."""
    # Copier project
    copier_proj = tmp_path / "copier-project"
    copier_proj.mkdir()
    (copier_proj / ".copier-answers.yml").write_text("_commit: v1.0.0\n")

    # Non-copier project
    other_proj = tmp_path / "other-project"
    other_proj.mkdir()
    (other_proj / ".git").mkdir()

    projects = find_copier_projects(tmp_path)

    assert len(projects) == 1
    assert projects[0].name == "copier-project"
    assert projects[0].has_copier
