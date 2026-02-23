# Spec Tests Setup Guide

## Overview

The `spec_tests` directory contains integration tests that validate the HED Python library against the official HED specification and example datasets. These tests are run separately from the main unit tests.

## Directory Structure Required

To run spec_tests locally, you need to have the following directory structure:

```
spec_tests/
├── hed-tests/
│   └── json_test_data/          # JSON test files from hed-tests repository
├── hed-examples/
│   └── datasets/                # BIDS datasets for validation testing
├── hed-schemas/
│   ├── standard_schema/         # Standard HED schemas in all formats
│   └── library_schemas/         # HED library schemas
├── test_sidecar.json           # Already present
├── test_errors.py              # Tests HED validation against spec
├── test_hed_cache.py           # Tests HED schema caching
├── test_bids_datasets.py       # Tests BIDS dataset validation
└── try_loading_all_schemas.py  # Manual script to test schema loading
```

## Setup Instructions

### Option 1: Using Git Submodules (Recommended)

1. **Initialize Submodules**:

   ```bash
   git submodule update --init --recursive
   ```

   This will automatically clone the `hed-tests`, `hed-examples`, and `hed-schemas` repositories into the correct locations.

2. **Update Submodules** (when needed):

   ```bash
   git submodule update --remote
   ```

### Option 2: Manual Setup (Alternative)

1. **Clone Required Repositories**:

   - Clone the `hed-tests` repository to `spec_tests/hed-tests/`
   - Clone the `hed-examples` repository to `spec_tests/hed-examples/`
   - Clone the `hed-schemas` repository to `spec_tests/hed-schemas/`

2. **Verify Setup**:

   - Run `python spec_tests/check_setup.py` to verify all required directories exist

## Running Spec Tests

### From Command Line:

```bash
# Run all spec tests
python -m unittest discover spec_tests -v

# Run specific spec test file
python -m unittest spec_tests.test_hed_cache -v
```

### From VS Code:

1. **Right-click Method**:

   - Right-click on the `spec_tests` folder in VS Code Explorer
   - Select "Run Tests" from the context menu

2. **Using Tasks**:

   - Open Command Palette (Ctrl+Shift+P)
   - Type "Tasks: Run Task"
   - Select "Run Spec Tests"

3. **Test Explorer**:

   - Open the Test Explorer panel
   - Tests should be discovered in both `tests/` and `spec_tests/` directories

## Schema Loading Test Script

The `try_loading_all_schemas.py` script provides comprehensive testing of schema loading capabilities across all formats and versions from the `hed-schemas` submodule.

### Usage

```bash
# Test all schemas (releases and prereleases, all formats)
python spec_tests/try_loading_all_schemas.py

# Test only release schemas (exclude prereleases)
python spec_tests/try_loading_all_schemas.py --exclude-prereleases

# Test only prerelease schemas
python spec_tests/try_loading_all_schemas.py --prerelease-only

# Test standard schemas only (no libraries)
python spec_tests/try_loading_all_schemas.py --standard-only

# Test a specific library
python spec_tests/try_loading_all_schemas.py --library lang

# Test a specific format
python spec_tests/try_loading_all_schemas.py --format xml

# Combine filters
python spec_tests/try_loading_all_schemas.py --library lang --format xml --exclude-prereleases

# Show detailed success messages
python spec_tests/try_loading_all_schemas.py --verbose
```

### Command-Line Options

- `--format {xml,mediawiki,json,tsv,all}`: Test specific format only (default: all)
- `--library NAME`: Test specific library only (default: all)
- `--standard-only`: Test only standard schemas (no libraries)
- `--exclude-prereleases`: Exclude prerelease schemas (releases only)
- `--prerelease-only`: Test only prerelease schemas
- `--verbose`: Show detailed success messages for each schema

### Output

The script displays schemas organized by type (standard/library) and release status (release/prerelease):

```
STANDARD SCHEMAS
XML (6): HED8.0.0.xml, HED8.1.0.xml, HED8.2.0.xml, ...

LIBRARY SCHEMAS
LANG:
  XML (3): HED_lang_1.0.0.xml, HED_lang_1.1.0.xml, ...

STANDARD PRERELEASE SCHEMAS
XML (1): HED8.5.0.xml

LIBRARY PRERELEASE SCHEMAS
LANG:
  XML (1): HED_lang_1.2.0.xml
```

### Exit Codes

- **0**: All schemas loaded successfully
- **1**: One or more schemas failed to load (causes CI failure)
- **130**: User interrupted (Ctrl+C)

This makes the script suitable for use in GitHub Actions workflows to automatically detect schema loading issues.

## Notes

- The `test_hed_cache.py` tests should work immediately as they don't require the submodule content
- The `test_errors.py` and `test_bids_datasets.py` tests require the submodule content to be present
- On GitHub Actions, the submodules are automatically checked out via the workflow configuration
- Locally, initialize submodules using `git submodule update --init --recursive`
- All three submodule directories (`hed-tests`, `hed-examples`, `hed-schemas`) are gitignored to prevent committing submodule content directly
- Use `git submodule update --remote` to pull the latest changes from the submodule repositories

## Troubleshooting

If spec tests aren't showing up in VS Code:

1. Make sure VS Code Python extension is installed
2. Ensure the workspace Python interpreter is set to `.venv/Scripts/python.exe`
3. Try refreshing the test discovery: Command Palette → "Test: Refresh Tests"
4. Check that the required directory structure exists using the check script
