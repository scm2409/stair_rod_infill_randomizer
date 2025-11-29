---
inclusion: always
---

# Python Development Standards

Technical standards and tooling requirements for Python development in this workspace.

## Python Version

- Python 3.12 required
- Type hints mandatory in all modules
- Include type stubs for dependencies

## Type Hints

**CRITICAL**: Avoid using `Any` type hint.

- The `Any` type hint defeats the purpose of type checking and must be avoided
- Only use `Any` as a last resort when no stricter type is possible

### TODO Comments for Future Tasks

**CRITICAL**: When implementing code that depends on classes/features from future tasks:

1. **Add TODO comments** with this exact pattern:
   ```python
   # TODO(Task X.Y): Description of what needs to be implemented
   # Example: TODO(Task 4.1): Replace BaseModel with RectangularRailingShapeParameters when implemented
   ```

2. **Before writing tests** for a task, search for all TODOs with current task number:
   ```bash
   grep -r "TODO(Task X.Y)" src/
   ```

3. **Implement all TODOs** for the current task before writing tests

4. **Remove the TODO comment** after implementation

**Pattern**: `TODO(Task X.Y): <description>`
- X.Y = task number from tasks.md
- Description = what needs to be done

### Pre-Task Code Review

**CRITICAL**: Before starting any task implementation:

1. **Review the existing codebase** to check if the class/feature is already implemented or partially implemented
2. **Search for the class name** in the codebase:
3. **If code exists**:
   - Evaluate if the existing implementation is complete and correct
   - If the new implementation is better, replace the old one
   - Update all imports and references to use the correct location
   - Ensure no duplicate classes exist in different locations

4. **If code is partially implemented**:
   - Complete the existing implementation rather than creating a new one
   - Add missing features to the existing class
   - Ensure consistency with the existing code style

### Protocols vs Abstract Base Classes

**When to use Protocols**:
- Prefer Protocols for library boundaries and tests where you don't control the concrete types
- Use when you want structural subtyping (duck typing with type safety)
- Ideal for defining interfaces that external code will implement

**When to use ABCs (Abstract Base Classes)**:
- Prefer ABCs when you want to share base behavior and guard against incomplete implementations at runtime
- Use when you control all implementations and want to enforce a contract


## Dependency Management

- Use `uv` for package management (not pip)
- Dependencies in `pyproject.toml`, lock file in `uv.lock`
- Virtual environment in `.venv/` (excluded from git)
- Execute commands with `uv run <command>` (auto-activates venv)

## Code Quality Tools

- **Type checking**: `uv run mypy` - strict mode, checks both src/ and tests/, must pass with zero errors
- **Formatting**: `uv run ruff format .` - auto-format all files (run once at the end of each task for the entire project)
- Configure via `pyproject.toml`

**Note**: No need to run `ruff check` separately - just run `ruff format` at the end to ensure consistent formatting across the entire project.

### CRITICAL: Zero Tolerance for Errors

**MANDATORY RULE**: Before completing ANY task, ALL mypy and test errors MUST be fixed, regardless of whether they are related to the current implementation.

**Requirements:**
1. **Run full test suite**: `uv run pytest --cov=railing_generator --cov-report=term-missing`
2. **Run mypy on entire codebase**: `uv run mypy src/`
3. **Fix ALL errors**: Even if errors are unrelated to your current task, you MUST fix them
4. **No exceptions**: It is NOT allowed to complete a task with ANY mypy or testing errors in the project
5. **Document fixes**: If fixing unrelated errors, briefly note what was fixed and why


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

### __init__.py Files

**CRITICAL**: Keep `__init__.py` files minimal.

**Default pattern** (preferred):
```python
"""Package description."""
```

**Only add exports when necessary**:
- When following established Python best practices

**If adding exports, document why**

**Never add**:
- Complex logic
- Initialization code
- Side effects
- Imports just for convenience

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

**CRITICAL**: Avoid generic names - use specific, descriptive names.

### General Naming Rules

- **Never use generic names** when a more specific name exists
- **Prefer longer, descriptive names** over short, ambiguous ones
- **Use domain-specific terminology** consistently throughout the codebase

**Examples of generic vs specific names**:

❌ **Too Generic**:
```python
generator_type: str  # What kind of generator?
enumeration_visible: bool  # Enumeration of what?
parameters: BaseModel  # Parameters for what?
```

✅ **Specific and Clear**:
```python
infill_generator_type: str  # Clearly an infill generator
rod_annotation_visible: bool  # Clearly annotating rods
infill_generator_parameters: InfillGeneratorParameters  # Clearly for infill generation
```

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
uv run mypy                   # Must pass (checks src/ and tests/)
uv run pytest --cov=railing_generator --cov-report=term-missing
```

#### Before Completing
1. **ALWAYS run ruff format for the entire project**: `uv run ruff format .`
   - This ensures consistent formatting across all files
   - Run this once at the end, not after each individual change
   - No need to run `ruff check` separately - formatting handles style issues
2. Verify coverage >= baseline
3. All checks pass: mypy ✅ pytest ✅ coverage ✅
4. Note final coverage (e.g., "Ending: 58%")

**Quick check**: `uv run mypy && uv run pytest --cov=railing_generator --cov-report=term-missing && uv run ruff format .`
