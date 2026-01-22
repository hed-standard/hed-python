# Release 0.9.0 January 22, 2026

The main purpose of this release is to clean up the CLI for the hedtools and to improve the documentation in preparation for release of 1.0.0, which will be a breaking release.

## Major changes

### Command-line interface (CLI) overhaul

**Complete CLI redesign with Git-Style commands**

- Introduced unified `hedpy` command-line interface with git-style subcommand structure
- Replaced legacy standalone scripts with organized command groups: `validate`, `schema`, `extract`
- Added comprehensive help system with detailed command documentation
- Implemented click-option-group for organized command options

**New commands:**

- `hedpy validate bids-dataset` - BIDS dataset validation
- `hedpy validate string` - HED string validation
- `hedpy validate sidecar` - JSON sidecar validation
- `hedpy validate tabular` - TSV file validation
- `hedpy schema validate` - Schema file validation
- `hedpy schema convert` - Schema format conversion
- `hedpy schema add-ids` - HED ID management
- `hedpy extract bids-sidecar` - Sidecar template extraction
- `hedpy extract tabular-summary` - Tabular file summarization

**Enhanced output options:**

- Multiple output formats: text, json, json_pp (pretty-printed JSON with metadata)
- Configurable error limiting per error type
- File-based and per-error error counting options
- Comprehensive logging configuration with file output support

### Documentation improvements

**Major documentation restructuring**

- Complete rewrite of user guide with comprehensive examples and workflows
- Added detailed Jupyter notebook documentation section
- Created extensive CLI documentation with command examples
- Improved API reference organization with clearer section headers
- Enhanced introduction page with quick start examples
- Added troubleshooting section with common issues and solutions
- Updated the RELEASE_GUIDE to better reflect current release process

**New documentation features:**

- Sidebar quick links for easy navigation
- Custom CSS styling for improved readability
- Dark mode support with proper color theming
- Brand customization with project logo and name
- Better code block formatting and syntax highlighting
- Comprehensive examples for all major workflows

### Jupyter notebook examples

**New example notebooks (examples/ directory)**

- `extract_json_template.ipynb` - Generate JSON sidecar templates
- `find_event_combinations.ipynb` - Find unique value combinations
- `merge_spreadsheet_into_sidecar.ipynb` - Merge edited annotations
- `sidecar_to_spreadsheet.ipynb` - Convert JSON to spreadsheet format
- `summarize_events.ipynb` - Summarize event file contents
- `validate_bids_dataset.ipynb` - Validate BIDS datasets
- `validate_bids_dataset_with_libraries.ipynb` - Validate with library schemas
- `validate_bids_datasets.ipynb` - Batch validate multiple datasets
- `validate_bids_dataset_nondefault. ipynb` - Non-standard validation scenarios

**Notebook infrastructure:**

- Added comprehensive README for notebooks with usage instructions
- Created optional dependencies group for Jupyter support
- Added notebook testing framework for validation

### Core functionality enhancements

**Validation improvements:**

- Enhanced placeholder validation with units (e.g., "# m-per-s^2")
- Fixed unit class validation for placeholders with units
- Improved error reporting with better categorization
- Added support for --no-log option to disable all logging

**TabularSummary Enhancements:**

- Added categorical limit feature to prevent memory issues with high-cardinality columns
- Implemented overflow column tracking for truncated summaries
- Added categorical counts metadata (total values and file counts)
- Improved summary statistics and reporting

**Schema processing:**

- Enhanced schema validation error messages with specification links
- Fixed schema attribute inheritance handling
- Improved JSON schema format support
- Updated conversion factor validation

### Script and utility improvements

**New scripts:**

- `hed/scripts/validate_hed_string.py` - Standalone HED string validation
- `hed/scripts/validate_hed_sidecar.py` - Standalone sidecar validation
- `hed/scripts/validate_hed_tabular.py` - Standalone tabular file validation
- `hed/scripts/extract_tabular_summary.py` - Non-BIDS tabular summarization
- `hed/scripts/script_utils.py` - Shared utility functions for scripts

