# Railing Infill Generator

Desktop application for generating rod arrangements for railing frames.

> **Note:** This is my first project written using Kiro AI. It's primarily a learning exercise and test project to explore AI-assisted development. The project may never reach a fully functional stage.

## Features

- Multiple railing frame shapes (stair, rectangular)
- Extensible generator system (random placement with quality evaluation)
- Real-time visual feedback during generation
- Bill of materials (BOM) generation
- Export to DXF format
- Save/load projects

## Requirements

- Python 3.12+
- uv (for dependency management)

## Installation

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"
```

## Usage

```bash
# Run application
uv run railing-generator

# Run with debug logging
uv run railing-generator --debug

# Run with console output
uv run railing-generator --verbose

# Run with custom config directory
uv run railing-generator --config-path /path/to/conf
```

## Development

### Development Workflow

**IMPORTANT:** Run these checks after every code change:

```bash
# 1. Type checking (must pass) - checks both src/ and tests/
uv run mypy

# 2. Linting (must pass)
uv run ruff check .

# 3. Format code
uv run ruff format .

# 4. Run tests with coverage (must pass)
uv run pytest --cov=railing_generator --cov-report=term-missing
```

### Quick Check (All at Once)

```bash
uv run mypy && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing
```

### Additional Commands

```bash
# Run tests with HTML coverage report
uv run pytest --cov=railing_generator --cov-report=html
# Then open htmlcov/index.html in browser

# Run tests with coverage for specific module
uv run pytest tests/infrastructure/ --cov=railing_generator.infrastructure --cov-report=term-missing

# Auto-fix linting issues where possible
uv run ruff check . --fix
```

## Project Structure

```
railing-infill-generator/
├── src/
│   └── railing_generator/
│       ├── __main__.py          # Entry point
│       ├── app.py               # Application setup
│       ├── domain/              # Business logic
│       ├── application/         # Orchestration
│       ├── presentation/        # UI layer
│       └── infrastructure/      # External services
├── conf/                        # Hydra configs
├── tests/                       # Test files
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

## License

GPL
