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
└── test_loading_schemas.py     # Tests that all schemas can be loaded
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

## Schema Loading Tests

The `test_loading_schemas.py` file tests that all schemas in the `hed-schemas` submodule load successfully. It runs automatically as part of `python -m unittest discover spec_tests`.

The core logic lives in `hed.scripts.check_schema_loading`, which can also be run standalone via the `hed_check_schema_loading` console script (installed with hedtools):

```bash
# Run from hed-schemas repo root (e.g. in a GitHub Action)
hed_check_schema_loading --schemas-dir .

# Or point at a local checkout
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas

# Filter by format, library, or release status
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas --format xml
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas --library lang
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas --exclude-prereleases
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas --prerelease-only
hed_check_schema_loading --schemas-dir spec_tests/hed-schemas --verbose
```

### CLI Options

- `--schemas-dir PATH` (required): Path to the hed-schemas repository root
- `--format {xml,mediawiki,json,tsv,all}`: Test specific format only (default: all)
- `--library NAME`: Test specific library only (default: all)
- `--standard-only`: Test only standard schemas (no libraries)
- `--exclude-prereleases`: Exclude prerelease schemas (releases only)
- `--prerelease-only`: Test only prerelease schemas
- `--verbose`: Show detailed success messages for each schema

### Exit Codes

- **0**: All schemas loaded successfully
- **1**: One or more schemas failed to load
- **2**: Invalid command-line arguments
- **130**: User interrupted (Ctrl+C)

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