**Script uilities:**

- Centralized logging setup across all scripts
- Standardized validation result formatting
- Consistent error handling and reporting
- Improved argument parsing with organized option groups

### Dependencies and requirements

**Updated Dependencies:**

- Added `click-option-group>=0.5.0` for CLI option organization
- Updated `wordcloud` from 1.9.4 to 1.9.5
- Updated `black` to >=26.1.0 with Jupyter support
- Added `mdformat>=0.7.0` and `mdformat-myst>=0.1.5` for markdown formatting
- Updated Sphinx and documentation dependencies

**New Optional Dependency Groups:**

- `examples` - Jupyter notebook support (jupyter, notebook, nbformat, ipykernel)
- Updated `docs` group with version constraints
- Enhanced `dev` group with markdown formatting tools

### Testing enhancements

**Schema test data:**

- Added extensive JSON test data for schema validation
- New test files for schema attribute validation
- Tests for conversion factors, HED IDs, unit classes, value classes
- Tests for character validation and deprecation handling
- Tests for library schema attributes

**Test organization:**

- Improved test structure with categorized error cases
- Added common causes and correction strategies to test metadata
- Enhanced test documentation with specification references
- Moved JSON test references from the hed-specification repository to the hed-tests repository

### Documentation files

**Updated documentation:**

- Comprehensive CHANGELOG.md updates
- Enhanced CONTRIBUTING.md with detailed workflows
- Improved README. md with better examples and structure
- Updated RELEASE_GUIDE.md with detailed release procedures

**Configuration files:**

- Added `.lycheeignore` for link checker exclusions
- Added `lychee.toml` for link validation configuration
- Enhanced `.gitignore` with additional patterns
- Updated workflow configurations for GitHub Actions

## GitHub actions and CI/CD

### Workflow updates

**Enhanced CI pipeline:**

- Updated cache actions from v4 to v5 across all workflows
- Changed default branch references from `develop` to `main`
- Renamed and reorganized workflow files (. yml → .yaml)
- Improved Sphinx documentation build workflow

**New workflows:**

- `links. yaml` - Lychee link checker for documentation (weekly schedule)
- `mdformat.yaml` - Markdown formatting validation
- `notebook_tests.yaml` - Jupyter notebook validation
- `ruff.yaml` - Python linting with Ruff

**Workflow improvements:**

- Updated codespell workflow to use main branch
- Enhanced documentation deployment workflow
- Added proper artifact handling for GitHub Pages
- Improved test isolation and parallel execution

## File organization and structure

### Repository structure changes

**Removed:**

- Removed `spec_tests/hed-specification` submodule (replaced with hed-tests)
- Removed remodeling CLI commands (moved to separate repository)

**Added:**

- New `examples/` directory with Jupyter notebooks and README
- New `hed/scripts/script_utils.py` for shared utilities
- New validation scripts for string, sidecar, and tabular files
- New extract script for non-BIDS tabular summaries

**Updated:**

- Moved documentation assets from `docs/assets/` to `docs/_static/`
- Enhanced documentation structure with better organization
- Improved test data organization in spec_tests/

### Code quality and formatting

**Black formatting:**

- Applied Black code formatter across entire codebase
- Updated Black configuration for Python 3.14 support
- Enhanced exclusion patterns for auto-generated files

**Ruff linting:**

- Added comprehensive Ruff configuration
- Implemented linting rules for code quality
- Added automated linting in CI pipeline

**Markdown formatting:**

- Added mdformat for consistent markdown styling
- Configured myst-parser support
- Automated markdown checking in CI

## Bug fixes and minor improvements

### Schema handling

- Fixed MediaWiki → MEDIAWIKI naming consistency
- Improved schema format detection and conversion
- Enhanced schema attribute validation
- Fixed inheritance handling for schema attributes

### Validation

- Fixed unit validation for placeholders with units
- Improved error message clarity and documentation links
- Fixed definition extraction from sidecars
- Enhanced sidecar validation error reporting

### Error reporting

