# AGENTS.md

This file provides guidance for AI coding agents working on the `EagleClassLists` project.

## Important Info For AI Agents

- **Always use `uv run` prefix** for running any Python commands (pytest, mypy, ruff, etc.)
- **Never modify pyproject.toml** without explicit approval
- **Run tests before committing**: Always verify `uv run pytest` passes
- **Check types**: Run `uv run mypy` to catch type errors
- **Format code**: Run `uv run ruff check --fix` before committing
- **Update CHANGELOG.md**: Document all user-facing changes
- **Respect line length**: Keep lines under 100 characters
- **Use double quotes**: Follow project convention for string literals
- **Add type hints**: All new functions should have proper type annotations
- **Improve Parallel Tox Output**: Use the `--parallel-no-spinner` flag when running `uv tox p`
- **Don't Suppress Warnings**: Do not suppress warnings or errors in tools without explicit approval
- **Use Google Docstrings**: Use the Google docstring format

## Project Resources

**Project Information**: See README.md
**Running Tests**: See CONTRIBUTING.md
**Tooling Information**: See CONTRIBUTING.md

## Code Style and Conventions

### Python Style (PEP 8)
- **Line length**: 100 characters (configured in pyproject.toml)
- **Quote style**: Double quotes
- **Indentation**: 4 spaces
- **Import sorting**: Enabled (isort via ruff)

## Git Workflow

### Branch Naming
- `feature/*` - New features (e.g., `feature/add-export-functionality`)
- `bugfix/*` - Bug fixes (e.g., `bugfix/fix-yaml-parsing`)
- `docs/*` - Documentation updates
- `chore/*` - Maintenance tasks

### Commit Messages
Format:
```
(BREAKING) description

Optional body with more details
```

- Use `(BREAKING)` prefix only for breaking API changes requiring major version bump
- Keep description concise and meaningful
- Focus on "why" rather than "what"
- **AI-generated commits**: Prefix commit messages with 🤖 emoji to identify AI-generated changes (e.g., `🤖 Add new validation function`)
