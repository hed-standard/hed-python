# HED Python (hedtools) Instructions

## Project Context

**Purpose:** Core Python library for HED (Hierarchical Event Descriptors) validation, summary, and analysis of event annotations in neuroscience datasets (BIDS compatible).
**Package:** `hedtools` on PyPI
**Tech Stack:** Python 3.10+, setuptools-scm, pandas, numpy, click (CLI)
**Architecture:** Modular package with schema loading/caching, string/tag parsing, validation engine, BIDS integration, and analysis tools.

## Environment Setup

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev,test,docs,examples]"
git submodule update --init --recursive  # fetch test data
pytest tests/ --cov
```

## Package Structure

```
hed/
  cli/         - Click CLI: validate (bids-dataset|string|sidecar|tabular), schema (validate|convert|add-ids), extract (bids-sidecar|tabular-summary)
  errors/      - Error types, messages, reporter, exceptions, known error codes
  models/      - HedString, HedTag, HedGroup, Sidecar, TabularInput, queries, definitions
  schema/      - Schema loading/caching, IO (XML/JSON/Wiki/DataFrame), validation, comparison
  scripts/     - Legacy CLI entry points (deprecated; use hedpy)
  tools/       - Analysis (tag counts, type factors, event manager), BIDS integration, utilities
  validator/   - HED string validation, definition/onset validation, sidecar/spreadsheet validation
tests/         - 60 test files mirroring hed/ structure; unittest-based (no conftest.py)
spec_tests/    - Submodules: hed-tests, hed-examples, hed-schemas; spec compliance tests
docs/          - Sphinx + Furo; autodoc, napoleon, myst-parser, intersphinx (Python, NumPy, Pandas)
examples/      - 10 Jupyter notebooks (validation, extraction, summarization workflows)
```

## Key Commands

```bash
# Tests
pytest tests/ --cov
python -m unittest discover tests

# Spec tests (require submodule init)
pytest spec_tests/

# Linting and formatting
ruff check --fix --unsafe-fixes hed/ tests/
black hed/ tests/
codespell

# Documentation
cd docs && sphinx-build -b html . _build/html

# CLI
hedpy --help
hedpy validate string --hed-string "Event" --schema-version 8.3.0
hedpy validate bids-dataset --bids-path /path/to/bids
hedpy schema convert --input schema.xml --output schema.json
```

## Core Principles

### Testing: Real Data Only

- unittest framework (project standard); pytest as runner
- No mocks; real schemas, real HED strings, real files
- Spec tests via git submodules for official HED test suites
- Details: `.rules/testing.md`

### Code Style

- PEP 8; 127-char line length
- Google-style docstrings for public APIs
- ruff (E, W, F, N, B, C4 rules), black for formatting, codespell for spelling
- Details: `.rules/python.md`

### Git and PRs

- PRs target `develop` branch
- Atomic commits, \<50 chars, no emojis, no AI attribution
- Run `/review-pr` before finalizing
- Details: `.rules/git.md`

## Important Conventions

- Schema versions cached in `~/.hedtools/`; use `portalocker` for cache locking
- HED strings are comma-separated path strings (e.g., `Event, Sensory-event`)
- `HedSchema` (single) and `HedSchemaGroup` (multi-library) handle schema operations
- Public API via `hed/__init__.py`: HedString, HedTag, HedSchema, load_schema, load_schema_version, Sidecar, TabularInput, etc.
- Version managed by setuptools-scm from git tags; `hed/_version.py` is auto-generated
- Releases: tag on main, build with `python -m build`, upload to PyPI via twine, verify on Zenodo

## Context File Management

- `.context/plan.md` - Active tasks only. **After a plan is fully executed, summarize it into 1-2 lines under "Completed" and remove the detailed steps.** Keep this file lean; it is not an archive.
- `.context/ideas.md` - Design concepts and architectural decisions
- `.context/research.md` - Technical explorations and references
- `.context/scratch_history.md` - Failed attempts and lessons learned

## Rules Reference

- `.rules/python.md` - Style, linting, formatting, naming, dependencies
- `.rules/testing.md` - unittest framework, no-mocks policy, spec tests
- `.rules/git.md` - Branch strategy, commits, PR process
- `.rules/ci_cd.md` - All 12 GitHub Actions workflows
- `.rules/code_review.md` - PR review checklist with pr-review-toolkit