- Updated documentation link format in error messages
- Improved error categorization and grouping
- Added error iteration utility (`iter_errors`)
- Enhanced printable issue formatting

### Miscellaneous

- Fixed various typos and formatting issues
- Improved code comments and docstrings
- Enhanced type hints and error handling
- Cleaned up deprecated code patterns

## Breaking changes

**CLI command changes:**

- Legacy commands are now deprecated (still work but show warnings)
- Recommended migration to new `hedpy` command structure
- Some command-line argument names have changed for consistency

**Python version:**

- Minimum Python version remains 3.10
- Added support for Python 3.14

## Migration guide

### CLI Migration

```bash
# Old (deprecated)
validate_bids /path/to/dataset

# New (recommended)
hedpy validate bids-dataset /path/to/dataset
```

### Script Imports

```python
# Validation functions remain unchanged
from hed import HedString, load_schema_version, BidsDataset

# New utility imports available
from hed.errors import iter_errors
from hed.scripts.script_utils import format_validation_results
```

# Release 0.8.1 December 9, 2025

The primary purpose of this release was to correct the JSON format for HED schemas so that it would accurately distinguish between inherited and non-inherited attributes. The documentation layout was also improved with quick links.

## Highlights

- HED schema JSON export is now cleaner: empty list attributes are omitted instead of written as empty arrays, with stronger tests around inheritance and round-trip behavior.
- Default HED XML schema version bumped to **8.4.0**, so helper functions pick up the latest standard without extra configuration.
- Sphinx docs get a polished Furo theme setup, project logo, sidebar quick links, dark-mode fixes, and a proper GitHub repo icon.
- CI updated to use `actions/checkout@v6` via Dependabot

## What’s Changed

### Schema & JSON I/O

- **Omit empty list attributes in schema JSON** Updated `build_attributes_dict` in `schema2json.py` so list-valued attributes like `suggestedTag`, `relatedTag`, `valueClass`, and `unitClass` are only written when non-empty, instead of always being present as `[]`. This produces a more compact JSON representation and avoids ambiguous “empty list means nothing” cases.

- **Stronger JSON format tests** Refined tests in `test_json_explicit_attributes.py` and `test_schema_format_roundtrip.py` to assert that:

  - Tags without `relatedTag` / `valueClass` / `unitClass` simply do not have those keys in `attributes`.
  - Any list attributes that *are* present must be non-empty.
  - A full 8.4.0 schema is saved as JSON and scanned to ensure no empty list attributes sneak into the output.

- **Schema comparison & round-trip robustness** Extended round-trip tests for JSON schema export/import so that schema comparison is aligned with the new “omit empty lists” behavior and no longer relies on placeholder empty arrays.

- **Default XML schema → 8.4.0** Updated the default XML schema version used by helper utilities to `8.4.0` (from 8.3.0). This ensures `load_schema_version()` and similar functions resolve to the current standard HED schema by default.

### Documentation & Site

- **Furo theme configuration and versioning** Updated `docs/conf.py` to:

  - Set `release = "0.8.0"` for the docs.
  - Use the Furo theme with `html_static_path = ["_static"]`.
  - Register extra assets: `custom.css` and `gh_icon_fix.js`.
  - Attach a project logo via `html_logo`.

- **Sidebar quick links** Added a new `quicklinks.html` sidebar template and wired it into `html_sidebars` so all pages include a “Quick links” section pointing to HED homepage, resources, schema browser, specification, and online tools.

- **Dark-mode & header polish** Extended `custom.css` and the new `gh_icon_fix.js` helper to:

  - Make the sidebar search box readable in dark mode (background, placeholder, and icon colors).
  - Hide the raw “view source” / “edit this page” links in the header.
  - Replace them with a single GitHub icon button that points to the repo root and works in both light and dark themes.

- **Minor formatting clean-ups**\
  Small documentation/test formatting adjustments, including updating tests to load schema version 8.4.0 and aligning text with the new JSON behavior.

### CI / Tooling

- **GitHub Actions: `actions/checkout` v6**\
  Dependabot PR **#1155** updates all workflows to use `actions/checkout@v6` instead of v5, pulling in the latest upstream improvements (including Node.js 24 support and updated credential handling).

