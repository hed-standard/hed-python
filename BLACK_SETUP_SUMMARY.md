# Black Code Formatter Setup - Summary

## What Has Been Done

### 1. Added Black to Project Dependencies
**File: `pyproject.toml`**
- Added `black>=24.0.0` to `[project.optional-dependencies] dev`
- Added `[tool.black]` configuration section with:
  - Line length: 127 (matching ruff)
  - Target Python versions: 3.9-3.13
  - Exclusions for auto-generated files and external repos

### 2. Created GitHub Actions Workflow
**File: `.github/workflows/black.yaml`**
- Runs on every push and pull request
- Uses Python 3.12 for consistency
- Runs `black --check --diff .` to verify formatting
- Will fail CI if code is not formatted

### 3. Updated Documentation
**File: `CONTRIBUTING.md`**
- Added Black to "Code Quality Tools" section
- Added installation instructions: `pip install -e .[dev]`
- Provided usage examples for local development

### 4. Local Installation
Black has been installed in your `.venv`:
- Location: `H:/Repos/hed-python/.venv/Scripts/black.exe`
- Version: 25.9.0

## Quick Usage Guide

### Using Black with PowerShell

Since you're on Windows with PowerShell, here are the commands:

```powershell
# Run from your .venv (recommended - already activated)
black --workers 1 --check .           # Check what would change
black --workers 1 --check --diff .    # Show what would change
black --workers 1 .                   # Format all code

# Or use the full path if needed
.\.venv\Scripts\black.exe --workers 1 --check .
```

**Note:** The `--workers 1` flag is required on Windows to avoid "I/O operation on closed file" errors with Black 25.9.0.

### Next Steps

1. **Review the changes** Black would make:
   ```powershell
   black --workers 1 --check --diff hed/ tests/
   ```

2. **Format the codebase** (if you agree with the changes):
   ```powershell
   black --workers 1 .
   ```

3. **Commit the formatted code**:
   ```powershell
   git add .
   git commit -m "Apply Black code formatting"
   ```

4. **Future development**: Always run `black --workers 1 .` before committing

### CI Integration

The GitHub Actions workflow will:
- ✅ Pass if all code is Black-formatted
- ❌ Fail if code needs formatting (showing diff)
- Run automatically on all branches and PRs

### Notes

- Black is deterministic (same input = same output always)
- Compatible with ruff (our existing linter)
- Uses 127 character line length (project standard)
- Automatically skips `_version.py` and other generated files

## Files Modified

1. `pyproject.toml` - Added Black config and dependency
2. `.github/workflows/black.yaml` - New CI workflow
3. `CONTRIBUTING.md` - Updated developer docs
4. `.black-howto.md` - Quick reference guide (this can be deleted if not needed)
