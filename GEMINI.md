# easy-worktree Development Environment

This file provides context for future AI development sessions.

## Project Overview
- **Name**: easy-worktree
- **Description**: A CLI tool for simple Git worktree management.
- **Languages**: Python (>= 3.10)

## Development Stack
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Build System**: [Hatch](https://hatch.pypa.io/) (`hatchling` backend)
- **Formatting & Linting**: [Ruff](https://beta.ruff.rs/docs/)
- **Configuration**: `pyproject.toml` (PEP 621 compliant)

## Key Files
- `easy_worktree/__init__.py`: Main implementation. All CLI logic resides here.
- `pyproject.toml`: Dependency and metadata configuration.
- `tests/test_integration.py`: Main integration test suite.

## Development Workflows

### Setup
Ensure `uv` is installed. Then run:
```bash
uv pip install --editable .
```

### Running the CLI
Run directly using uv:
```bash
uv run wt <command>
```

### Formatting
```bash
uvx ruff format .
```

### Testing
Run the integration tests:
```bash
uv run python tests/test_integration.py
```
> [!IMPORTANT]
> Some tests require a Git repository to exist at `tmp/memo` relative to the repository root.

## Project Characteristics
- **Multi-language Support**: Supports English and Japanese messages. Detects language based on the `LANG` environment variable.
- **Architecture**: Most functionality is contained within `easy_worktree/__init__.py`. It uses `subprocess` to call `git` commands directly.
