# repobatch

**Batch operations manager for multiple projects**

[![PyPI version](https://img.shields.io/pypi/v/repobatch.svg)](https://pypi.org/project/repobatch/)
[![Python versions](https://img.shields.io/pypi/pyversions/repobatch.svg)](https://pypi.org/project/repobatch/)
[![License](https://img.shields.io/pypi/l/repobatch.svg)](https://github.com/phil65/repobatch/blob/main/LICENSE)

`repobatch` is a powerful CLI tool for managing multiple projects in a workspace. It helps you run batch operations, check status, run tests, and manage copier-templated projects across your entire development portfolio.

## Features

- 🔍 **Project Discovery** - Automatically finds all projects (Python, Node.js, Rust, etc.)
- 🏷️ **Smart Filtering** - Filter by language, file patterns, git status, and more
- 🔄 **Copier Management** - Update all copier-templated projects with one command
- 🧪 **Batch Testing** - Run tests across multiple projects and see aggregated results
- 📊 **Status Overview** - Check git status, uncommitted changes across all projects
- 🔧 **Batch Commands** - Run arbitrary commands in multiple projects
- 📄 **File Inspection** - View specific files across your entire workspace

## Installation

```bash
pip install repobatch
```

Or with uv:

```bash
uv pip install repobatch
```

## Quick Start

```bash
# List all projects in current directory
repobatch list

# Show copier template versions
repobatch versions

# Check git status across all projects
repobatch status --uncommitted

# Run tests in all Python projects
repobatch test --python

# Update all copier-managed projects
repobatch update

# Run a command in all projects
repobatch run "git pull" --git
```

## Commands

### `list` - List Projects

Discover and list all projects in a directory tree.

```bash
# List all projects
repobatch list

# Only Python projects
repobatch list --python

# Only copier-managed projects
repobatch list --copier

# Filter by name pattern
repobatch list --name "llmling*"

# Projects containing a specific file
repobatch list --has-file "pytest.ini"
```

### `versions` - Show Copier Versions

Display copier template versions across all projects.

```bash
# Show all copier project versions
repobatch versions

# Filter by name
repobatch versions --name "mk*"
```

Output:
```
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project     ┃ Version ┃ Template                                ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ mkdown      │ v1.9.0  │ https://github.com/phil65/copier-ph... │
│ mkconvert   │ v1.9.0  │ https://github.com/phil65/copier-ph... │
└─────────────┴─────────┴─────────────────────────────────────────┘
```

### `status` - Git Status

Check git status across multiple projects.

```bash
# Show all git repositories
repobatch status

# Only projects with uncommitted changes
repobatch status --uncommitted

# Filter Python projects
repobatch status --python
```

### `test` - Run Tests

Run tests across multiple projects and get aggregated results.

```bash
# Run tests in all Python projects
repobatch test

# Filter by name
repobatch test --name "llmling*"

# Show verbose output
repobatch test --verbose

# Custom timeout
repobatch test --timeout 600
```

### `run` - Batch Command Execution

Execute arbitrary commands across multiple projects.

```bash
# Run git pull in all git repositories
repobatch run "git pull" --git

# Run a command in Python projects only
repobatch run "uv sync" --python

# With verbose output
repobatch run "pytest" --verbose

# Filter by pattern
repobatch run "git status" --name "mk*"
```

### `update` - Update Copier Projects

Update all copier-managed projects to their latest template version.

```bash
# Update all copier projects
repobatch update

# Dry run to see what would be updated
repobatch update --dry-run

# Filter by name
repobatch update --name "llmling*"
```

Features:
- Automatically stashes uncommitted changes
- Runs `copier update --trust --defaults`
- Detects merge conflicts
- Unstashes changes if successful
- Reports all problems at the end

### `show` - Show Files

Display a specific file across multiple projects.

```bash
# Show pyproject.toml from all Python projects
repobatch show pyproject.toml --python

# Show specific config file
repobatch show .github/workflows/ci.yml --copier

# Filter by name
repobatch show README.md --name "llm*"
```

## Filtering Options

All commands support these filter options:

- `--python` - Only Python projects (have `pyproject.toml`)
- `--non-python` - Only non-Python projects
- `--copier` - Only copier-managed projects (have `.copier-answers.yml`)
- `--git` - Only git repositories
- `--name PATTERN` - Filter by name pattern (supports wildcards)
- `--has-file PATH` - Only projects containing a specific file

## Examples

### Daily Workflow

```bash
# Check what needs updating
repobatch versions | grep -v "v1.9.0"

# See what has uncommitted changes
repobatch status --uncommitted

# Update all copier templates
repobatch update

# Run tests to ensure everything still works
repobatch test --python
```

### Project Audit

```bash
# Find all projects
repobatch list

# Check which are Python projects
repobatch list --python

# Check which have copier templates
repobatch list --copier

# Find projects with specific files
repobatch list --has-file ".pre-commit-config.yaml"
```

### Batch Operations

```bash
# Pull latest changes everywhere
repobatch run "git pull" --git

# Update dependencies in Python projects
repobatch run "uv sync" --python

# Run linting across all projects
repobatch run "ruff check ." --python

# Check for outdated dependencies
repobatch run "uv pip list --outdated" --python
```

## Configuration

`repobatch` works without configuration, but you can control behavior through:

**Project Discovery:**
- Searches up to 2 levels deep by default
- Automatically excludes `.git`, `.venv`, `node_modules`, etc.
- Identifies projects by markers: `.git`, `pyproject.toml`, `package.json`, etc.

**Command Execution:**
- Default timeout: 300 seconds (5 minutes)
- Tests timeout: 600 seconds (10 minutes)
- Commands run in project directory with proper cwd

## Use Cases

### For Template Maintainers

Keep all projects using your copier template up-to-date:

```bash
repobatch update
repobatch test
```

### For Multi-Project Workflows

Manage dozens of microservices or libraries:

```bash
# Check status across all services
repobatch status --uncommitted

# Run tests before deployment
repobatch test --name "service-*"

# Update dependencies
repobatch run "uv sync" --python
```

### For Project Auditing

Understand your workspace:

```bash
# What do I have?
repobatch list

# What needs updating?
repobatch versions

# What's the test status?
repobatch test
```

## Python API

You can also use repobatch as a library:

```python
from pathlib import Path
from repobatch import discover_projects, run_batch

# Discover all projects
projects = discover_projects(Path.cwd())

# Filter Python projects
python_projects = [p for p in projects if p.is_python]

# Run a command
result = run_batch(python_projects, "pytest")

print(f"Passed: {result.successful}/{result.total}")
```

## Contributing

Contributions welcome! Please check out the [issues](https://github.com/phil65/repobatch/issues).

## License

MIT License - see LICENSE file for details.

## Links

- [Documentation](https://phil65.github.io/repobatch/)
- [Source Code](https://github.com/phil65/repobatch)
- [Issue Tracker](https://github.com/phil65/repobatch/issues)
- [PyPI](https://pypi.org/project/repobatch/)