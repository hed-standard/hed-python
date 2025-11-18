# Spec Tests Setup Guide

## Overview

The `spec_tests` directory contains integration tests that validate the HED Python library against the official HED specification and example datasets. These tests are run separately from the main unit tests.

## Directory Structure Required

To run spec_tests locally, you need to have the following directory structure:

```
spec_tests/
├── hed-specification/
│   └── tests/
│       └── json_tests/          # JSON test files for error validation
├── hed-examples/
│   └── datasets/                # BIDS datasets for validation testing  
├── test_sidecar.json           # Already present
├── test_errors.py              # Tests HED validation against spec
├── test_hed_cache.py           # Tests HED schema caching
└── validate_bids.py            # Tests BIDS dataset validation
```

## Setup Instructions

1. **Copy Submodule Content**: 
   - Copy the content of the `hed-specification` repository to `spec_tests/hed-specification/`
   - Copy the content of the `hed-examples` repository to `spec_tests/hed-examples/`

2. **Verify Setup**: 
   - Run `python spec_tests/check_setup.py` to verify all required directories exist

## Running Spec Tests

### From Command Line:
```powershell
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

## Notes

- The `test_hed_cache.py` tests should work immediately as they don't require the submodule content
- The `test_errors.py` and `validate_bids.py` tests require the submodule content to be present
- On GitHub Actions, the submodules are automatically checked out, but locally you need to copy the content manually

## Troubleshooting

If spec tests aren't showing up in VS Code:
1. Make sure VS Code Python extension is installed
2. Ensure the workspace Python interpreter is set to `.venv/Scripts/python.exe`
3. Try refreshing the test discovery: Command Palette → "Test: Refresh Tests"
4. Check that the required directory structure exists using the check script