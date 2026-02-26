# Git Workflow

## Branch Strategy
- `stable`: Released versions on PyPI
- `main`/`master`: Most recent usable version
- `develop`: Experimental, evolving features
- Feature branches: `feature/<issue-number>-short-description`
- PRs target `develop` branch

## Commits
- Atomic, focused changes
- Messages <50 chars, no emojis
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
2. Use `gh issue develop` to create branch from `develop`
3. Implement with atomic commits
4. Run tests: `pytest tests/ --cov` and `pytest spec_tests/`
5. Run linting: `ruff check hed/ tests/` and `black --check hed/ tests/`
6. Create PR targeting `develop`
7. Run `/review-pr` for code review
8. Address all critical/important findings
9. Merge when all CI (12 workflows) is green

## Release Process (see RELEASE_GUIDE.md)
1. Update CHANGELOG.md
2. Run code quality checks (black, ruff, codespell)
3. Run all tests (unit + spec)
4. Push CHANGELOG PR, merge to main
5. Create git tag (semantic versioning: MAJOR.MINOR.PATCH)
6. Build: `python -m build`; check: `twine check dist/*`
7. Upload to PyPI: `twine upload dist/*`
8. Verify Zenodo DOI generation
9. setuptools-scm derives version from git tags automatically
