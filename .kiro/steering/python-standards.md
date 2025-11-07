# Python Development Standards

This document defines the technical standards and tooling requirements for all Python development in this workspace.

## Python Version

- Use Python 3.12 for all projects
- Enforce type hints in all Python modules
- Include type stubs for all dependencies where available

## Dependency Management

- Use `uv` for all package installation and dependency management
- Maintain dependencies in `pyproject.toml`
- Generate lock files for reproducible installations
- Store virtual environments in `.venv` directory within project root

## Virtual Environment

- Create virtual environments in `.venv` directory at project root
- Use `uv run` to execute commands within the virtual environment automatically
- Exclude `.venv` from version control

## Type Checking

- Use `mypy` with strict type checking enabled
- Validate all Python files in the project
- Configure mypy through `pyproject.toml`
- Ensure type errors are reported with file locations and descriptions

## Code Quality

### Formatting and Linting
- Use `ruff` for both code formatting and linting
- Format all Python files automatically with ruff
- Check for code quality issues, style violations, and common anti-patterns
- Configure ruff through `pyproject.toml`

## Testing

- Use `pytest` as the testing framework
- Place test files in `tests/` directory
- Support fixtures and parameterized tests
- Include pytest as a development dependency
- Report test results with pass/fail status and coverage information

## Project Structure

All Python projects should follow this structure:

```
project-root/
├── src/                  # Application source code
│   └── package_name/
├── tests/               # Test files
├── .venv/               # Virtual environment (not in git)
├── .gitignore          # Python-specific exclusions
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # Project documentation
```

### Key Points:
- Use `src/` layout for application code
- Include `tests/` directory for test files
- Exclude virtual environments, cache files (`__pycache__`, `*.pyc`), and build artifacts from version control
- Include comprehensive `.gitignore` for Python projects

## UI Development

- Use `PySide6` for graphical user interfaces
- Include PySide6 type stubs for type checking support
- Manage PySide6 installation through uv

## Logging

- Use `RichHandler` from the `rich` library for console output
- Display log messages with color-coded severity levels
- Format log output with timestamps and module information
- Include `rich` as a project dependency

## CLI Applications

- Use `Typer` for building command-line interfaces
- Implement automatic help generation with `--help` flag
- Support extensible command-line options
- Parse and validate command-line arguments
- Include Typer as a project dependency

## Configuration Management

- Use `pydantic` for type-safe configuration validation
- Validate configuration values against defined types
- Provide clear error messages for invalid configuration
- Support loading configuration from files and environment variables
- Include pydantic as a project dependency

## Development Dependencies

Separate development dependencies from runtime dependencies in `pyproject.toml`:

**Runtime dependencies:**
- PySide6
- rich
- typer
- pydantic

**Development dependencies:**
- mypy
- ruff
- pytest
- pytest-cov (for coverage reporting)

## Example pyproject.toml Structure

```toml
[project]
name = "your-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "PySide6",
    "rich",
    "typer",
    "pydantic",
]

[project.optional-dependencies]
dev = [
    "mypy",
    "ruff",
    "pytest",
    "pytest-cov",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

## Workflow

1. Initialize project with `uv init`
2. Set up `.venv` with `uv venv`
3. Install dependencies with `uv pip install -e ".[dev]"`
4. Run type checking with `uv run mypy src/`
5. Format code with `uv run ruff format .`
6. Lint code with `uv run ruff check .`
7. Run tests with `uv run pytest`

Note: `uv run` automatically uses the project's virtual environment, so no manual activation is needed.
