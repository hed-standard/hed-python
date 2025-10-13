Release 0.7.1 October 13, 2025
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

Release 0.7.0 October 2, 2025
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

Release 0.6.0 August 7, 2024
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

Release 0.5.0
- Added JSON schema specification of remodeling commands.
- Added support for schema that are specified by .tsv files.
- Added support for embedding schema in an ontology.
- Added WordCloud visualizations.
- Added handling of event context and events of temporal extent.

Release 0.4.0 October 27, 2023
- Refactored the model classes to be based on DataFrame.
- Added additional command line options for remodeling tools.
- Restructured summaries for better reporting.
- Minor refactoring to reduce code complexity.
- Finalized and automated SPEC tests.
- Improvements to GitHub automation -- including adding CodeSpell.
- Improvements to API-Docs.

Release 0.3.1 July 3, 2023
- Pinned the version of the pydantic and inflect libraries due to conflict.
- Reorganized JSON output of remodeling summaries so that all of consistent form.
- Fixed summarize_hed_tags_op so that tags were correctly categorized for output.
- Minor refactoring to reduce code complexity.
- BaseInput and Sidecar now raise HedFileError if input could not be read.

Release 0.3.0 June 20, 2023
- Introduction of partnered schema.
- Improved error handling for schema validation.
- Support of Inset tags.
- Support of curly brace notation in sidecars.
- Expanded remodeling functionality.
- Refactoring of models to rely on DataFrames.
- Expanded unit tests in conjunction with specification tests.

Release 0.2.0 February 14, 2023
- First release of the HED remodeling tools.
- Reorganization of branches to reflect stages of development.
- Updating of schema cache with local copies.
- Improved schema validation and error messages.
- First pass at search and summarization.

Release 0.1.0  June 20, 2022
- First release on PyPI