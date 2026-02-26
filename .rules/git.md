# Git Workflow

## Branch Strategy

- `stable`: Released versions on PyPI
- `main`/`master`: Most recent usable version
- `develop`: Experimental, evolving features
- Feature branches: `feature/<issue-number>-short-description`
- PRs target `develop` branch

## Commits

- Atomic, focused changes
- Messages \<50 chars, no emojis
- No AI attribution in commits or PRs
- Pre-commit hook runs ruff check + format on staged .py files

## Submodules

Three submodules under `spec_tests/`, all tracking `main`:

- `hed-tests` - Official HED specification tests
- `hed-examples` - Example BIDS datasets
- `hed-schemas` - Official HED schema repository
- Initialize: `git submodule update --init --recursive`

## PR Process

1. Create issue (except for minor fixes)
1. Use `gh issue develop` to create branch from `develop`
1. Implement with atomic commits
1. Run tests: `pytest tests/ --cov` and `pytest spec_tests/`
1. Run linting: `ruff check hed/ tests/` and `black --check hed/ tests/`
1. Create PR targeting `develop`
1. Run `/review-pr` for code review
1. Address all critical/important findings
1. Merge when all CI (12 workflows) is green

## Release Process (see RELEASE_GUIDE.md)

1. Update CHANGELOG.md
1. Run code quality checks (black, ruff, codespell)
1. Run all tests (unit + spec)
1. Push CHANGELOG PR, merge to main
1. Create git tag (semantic versioning: MAJOR.MINOR.PATCH)
1. Build: `python -m build`; check: `twine check dist/*`
1. Upload to PyPI: `twine upload dist/*`
1. Verify Zenodo DOI generation
1. setuptools-scm derives version from git tags automatically
