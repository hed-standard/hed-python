# Testing Standards

## Framework

- **unittest** is the project standard for writing and running tests
- Test files mirror `hed/` package structure under `tests/`
- Test file naming: `test_<module>.py`
- Uses unittest's `setUp`/`setUpClass` (no pytest fixtures or conftest.py)

## Test Organization (60 test files)

```
tests/
  data/                        - Test data files (schemas, sidecars, TSVs)
  errors/                      - Error handling tests
  models/                      - HedString, HedTag, definitions, queries, sidecar, tabular
  schema/                      - Schema loading, caching, IO, validation, comparison
  scripts/                     - Script integration tests
  tools/                       - Analysis and BIDS tools
  validator/                   - Core validator tests
  bids_tests/                  - BIDS dataset validation
  model_tests/                 - Additional model tests
  other_tests/                 - Miscellaneous tests
  sidecar_tests/               - BIDS sidecar tests
  spreadsheet_validator_tests/ - Spreadsheet validation
  validator_tests/             - Extended validator tests
  test_cli_parameter_parity.py - CLI parameter consistency
  test_notebooks.py            - Jupyter notebook structure/imports
```

## No Mocks Policy

- All tests use real data: real schemas, real HED strings, real files
- Spec tests use official HED test data via git submodules:
  - `spec_tests/hed-tests/` - Official specification test cases
  - `spec_tests/hed-examples/` - Example BIDS datasets
  - `spec_tests/hed-schemas/` - Official schema repository
- Initialize: `git submodule update --init --recursive`

## Running Tests

```bash
# All unit tests
python -m unittest discover tests -v

# Spec tests (require submodule init)
python -m unittest discover spec_tests -v

# Specific test file
python -m unittest tests/models/test_hed_string.py

# Specific test case
python -m unittest tests.models.test_hed_string.TestHedString.test_constructor

# Notebook tests
python -m unittest tests.test_notebooks
```

## Test Patterns

- Use `setUpClass` to load schemas (expensive; shared across test methods)
- Each test should be independent and isolated
- Test both success and failure/error cases
- Include edge cases and validation error scenarios
- Spec tests use `continue-on-error` in CI but fail the workflow if any test fails

## Coverage

- Branch coverage enabled (`.coveragerc`)
- Omits: `__init__.py`, `_version.py`, venv, test directories
- CI uploads coverage to Qlty via `ci_cov.yaml`
