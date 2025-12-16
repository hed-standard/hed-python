# HED-Python Release Guide

This document provides step-by-step instructions for releasing a new version of hedtools to PyPI.

**Platform Support:** This guide includes commands for both Windows (PowerShell) and Linux/macOS (Bash).

## Prerequisites

Before starting the release process, ensure you have:

- [ ] Write access to the hed-python repository
- [ ] PyPI account with maintainer access to the `hedtools` package
- [ ] Git configured with your credentials
- [ ] Python 3.10+ installed
- [ ] Virtual environment activated (if using one)
- [ ] All intended changes merged to the `main` branch

## Release Checklist

### 1. Pre-Release Preparation

#### 1.1 Ensure Working Tree is Clean

**Windows (PowerShell):**

```powershell
# Check git status
git status

# If there are uncommitted changes, commit or stash them
git add .
git commit -m "Pre-release cleanup"
```

**Linux/macOS (Bash):**

```bash
# Check git status
git status

# If there are uncommitted changes, commit or stash them
git add .
git commit -m "Pre-release cleanup"
```

#### 1.2 Update CHANGELOG.md

Add a new entry at the top of `CHANGELOG.md` with:

- Release version number (e.g., "Release 0.7.1")
- Release date
- Bullet points describing:
  - New features
  - Enhancements
  - Bug fixes
  - Documentation improvements
  - Breaking changes (if any)

**Example:**

```markdown
Release 0.7.1 October 13, 2025
- Applied Black code formatter to entire codebase for consistent code style
- Added Black to development dependencies and CI workflow
- Enhanced CONTRIBUTING.md with code formatting guidelines
- Updated README.md with Black usage instructions
```

#### 1.3 Run Code Quality Checks

Before releasing, ensure all code quality checks pass:

**All Platforms:**

```bash
# Run code formatter check
black --check .
# On Windows, use: black --workers 1 --check .

# Run linter
ruff check hed/ tests/

# Run spell checker
codespell

# Run all tests
python -m unittest discover tests -v
```

Fix any issues before proceeding.

#### 1.4 Commit CHANGELOG Updates

**All Platforms:**

```bash
git add CHANGELOG.md
git commit -m "Update CHANGELOG for version 0.7.1"
```

#### 1.5 Merge to Main Branch

If you're working on a feature branch:

**All Platforms:**

```bash
# Update your local main branch
git checkout main
git pull origin main

# Merge your feature branch
git merge your-feature-branch

# Resolve any conflicts if they arise
# Then push to origin
git push origin main
```

### 2. Version Tagging

