# Contributing to HEDTools

Thank you for your interest in contributing to HEDTools! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### Types of Contributions

- **Bug Reports:** Help us identify and fix issues
- **Feature Requests:** Suggest new functionality
- **Code Contributions:** Submit bug fixes or new features
- **Documentation:** Improve guides, examples, or API docs
- **Testing:** Add test coverage or report test failures
- **Examples:** Share use cases and example code

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip (Python package manager)

### Setting Up Your Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hed-python.git
   cd hed-python
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e .
   pip install -r requirements.txt
   pip install -r docs/requirements.txt
   pip install -e .[dev]  # Install development tools (black, ruff, codespell)
   ```

4. **Run tests to verify setup:**
   ```bash
   python -m unittest discover tests
   ```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Maximum line length: 120 characters
- Use descriptive variable and function names
- Add docstrings to all public classes and functions

### Code Quality Tools

We use several tools to maintain code quality:

- **black:** For automatic code formatting
  ```bash
  # Check if code is formatted correctly
  black --check .
  
  # Automatically format all code
  black .
  
  # Format specific files or directories
  black hed/ tests/
  
  # Windows: Use --workers 1 if you encounter file I/O errors
  black --workers 1 .
  ```

- **ruff:** For linting, style checking, and import sorting
  ```bash
  ruff check hed/ tests/
  ```
  
  To automatically fix issues:
  ```bash
  ruff check --fix hed/ tests/
  ```

- **codespell:** For spell checking
  ```bash
  codespell
  ```

### Documentation Style

- Use Google-style docstrings for all public APIs
- Include type hints where appropriate
- Provide examples for complex functionality

Example docstring:
```python
def validate_hed_string(hed_string, schema)->list[dict]:
    """Validate a HED string against a schema.
    
    Parameters:
        hed_string (str): The HED string to validate.
        schema (HedSchema): The schema to validate against.
        
    Returns:
        list: A list of validation issues, empty if valid.
        
    Example:
        >>> schema = load_schema_version('8.4.0')
        >>> issues = validate_hed_string("Event", schema)
        >>> if not issues:
        ...     print("Valid!")
    """
    pass
```

## Testing Guidelines

### Test Structure

- Place tests in the `tests/` directory, mirroring the `hed/` structure
- Name test files with `test_` prefix
- Use descriptive test method names

### Writing Tests

- Each test should be independent and isolated
- Use unittest framework (the project standard)
- Test both success and failure cases
- Include edge cases

Example test:
```python
import unittest
from hed import HedString, load_schema

class TestHedValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version('8.4.0')
    
    def test_valid_hed_string(self):
        hed_string = HedString("Event", self.schema)
        issues = hed_string.validate()
        self.assertEqual(len(issues), 0)
    
    def test_invalid_hed_string(self):
        hed_string = HedString("InvalidTag", self.schema)
        issues = hed_string.validate()
        self.assertGreater(len(issues), 0)

if __name__ == '__main__':
    unittest.main()
```

### Running Tests

Run all tests:
```bash
python -m unittest discover tests
```

Run specific test file:
```bash
python -m unittest tests/models/test_hed_string.py
```

Run specific test case:
```bash
python -m unittest tests.models.test_hed_string.TestHedString.test_constructor
```

## Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all tests:**
   ```bash
   python -m unittest discover tests
   ```

3. **Check code style:**
   ```bash
   ruff check hed/ tests/
   ```

4. **Update documentation** if you've added/changed functionality

### Submitting a Pull Request

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, focused commits

3. **Write descriptive commit messages:**
   ```
   Add validation for temporal extent
   
   - Implement temporal extent validation logic
   - Add unit tests for temporal validation
   - Update documentation with temporal examples
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub:
   - Target the `main` branch
   - Fill out the PR template completely
   - Link related issues
   - Add meaningful description of changes

### PR Review Process

- A maintainer will review your PR within a few days
- Address any requested changes
- Once approved, a maintainer will merge your PR

## Reporting Bugs

### Before Submitting a Bug Report

- Check the [existing issues](https://github.com/hed-standard/hed-python/issues)
- Update to the latest version
- Verify the bug is reproducible

### How to Submit a Bug Report

Create an issue with:

1. **Clear title** describing the problem
2. **Environment details:** OS, Python version, hedtools version
3. **Steps to reproduce** the issue
4. **Expected behavior**
5. **Actual behavior**
6. **Code sample** demonstrating the problem (if applicable)
7. **Error messages** or stack traces

Example:
```markdown
## Bug: Schema validation fails with custom schema

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.5
- hedtools: 0.5.0

**Steps to Reproduce:**
1. Load custom schema from file
2. Validate HED string with tag "Event"
3. Observe error

**Expected:** Validation succeeds
**Actual:** Raises KeyError

**Code:**
\```python
from hed import load_schema, HedString
schema = load_schema('/path/to/schema.xml')
hed = HedString("Event")
issues = hed.validate(schema)  # KeyError here
\```

**Error:**
\```
KeyError: 'Event'
  at line 123 in validator.py
\```
```

## Suggesting Enhancements

### How to Suggest an Enhancement

Create an issue with:

1. **Clear title** describing the enhancement
2. **Use case:** Why is this enhancement needed?
3. **Proposed solution:** How should it work?
4. **Alternatives considered:** Other approaches you've thought about
5. **Additional context:** Screenshots, mockups, or examples

## Questions?

- **Documentation:** [https://www.hedtags.org/hed-python](https://www.hedtags.org/hed-python)
- **Issues:** [GitHub Issues](https://github.com/hed-standard/hed-python/issues)
- **Email:** Kay.Robbins@utsa.edu

Thank you for contributing to HEDTools! 🎉