# Release 0.8.0 November 18, 2025

- **Unified CLI Interface**: Added `hedpy` command-line tool with git-like subcommand structure.
  - Main command: `hedpy` with subcommands for all HED operations.
  - Subcommands organized by category: `hedpy validate-bids`, `hedpy remodel run`, `hedpy schema validate`, etc.
  - Prevents CLI namespace collisions with other tools (e.g., `validate_bids` → `hedpy validate-bids`).
  - Legacy commands still available for backward compatibility but deprecated.
  - Built with `click` framework for better CLI user experience.
  - Added comprehensive help text: `hedpy --help`, `hedpy COMMAND --help`.
  - **CLI Parameter Fidelity**: All CLI wrapper commands now correctly match original script parameters (38+ parameter fixes across 7 commands).
    - Fixed `validate-bids`: Added missing suffixes, output format, error control, and print options.
    - Fixed `remodel` commands: Corrected argument names, added missing parameters, fixed option conflicts.
    - Fixed `schema` commands: Corrected positional vs option argument structures for add-ids and create-ontology.
    - Added comprehensive test suite (`tests/test_cli_parameter_parity.py`) to verify CLI parameters match original parsers.
- **JSON Schema Format Support**: Added comprehensive JSON format support for HED schemas alongside existing XML, MEDIAWIKI, and TSV formats.
  - Implemented `SchemaLoaderJSON` class for loading JSON schemas (`hed/schema/schema_io/json2schema.py`).
  - Implemented `Schema2JSON` class for exporting schemas to JSON (`hed/schema/schema_io/schema2json.py`).
  - Added JSON constants and key mappings (`hed/schema/schema_io/json_constants.py`).
  - Added `save_as_json()` and `get_as_json_string()` methods to HedSchema class.
  - JSON format uses flat tag structure with hierarchy metadata for easier programmatic access.
  - Separate units section in JSON format for improved AI/tool accessibility.
  - Placeholder structure for takes-value tags with proper attribute inheritance.
  - Full roundtrip validation ensures JSON format produces identical validation results to XML/MEDIAWIKI.
- **New BIDS Sidecar Extraction Tool**: Added `hed_extract_bids_sidecar` command-line script for extracting sidecar templates from BIDS datasets.
  - Configurable value columns and skip columns for flexible template generation.
  - Comprehensive logging support with file output and verbosity control.
  - Integrated with BidsDataset and TabularSummary classes for robust extraction.
- **Schema Validation Enhancements**: Extended schema validation to include JSON format in roundtrip testing.
  - Updated `hed_script_util.py` to validate all 4 schema formats (XML, MEDIAWIKI, TSV, JSON).
  - Updated schema conversion script to automatically generate JSON format alongside other formats.
- **Python Version Requirements**: Minimum Python version raised to 3.10 (dropped 3.9 support).
- **Documentation Improvements**: Added comprehensive Google-style docstrings to all functions in `hed_script_util.py`.
- **Configuration Updates**:
  - Added `status` directory to Black exclude list in `pyproject.toml` for development scripts.
  - Updated matplotlib dependency to 3.10.7.
- **Specification Tests**: Updated hed-specification submodule to latest version for improved test coverage.

# Release 0.7.1 October 13, 2025

- Added official support for Python 3.13 (tested in CI workflows).
- Applied Black code formatter to entire codebase for consistent code style (148 files reformatted).
- Added Black to development dependencies (`pip install -e .[dev]`) and GitHub Actions CI workflow.
- Created `.github/workflows/black.yaml` for automated code formatting checks on all PRs and pushes.
- Migrated from flake8 to ruff for linting and code quality checks (faster, more comprehensive).
- Applied code corrections throughout codebase as suggested by ruff linter.
- Removed `.flake8` configuration file in favor of ruff configuration in pyproject.toml.
- Removed unneeded parameters from validator functions for cleaner API.
- Added TYPE_CHECKING imports to avoid circular import issues in type annotations.
- Changed sentinel value name from `_UNSET` to `_SENTINEL` in bids_dataset.py for clarity.
- Enhanced coverage workflow configuration for improved CI/CD reliability.
  - Changed ci_cov.yaml to only run on main branch (not all branches).
  - Updated Python version from 3.12 to 3.10 for coverage tests.
  - Configured qlty.toml for proper coverage reporting with relative paths.
  - Updated .coveragerc to remove explicit source specification.