The project uses [versioneer](https://github.com/python-versioneer/python-versioneer) for version management, which automatically derives the version from git tags.

#### 2.1 Create Annotated Tag

**All Platforms:**

```bash
# Create an annotated tag with the version number
git tag -a 0.7.0 -m "Release version 0.7.0"
```

**Important:**

- Use semantic versioning: MAJOR.MINOR.PATCH
- Do NOT use a prefix (e.g., use `0.7.0`, not `v0.7.0`)
- The tag name must match the version you want to release

#### 2.2 Push the Tag

**All Platforms:**

```bash
# Push the tag to the remote repository
git push origin 0.7.0
```

#### 2.3 Verify Version

**All Platforms:**

```bash
# Check that the version is correctly detected
python -c "import hed; print(hed.__version__)"
```

Expected output: `0.7.0`

If you see something like `0+untagged.xxx.gxxxxxxx`, the tag wasn't properly created or you need to pull the tags:

**All Platforms:**

```bash
git fetch --tags
```

### 3. Build Distribution Packages

#### 3.1 Clean Previous Builds

**Windows (PowerShell):**

```powershell
# Remove old build artifacts
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

**Linux/macOS (Bash):**

```bash
# Remove old build artifacts
rm -rf dist build *.egg-info
```

#### 3.2 Install/Upgrade Build Tools

**All Platforms:**

```bash
python -m pip install --upgrade build twine
```

#### 3.3 Build the Packages

**All Platforms:**

```bash
# Build both wheel and source distributions
python -m build
```

This creates:

- `dist/hedtools-0.7.0-py3-none-any.whl` (wheel distribution)
- `dist/hedtools-0.7.0.tar.gz` (source distribution)

#### 3.4 Verify Build Contents

**Windows (PowerShell):**

```powershell
# List contents of the wheel
python -m zipfile -l dist/hedtools-0.7.0-py3-none-any.whl

# Check the source distribution (requires tar in PATH)
tar -tzf dist/hedtools-0.7.0.tar.gz
```

**Linux/macOS (Bash):**

```bash
# List contents of the wheel
unzip -l dist/hedtools-0.7.0-py3-none-any.whl

# Check the source distribution
tar -tzf dist/hedtools-0.7.0.tar.gz
```

### 4. Test the Distribution (Recommended)

#### 4.1 Create Test Environment

**Windows (PowerShell):**

```powershell
# Create a fresh virtual environment for testing
python -m venv test_env
.\test_env\Scripts\Activate.ps1
```

**Linux/macOS (Bash):**

```bash
# Create a fresh virtual environment for testing
python -m venv test_env
source test_env/bin/activate
```

#### 4.2 Install from Wheel

**All Platforms:**

```bash
# Install the built wheel
pip install dist/hedtools-0.7.0-py3-none-any.whl
```

#### 4.3 Run Tests

**Windows (PowerShell):**

```powershell
# Navigate back to the repository
cd h:\Repos\hed-python

# Run the test suite
python -m unittest discover tests -v
```

**Linux/macOS (Bash):**

```bash
# Navigate back to the repository
cd ~/path/to/hed-python

# Run the test suite
python -m unittest discover tests -v
```

#### 4.4 Verify Installation

**All Platforms:**

```bash
# Check version
python -c "import hed; print(hed.__version__)"

# Test a basic import
python -c "from hed import load_schema_version; schema = load_schema_version('8.3.0'); print('Success!')"
```

#### 4.5 Clean Up Test Environment

**Windows (PowerShell):**

```powershell
deactivate
Remove-Item -Recurse -Force test_env
```

**Linux/macOS (Bash):**

```bash
deactivate
rm -rf test_env
```

### 5. Upload to PyPI

#### 5.1 Check Distribution with Twine

**All Platforms:**

```bash
# Validate the distribution packages
python -m twine check dist/*
```

Expected output: `Checking dist/hedtools-0.7.0.tar.gz: PASSED` (and same for .whl)

#### 5.2 Upload to Test PyPI (Optional but Recommended)

**All Platforms:**

```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for your TestPyPI credentials.

**Test installation from TestPyPI:**

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ hedtools==0.7.0
```

#### 5.3 Upload to Production PyPI

**All Platforms:**

```bash
# Upload to the real PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials (or use an API token).

**Alternative with API Token:**

*Windows (PowerShell):*

```powershell
# Set your PyPI API token as an environment variable
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-your-api-token-here"

# Upload
python -m twine upload dist/*
```

*Linux/macOS (Bash):*

```bash
# Set your PyPI API token as an environment variable
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-your-api-token-here"

# Upload
python -m twine upload dist/*
```

#### 5.4 Verify on PyPI

Visit https://pypi.org/project/hedtools/ and verify:

- [ ] Version 0.7.0 is listed
- [ ] README renders correctly
- [ ] All metadata is correct
- [ ] Download links work

### 6. Create GitHub Release

#### 6.1 Navigate to Releases

Go to: https://github.com/hed-standard/hed-python/releases/new

#### 6.2 Create Release

Fill in the release form:

- **Choose a tag:** Select `0.7.0` from the dropdown
- **Release title:** `Release 0.7.0`
- **Description:** Copy the relevant section from CHANGELOG.md

**Example description:**

```markdown
## What's New in 0.7.0

### Features
- Added comprehensive logging infrastructure with configurable log levels and file output
- Enhanced validate_bids script with improved error reporting and filtering capabilities
- Added error code counting and filtering by count/file in ErrorHandler

### Documentation
- Added comprehensive CONTRIBUTING.md with development guidelines
- Significantly enhanced README.md with better documentation structure
- Improved user guide documentation

### Bug Fixes
- Fixed Windows path handling in tests
- Fixed typos and improved code documentation

### Full Changelog
See [CHANGELOG.md](https://github.com/hed-standard/hed-python/blob/main/CHANGELOG.md)
```

#### 6.3 Attach Build Artifacts

- Upload `dist/hedtools-0.7.0-py3-none-any.whl`
- Upload `dist/hedtools-0.7.0.tar.gz`

#### 6.4 Publish Release

Click **Publish release**

### 7. Post-Release Verification

#### 7.1 Test Installation from PyPI

In a fresh environment:

**All Platforms:**

```bash
pip install --upgrade hedtools
python -c "import hed; print(hed.__version__)"
```

Expected output: `0.7.0`

#### 7.2 Verify Documentation

Check that documentation sites are updated (may take some time):

- https://www.hedtags.org/hed-python/

#### 7.3 Announce the Release

Consider announcing the release:

- [ ] GitHub Discussions
- [ ] HED mailing list
- [ ] Community forums
- [ ] Social media (if applicable)

### 8. Troubleshooting

#### Issue: Wrong version number after tagging

**Problem:** `python -c "import hed; print(hed.__version__)"` shows wrong version

**Solution:**

```bash
# Fetch all tags
git fetch --tags

# Verify tag exists
git tag -l

# Check versioneer can find it
python -c "import hed._version; print(hed._version.get_versions())"
```

#### Issue: Build fails with "No module named X"

**Problem:** Missing dependencies during build

**Solution:**

```bash
# Ensure build tools are installed
pip install --upgrade pip setuptools wheel build

# Try building again
python -m build
```

#### Issue: Upload to PyPI fails with authentication error

**Problem:** Invalid credentials or API token

**Solution:**

- Create a new API token at https://pypi.org/manage/account/token/
- Scope it to the `hedtools` project only
- Use `__token__` as username and the token as password

#### Issue: Tag already exists

**Problem:** You need to delete and recreate a tag

**Solution:**

```bash
# Delete local tag
git tag -d 0.7.0

# Delete remote tag (CAUTION: only if not yet released!)
git push origin :refs/tags/0.7.0

# Recreate the tag
git tag -a 0.7.0 -m "Release version 0.7.0"
git push origin 0.7.0
```

**WARNING:** Only delete remote tags if the release hasn't been published yet!

## Version Numbering Guidelines

HED-Python follows [Semantic Versioning](https://semver.org/):

- **MAJOR version (X.0.0):** Incompatible API changes
- **MINOR version (0.X.0):** New features, backward-compatible
- **PATCH version (0.0.X):** Bug fixes, backward-compatible

### When to increment:

- **MAJOR:** Breaking changes, API redesign, major architectural changes
- **MINOR:** New features, new functions/classes, enhancements (this release: 0.7.0)
- **PATCH:** Bug fixes, documentation fixes, small improvements (0.7.1)

## Quick Reference Commands

**Windows (PowerShell):**

```powershell
# Complete release workflow
git status                                    # Check working tree
git add CHANGELOG.md                          # Stage changelog
git commit -m "Update CHANGELOG for v0.7.0"   # Commit
git push origin main                          # Push to main
git tag -a 0.7.0 -m "Release version 0.7.0"   # Create tag
git push origin 0.7.0                         # Push tag
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build                               # Build
python -m twine check dist/*                  # Verify
python -m twine upload dist/*                 # Upload
```

**Linux/macOS (Bash):**

```bash
# Complete release workflow
git status                                    # Check working tree
git add CHANGELOG.md                          # Stage changelog
git commit -m "Update CHANGELOG for 0.7.0"    # Commit
git push origin main                          # Push to main
git tag -a 0.7.0 -m "Release version 0.7.0"   # Create tag
git push origin 0.7.0                         # Push tag
rm -rf dist build *.egg-info                  # Clean old builds
python -m build                               # Build
python -m twine check dist/*                  # Verify
python -m twine upload dist/*                 # Upload
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Versioneer Documentation](https://github.com/python-versioneer/python-versioneer)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [HED Documentation](https://www.hedtags.org/)

## Contacts

For questions about the release process:

- **Maintainer:** Kay Robbins (Kay.Robbins@utsa.edu)
- **Repository:** https://github.com/hed-standard/hed-python
- **Issues:** https://github.com/hed-standard/hed-python/issues
