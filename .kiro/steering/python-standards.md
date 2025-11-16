---
inclusion: always
---

# Python Development Standards

Technical standards and tooling requirements for Python development in this workspace.

## Python Version

- Python 3.12 required
- Type hints mandatory in all modules
- Include type stubs for dependencies

## Dependency Management

- Use `uv` for package management (not pip)
- Dependencies in `pyproject.toml`, lock file in `uv.lock`
- Virtual environment in `.venv/` (excluded from git)
- Execute commands with `uv run <command>` (auto-activates venv)

## Code Quality Tools

- **Type checking**: `uv run mypy src/` - strict mode, must pass with zero errors
- **Linting**: `uv run ruff check .` - must pass before committing
- **Formatting**: `uv run ruff format .` - auto-format all files
- Configure via `pyproject.toml`

### Mypy Type Ignore Policy

**CRITICAL**: Before adding any `# type: ignore` comment, you MUST ask the user for approval.

**Exceptions** (pre-approved, no need to ask):
1. **Pydantic `@computed_field` with `@property`**: Use `# type: ignore[prop-decorator]`
   ```python
   @computed_field  # type: ignore[prop-decorator]
   @property
   def computed_value(self) -> float:
       return self.some_calculation()
   ```
   - This is a known Pydantic/mypy compatibility issue
   - Always use the specific `[prop-decorator]` code, not the broader `[misc]`
   - Reference: https://docs.pydantic.dev/2.0/usage/computed_fields/

**For all other cases**: Research the issue, propose a solution, and wait for user approval before adding `# type: ignore`.

## Testing

**CRITICAL**: Tests are part of implementation, not separate tasks.

### Requirements
- Every implementation task MUST include tests
- Write tests immediately after implementation
- Use `pytest` with `pytest-qt` for GUI testing
- Test files in `tests/` mirror `src/` structure
- Run: `uv run pytest --cov=railing_generator --cov-report=term-missing`

### Coverage Policy
- Record baseline coverage before starting task
- Coverage must NOT decrease after task completion
- Add tests if coverage drops below baseline

### Test Types
- **Unit tests**: Individual functions/classes in isolation
- **Integration tests**: Component interactions
- **UI tests**: PySide6 GUI (optional, can defer)

## Project Structure

```
project-root/
├── src/package_name/
│   ├── __main__.py          # Entry point
│   ├── app.py               # Application setup
│   ├── domain/              # Business logic, models
│   ├── application/         # Orchestration, workflows
│   ├── presentation/        # UI layer (PySide6)
│   └── infrastructure/      # File I/O, config, logging
├── tests/                   # Mirror src/ structure
├── conf/                    # Hydra configs (YAML)
│   ├── config.yaml          # Main config
│   └── [feature]/           # Config groups
├── temp/                    # NEVER read or modify this
├── pyproject.toml
└── README.md
```

**Key Rules**:
- `src/` layout with layered architecture
- Hydra configs in `conf/`, main file is `config.yaml`
- `temp/` is for humans only - AI must ignore completely
- Exclude from git: `.venv/`, `__pycache__/`, `*.pyc`, Hydra outputs

## Architecture

### Layered Architecture
- **Domain**: Business logic, Pydantic models, algorithms
- **Application**: Orchestration, workflows, state
- **Presentation**: PySide6 UI, user interaction
- **Infrastructure**: File I/O, config, logging

### Design Patterns
- **Strategy**: Interchangeable algorithms (generators)
- **Factory**: Create instances from type strings
- **Observer**: PySide6 Signal/Slot for events
- **Repository**: Config and data access abstraction

## Geometry Operations

- Use `Shapely` for 2D geometry: `Point`, `LineString`, `Polygon`, `MultiPolygon`
- Use `STRtree` for spatial indexing with many queries
- In Pydantic models with Shapely: `model_config = {"arbitrary_types_allowed": True}`

## UI Development (PySide6)

### Signal/Slot Pattern
- Use Signal/Slot for events and progress (type-safe, thread-safe)
- Define typed signals: `Signal(dict)`, `Signal(object)`
- Prefer signals over callbacks
- Components emit; UI connects to slots

### Threading Pattern
```python
from PySide6.QtCore import QObject, QThread, Signal

class Worker(QObject):
    progress_updated = Signal(dict)
    finished = Signal(object)
    
    def run(self):
        self.progress_updated.emit({"status": "working"})
        result = do_work()
        self.finished.emit(result)

# Main thread:
thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
thread.start()
```

### Vector Graphics
- Use `QGraphicsView`/`QGraphicsScene` for 2D rendering
- Efficient for thousands of items, hardware-accelerated
- Built-in zoom/pan

## Logging