- Added `pip install -e .[test]` to all GitHub Actions workflows (ci.yaml, ci_windows.yaml, spec_tests.yaml).
- Enhanced CONTRIBUTING.md with Black and ruff usage guidelines and code quality tools section.
- Updated README.md with "Code Formatting with Black" section including Windows-specific workarounds.
- Updated RELEASE_GUIDE.md to include code quality checks (Black, ruff, codespell) as pre-release step.
- Configured Black in pyproject.toml with 127 character line length matching existing ruff configuration.

# Release 0.7.0 October 2, 2025

- Added comprehensive logging infrastructure with configurable log levels and file output to validation tools.
- Enhanced validate_bids script with improved error reporting and filtering capabilities.
- Added error code counting and filtering by count/file in ErrorHandler.
- Improved validation output formatting with version tracking in JSON output.
- Added comprehensive CONTRIBUTING.md with development guidelines and best practices.
- Enhanced README.md with better documentation structure and examples.
- Improved user guide documentation with clearer installation and usage instructions.
- Fixed typos and improved code documentation throughout the codebase.
- Enhanced Windows compatibility with normalized path handling in tests.
- Updated pyproject.toml with improved metadata and dependencies.

# Release 0.6.0 August 7, 2024

- Added MATLAB integration support with improved function visibility in __init__.py.
- Enhanced ontology creation and validation with better handling of equivalent classes.
- Improved schema scripts with migration from hed-schemas repository.
- Added DataFrame loading/saving optimizations and folder-based operations.
- Enhanced HED ID validation with more robust checks.
- Improved sidecar and tabular input utilities with new helper functions.
- Added support for empty tabular files and whitespace-only files.
- Enhanced annotation utilities for better MATLAB compatibility.
- Improved matplotlib compatibility and updated color map access.
- Fixed various bugs in spreadsheet handling and schema loading.
- Updated dependencies and improved Python 3.7+ compatibility.
- Improved code quality with better type handling and error messages.

# Release 0.5.0

- Added JSON schema specification of remodeling commands.
- Added support for schema that are specified by .tsv files.
- Added support for embedding schema in an ontology.
- Added WordCloud visualizations.
- Added handling of event context and events of temporal extent.

# Release 0.4.0 October 27, 2023

- Refactored the model classes to be based on DataFrame.
- Added additional command line options for remodeling tools.
- Restructured summaries for better reporting.
- Minor refactoring to reduce code complexity.
- Finalized and automated SPEC tests.
- Improvements to GitHub automation -- including adding CodeSpell.
- Improvements to API-Docs.

# Release 0.3.1 July 3, 2023

- Pinned the version of the pydantic and inflect libraries due to conflict.
- Reorganized JSON output of remodeling summaries so that all of consistent form.
- Fixed summarize_hed_tags_op so that tags were correctly categorized for output.
- Minor refactoring to reduce code complexity.
- BaseInput and Sidecar now raise HedFileError if input could not be read.

# Release 0.3.0 June 20, 2023

- Introduction of partnered schema.
- Improved error handling for schema validation.
- Support of Inset tags.
- Support of curly brace notation in sidecars.
- Expanded remodeling functionality.
- Refactoring of models to rely on DataFrames.
- Expanded unit tests in conjunction with specification tests.

# Release 0.2.0 February 14, 2023

- First release of the HED remodeling tools.
- Reorganization of branches to reflect stages of development.
- Updating of schema cache with local copies.
- Improved schema validation and error messages.
- First pass at search and summarization.

# Release 0.1.0 June 20, 2022

- First release on PyPI\`\`\`

```
```
