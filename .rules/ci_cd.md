# CI/CD Configuration

## GitHub Actions Workflows (.github/workflows/)

### Core Testing
| Workflow | Triggers | Python | Description |
|----------|----------|--------|-------------|
| `ci.yaml` | Push + PR (all branches) | 3.10-3.14 (main/PR to main); 3.10, 3.13 (others) | Matrix-based unit + spec tests; continue-on-error for spec_tests |
| `ci_cov.yaml` | Push to main | 3.10 | Coverage reporting; uploads to Qlty |
| `ci_windows.yaml` | Push + PR to main | 3.10-3.12 | Windows-specific tests; skips submodules |
| `spec_tests.yaml` | Push + PR (all branches) | 3.10 | test_errors, test_bids_datasets, test_hed_cache; fails if any spec test fails |
| `test_installer.yaml` | Push + PR to main | 3.10, 3.13 | Fresh venv pip install; imports HedString to verify |

### Code Quality
| Workflow | Triggers | Python | Description |
|----------|----------|--------|-------------|
| `ruff.yaml` | Push + PR to main | 3.12 | Ruff linter (>=0.8.0) |
| `black.yaml` | Push + PR (all branches) | 3.12 | Black formatter check (>=24.0.0) |
| `codespell.yaml` | Push + PR to main | 3.10 | Spelling check |
| `mdformat.yaml` | Push + PR to main | 3.12 | Markdown format check (docs/ and root *.md) |

### Documentation
| Workflow | Triggers | Python | Description |
|----------|----------|--------|-------------|
| `docs.yaml` | Push + PR to main | 3.10 | Sphinx build; GitHub Pages deploy on push to main |
| `links.yaml` | Weekly (Sun 3am UTC) + manual | 3.12 | Sphinx build + Lychee link checker on HTML output |
| `notebook_tests.yaml` | Push + PR to main (path-filtered: examples/**, tests/test_notebooks.py) | 3.10, 3.13 | Notebook structure and import tests |

## Dependabot
- Monitors GitHub Actions versions and git submodules for updates

## All CI Must Pass Before Merge
- Tests across Python 3.10-3.14
- Linting (ruff), formatting (black), spelling (codespell), markdown (mdformat)
- Documentation builds successfully
- Package installs correctly in fresh environment
