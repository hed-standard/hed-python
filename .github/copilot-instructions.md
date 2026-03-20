# HED-Python Developer Instructions

> **Local environment**: If `.status/local-environment.md` exists in the repository root, read it first — it contains machine-specific shell, OS, and venv details (e.g. Windows/PowerShell vs Linux/bash) that override the generic commands shown here.

## Code style

- Google-style docstrings; use `Parameters:` not `Args:`
- Line length: 120 characters (configured in `pyproject.toml`)
- Markdown headers use sentence case: capitalize only the first word (and proper nouns/acronyms)
- When creating work summaries, place them in `.status/` at the repository root

## Project overview

HED (Hierarchical Event Descriptors) is a framework for systematically describing events and experimental metadata. This Python repository (`hed-python`) provides the core **hedtools** package for validation, analysis, and transformation of HED-annotated datasets. HED is integrated into two major neuroimaging standards: BIDS (Brain Imaging Data Structure) and NWB (Neurodata Without Borders).

### Related repositories

- **[hed-schemas](https://github.com/hed-standard/hed-schemas)**: Standardized vocabularies (HED schemas) in XML/MediaWiki/OWL formats
- **[hed-specification](https://github.com/hed-standard/hed-specification)**: Formal specification defining HED annotation rules
- **[hed-examples](https://github.com/hed-standard/hed-examples)**: Example datasets and use cases (used as submodule in `spec_tests/`)

### Package distribution

- **PyPI Package**: `hedtools` (install via `pip install hedtools`)
- **Python Version**: 3.10+ required
- **Online Tools**: [hedtools.org](https://hedtools.org) for web-based validation/transformation

## Architecture & core components

### Three-layer architecture

1. **Models Layer** (`hed/models/`): Core data structures

   - `HedString`: Parsed HED tag strings with schema validation
   - `HedTag`: Individual HED tags with canonical forms
   - `HedGroup`: Parenthesized tag groups
   - `HedSchema`: Schema definitions loaded from XML/MediaWiki/OWL
   - `TabularInput`: BIDS-compliant tabular data files with sidecar integration
   - `SpreadsheetInput`: Excel/TSV file handling
   - `Sidecar`: JSON metadata files mapping event codes to HED tags
   - `DefinitionDict`: Manages HED definitions from annotations
   - `QueryHandler`: Search/query interface for HED annotations

2. **Validation Layer** (`hed/validator/`):

   - `HedValidator`: Core tag validation against schema rules
   - `SidecarValidator`: JSON sidecar validation
   - `SpreadsheetValidator`: TSV/Excel validation with BIDS compliance
   - `DefValidator`: Definition/Def-expand tag validation
   - `OnsetValidator`: Temporal onset/offset/duration validation

3. **Tools Layer** (`hed/tools/`):

   - **BIDS** (`bids/`): Dataset discovery, file grouping, inheritance handling
   - **Analysis** (`analysis/`): Event summarization, type analysis, temporal processing, tag counting
   - **Remodeling** (`remodeling/`): Transformation operations on tabular data
   - **Util** (`util/`): Shared utilities for data manipulation

### Key data flow patterns

**Schema Loading & Caching**:

```python
# Always use schema loading utilities from hed.schema
from hed.schema import load_schema_version, load_schema
from hed import HedSchema

# Load specific version (auto-cached in ~/.hedtools/)
schema = load_schema_version("8.4.0")

# Load from local file
schema = load_schema("path/to/schema.xml")
```

**HED String Processing**:

```python
# Standard pattern: parse → validate → analyze
from hed import HedString, HedValidator, DefinitionDict

hed_string = HedString("Event, Action/Button-press", schema)
def_dict = DefinitionDict()  # For definitions if needed
issues = HedValidator(schema).validate(hed_string, def_dict)
```

**BIDS Integration**:

```python
# Use TabularInput for BIDS-compliant processing
from hed import TabularInput

tabular = TabularInput(events_file, sidecar=json_file)
def_dict = tabular.get_def_dict(schema)  # Extract definitions
issues = tabular.validate(schema)  # Validate entire file
```

**Query/Search Operations**:

```python
# Use QueryHandler for searching HED annotations
from hed import QueryHandler, get_query_handlers

query = QueryHandler("Event and Action")
search_results = query.search(hed_string)
```

## Development workflows

### Testing strategy

- Use `unittest` framework exclusively (not pytest)
- Test structure: `tests/` mirrors `hed/` package structure
- Run tests via VS Code tasks or PowerShell:
  - All tests: `.venv\Scripts\python.exe -m unittest discover tests -v`
  - Spec tests: `.venv\Scripts\python.exe -m unittest discover spec_tests -v`
  - Individual test: `.venv\Scripts\python.exe -m unittest tests.models.test_hed_string.TestHedStrings.test_constructor`
- Test data stored in `tests/data/` subdirectories

### Schema integration

- Schemas auto-downloaded and cached in `~/.hedtools/` (cross-platform)
- Local schema copies bundled in releases for offline use
- Test schemas in `tests/data/schema_tests/` for development
- Always validate against multiple schema versions in tests
- Schema formats: XML, MediaWiki, OWL (all equivalent internally)

### Error handling conventions

- Use `ErrorHandler` class for collecting validation issues
- Return structured error dictionaries, never raise for validation failures
- Log with `HedLogger` for debugging, not print statements
- Error codes defined in `hed/errors/error_types.py` and reference `hed-specification` repository
- Error messages in `hed/errors/error_messages.py` and `hed/errors/schema_error_messages.py`

## BIDS-specific patterns

### File discovery & inheritance

```python
# Use BidsDataset for proper BIDS traversal with inheritance
from hed.tools.bids import BidsDataset

dataset = BidsDataset(root_path)
for file_group in dataset.iter_file_groups(["events"]):
    # file_group handles inheritance automatically
    tabular_file = file_group.get_tabular_file()
```

### Sidecar inheritance chain

- BIDS inheritance: dataset → subject → session → file level
- Use `BidsFileGroup` to handle inheritance automatically
- Never manually resolve inheritance - use built-in mechanisms

## Remodeling operations architecture

Located in `hed/tools/remodeling/operations/`:

- All operations inherit from `BaseOp`
- Define `PARAMS` JSON schema for validation
- Implement `do_op(dispatcher, df, name, sidecar=None)` method
- Use `Dispatcher` class to orchestrate multi-step transformations
- Operations are JSON-configurable for reproducible analysis pipelines

## Development environment

### Setup

**Always** install in editable mode and activate the virtual environment before running any commands. See `.status/local-environment.md` for OS-specific activation and command syntax.

```bash
# Generic (adjust path separators / activation script for your OS)
pip install -e ".[dev,test,docs,examples]"
```

### Package structure

- Entry point: `hed/__init__.py` exports main user API
- Unified CLI entry point: `hedpy` → `hed/cli/cli.py`
- Legacy CLI scripts in `hed/scripts/` (deprecated — prefer `hedpy`)
- Version managed by `setuptools-scm`; `hed/_version.py` is auto-generated — do not edit
- Configuration: `pyproject.toml` (build, ruff, typos, setuptools)

### Dependencies

- Python 3.10+ required; declared in `pyproject.toml`
- Core: `pandas<3.0`, `numpy>=2`, `defusedxml`, `portalocker`, `click`, `semantic-version`, `inflect`, `openpyxl`
- Dev extras: `ruff`, `typos`, `mdformat`; install with `pip install -e ".[dev]"`

### Linting and formatting

Run before every commit — these are enforced by CI:

```bash
# Check for lint errors
ruff check hed/ tests/

# Check formatting
ruff format --check hed/ tests/

# Auto-fix lint + format
ruff check --fix --unsafe-fixes hed/ tests/
ruff format hed/ tests/

# Spell check (excludes tests/, yaml, json, xml — see pyproject.toml [tool.typos])
typos
```

Ruff rules and line length (120) are configured in `pyproject.toml` under `[tool.ruff]`.

### Running tests

```bash
# All unit tests
python -m unittest discover tests -v

# Spec-compliance tests (requires git submodules: spec_tests/hed-tests, hed-examples, hed-schemas)
python -m unittest discover spec_tests -v

# Single test
python -m unittest tests.models.test_hed_string.TestHedStrings.test_constructor
```

### CI/CD pipeline (`.github/workflows/`)

| Workflow      | File                  | Trigger                     | Purpose                                                                 |
| ------------- | --------------------- | --------------------------- | ----------------------------------------------------------------------- |
| Tests         | `ci.yaml`             | push/PR to any branch       | Python 3.10–3.14 on Ubuntu (main branch); 3.10 & 3.13 on other branches |
| Coverage      | `ci_cov.yaml`         | push to main only           | Coverage report, Python 3.10                                            |
| Windows tests | `ci_windows.yaml`     | push/PR to main             | Python 3.10–3.12 on Windows                                             |
| Ruff          | `ruff.yaml`           | push/PR to main             | Lint + format check                                                     |
| Typos         | `typos.yaml`          | push/PR to main             | Spelling check                                                          |
| Spec tests    | `spec_tests.yaml`     | push/PR to any branch       | HED specification compliance, Python 3.10                               |
| Docs          | `docs.yaml`           | push/PR to main             | Sphinx build                                                            |
| Notebooks     | `notebook_tests.yaml` | push/PR to main             | Jupyter notebook execution                                              |
| Links         | `links.yaml`          | scheduled + manual dispatch | Dead-link checker (lychee)                                              |

To replicate CI locally, run `ruff check`, `ruff format --check`, `typos`, and `python -m unittest discover tests -v` before pushing.

## Schema development notes

- Schemas support multiple formats: (MediaWiki, XML, OWL) but all schema formats are equivalent and are loaded into the same internal representation.
- Library schemas can be merged with base schema if they have the withStandard attribute in their header.
- Schema validation includes attribute checking, unit validation
- Use `HedSchemaGroup` for multi-schema validation scenarios
- Schema I/O handled by modules in `hed/schema/schema_io/`

## Common pitfalls to avoid

- Don't use hardcoded schema versions in production code
- Don't modify schemas in-place — they're cached/shared across processes and are immutable
- Always activate the virtual environment before running Python/pip commands
- Check `.status/local-environment.md` for shell-specific command syntax (e.g. PowerShell vs bash)
- Don't mix pytest and unittest — this project uses `unittest` exclusively
- Always use absolute imports from `hed` package, not relative imports
- `hed/_version.py` is auto-generated by `setuptools-scm` — never edit it manually
- `spec_tests/` contains git submodules; run `git submodule update --init --recursive` if spec tests fail to find data