- Use `RichHandler` from `rich` for color-coded console output
- Default level: INFO (use `-d`/`--debug` flag for DEBUG)
- Configure early in startup

## CLI Applications

- Use `Typer` for CLI with auto-generated `--help`
- Always include `-d`/`--debug` flag to control log level

## Naming Conventions

**CRITICAL**: Always append unit suffix to physical quantities.

### Unit Suffixes
- Length: `_cm`, `_m`, `_mm`
- Mass: `_kg`, `_g`
- Angle: `_deg`, `_rad`
- Time: `_sec`, `_ms`, `_min`
- Area: `_cm2`, `_m2`
- Speed: `_m_s`, `_km_h`
- Mass per length: `_kg_m`

```python
# Correct
post_length_cm: float = 150.0
weight_per_meter_kg_m: float = 0.5
max_angle_deg: float = 30.0

# Wrong - ambiguous units
post_length: float = 150.0
weight_per_meter: float = 0.5
```

## Data Validation and Models

### Dataclasses vs Pydantic

**Dataclasses**: Hydra config defaults from YAML
- Example: `StairShapeDefaults`, `RandomGeneratorDefaults`

**Pydantic**: UI parameters, domain models, runtime validation
- Example: `StairShapeParameters`, `Rod`, `InfillResult`
- Use for: computed fields, complex validation, serialization

**Flow**: `YAML (Hydra) → Dataclass (defaults) → Pydantic (UI/domain) → Logic`

### Dataclass Pattern (Hydra Configs)

```python
from dataclasses import dataclass
from hydra.core.config_store import ConfigStore

@dataclass
class FeatureDefaults:
    param_one: float = 100.0
    weight_kg_m: float = 0.5

cs = ConfigStore.instance()
cs.store(group="feature", name="default", node=FeatureDefaults)
```

### Pydantic Pattern (UI/Domain Models)

```python
from pydantic import BaseModel, Field, field_validator, computed_field

class FeatureParameters(BaseModel):
    param_one: float = Field(gt=0, description="Parameter one")
    weight_kg_m: float = Field(gt=0)
    
    @field_validator('param_one')
    @classmethod
    def validate_param(cls, v: float) -> float:
        if v > 1000:
            raise ValueError('Value too large')
        return v
    
    @computed_field
    @property
    def computed_value(self) -> float:
        return self.param_one * 2

# For Shapely types
model_config = {"arbitrary_types_allowed": True}
```

**Key methods**: `model_dump()`, `model_dump_json()`, `model_validate()`

## Configuration Management (Hydra)

- Config files in `conf/`, main file is `conf/config.yaml`
- Use dataclasses for structured configs (not Pydantic)
- Config groups in subdirectories under `conf/`
- Support CLI overrides

```python
from dataclasses import dataclass
import hydra
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

@dataclass
class FeatureConfig:
    param_one: str = "default"
    param_two: int = 100

@dataclass
class AppConfig:
    feature: FeatureConfig
    debug: bool = False

cs = ConfigStore.instance()
cs.store(name="base_config", node=AppConfig)
cs.store(group="feature", name="default", node=FeatureConfig)

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: AppConfig):
    config_obj = OmegaConf.to_object(cfg)  # Convert to dataclass
```

## Dependencies

**Runtime**: PySide6, PySide6-stubs, pydantic, shapely, hydra-core, omegaconf, rich, typer, ezdxf, numpy

**Dev**: mypy, ruff, pytest, pytest-qt, pytest-cov

## pyproject.toml Structure

```toml
[project]
name = "project-name"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.6.0",
    "PySide6-stubs",
    "pydantic>=2.0.0",
    "shapely>=2.0.0",
    "hydra-core>=1.3.0",
    "omegaconf>=2.3.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
]

[project.optional-dependencies]
dev = ["mypy>=1.0.0", "ruff>=0.1.0", "pytest>=7.0.0", "pytest-qt>=4.0.0", "pytest-cov"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Workflow

### Initial Setup
```bash
uv init
uv venv
uv pip install -e ".[dev]"
```

### Task Workflow

**CRITICAL**: Follow for every task.

#### Before Starting
1. Record baseline coverage: `uv run pytest --cov=railing_generator --cov-report=term-missing`
2. Note TOTAL percentage (e.g., "Starting: 51%")

#### During Development
Run after each change:
```bash
uv run mypy src/              # Must pass
uv run ruff check .           # Must pass
uv run ruff format .          # Auto-format
uv run pytest --cov=railing_generator --cov-report=term-missing
```

#### Before Completing
1. Verify coverage >= baseline
2. All checks pass: mypy ✅ ruff ✅ pytest ✅ coverage ✅
3. Note final coverage (e.g., "Ending: 58%")

**Quick check**: `uv run mypy src/ && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing`
