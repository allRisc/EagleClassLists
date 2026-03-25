# Contributing

## Prerequisites

- Python >=3.12
- UV package manager

## Getting Setup

The `EagleClassLists` tool uses `uv` as its packaging and tool running utility.

## Development Workflow

### Testing - pytest

Unit tests validate functionality and are stored in the `./tests/` directory.

```bash
uv run pytest              # Run all unit tests
uv run pytest tests/test_module.py::test_function  # Run specific test
```

### Type Checking - mypy

Catches type-related errors at development time, ensuring code reliability.

```bash
uv run mypy
```

### Code Quality - ruff

Enforces PEP8 compliance and catches common bugs automatically.

```bash
uv run ruff check         # Check code style
uv run ruff check --fix   # Auto-fix style issues
```

### Integration Testing - tox

Runs all test suites across Python versions and environments to ensure compatibility.

```bash
uv run tox               # Run all test suites
uv run tox p             # Run tests in parallel (faster)
```

## Code Formatting Guidelines

All Python code must comply with [PEP 8](https://peps.python.org/pep-0008/).

Project-specific settings are configured in `pyproject.toml`:
- Line length: 100 characters
- Python version: 3.12+
- Import sorting: enabled (isort)
- Quote style: double quotes

## Branching and Commit Conventions

### Branch Naming

Use the following format for branch names:
- `feature/*` - New features (e.g., `feature/add-export-functionality`)
- `bugfix/*` - Bug fixes (e.g., `bugfix/fix-yaml-parsing`)
- `docs/*` - Documentation updates
- `chore/*` - Maintenance tasks

### Commit Messages

Use the following format for commit messages:
```
(BREAKING) description

Optional body with more details
```

Where the `BREAKING` part is only appended for breaking API changes which will require a major version bump.

## Before Making a PR

Ensure all of the following are complete:

- [ ] All tests pass: `uv run tox` (or `uv run tox p` for parallel)
    - [ ] Code is formatted: `uv run ruff check --fix`
    - [ ] Type checking passes: `uv run mypy`
- [ ] CHANGELOG.md updated with your changes
- [ ] Documentation updated (docstrings, README, docs/)
- [ ] Branch follows naming convention: `feature/*`, `bugfix/*`, etc.
- [ ] Commit messages follow Conventional Commits format
- [ ] PR description clearly explains the changes and motivation

## Debugging Tips

### Running Specific Tests

```bash
# Run tests matching a pattern
uv run pytest -k "pattern"

# Run with verbose output
uv run pytest -v

# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x
```

### Type Checking with Details

```bash
# Show detailed error information
uv run mypy --show-error-codes --show-error-context
```

### Building Documentation Locally

```bash
uv run tox -e docs_html   # Build HTML docs
uv run tox -e docs_dirhtml # Build dirhtml docs
```

## Common Issues and Troubleshooting

### UV Command Not Found

- Ensure `uv` is installed and in your PATH
- Try `python -m pip install uv`
- Check with your VDT team if using module-based installation

### Import Errors When Running Tests

- Ensure you're running commands with `uv run` (not directly)
- Try: `uv sync` to update dependencies

### Tests Pass Locally but Fail in CI

- Run the full test suite: `uv run tox` (not just `pytest`)
- Check Python version: `python --version` (must be 3.12+)

