# Python Code Standards

## Style

- PEP 8 compliant with 120-char line length (configured in pyproject.toml)
- Google-style docstrings for all public classes and functions
- Type hints where appropriate

## Formatting and Linting

- **ruff:** Lint (`ruff check --fix --unsafe-fixes hed/ tests/`)
  - Rules enabled: E (pycodestyle errors), W (warnings), F (pyflakes), N (pep8-naming), B (bugbear), C4 (comprehensions)
  - Max McCabe complexity: 10
  - Excludes: .git, .venv, __pycache__, build, dist, hed/\_version.py, spec_tests submodules
  - Per-file: F401 ignored in `__init__.py` (unused imports are re-exports)
- **ruff format:** Format (`ruff format hed/ tests/`); 120-char line, matches ruff lint config
- **typos:** Spell checking; skips binary/data files, ignores domain-specific words (hed, parms, etc.)

## Naming Conventions

- Classes: PascalCase (e.g., `HedString`, `HedSchema`, `TabularInput`)
- Functions/methods: snake_case
- Constants: UPPER_SNAKE_CASE
- Private members: leading underscore
- Test methods: may use camelCase (legacy convention; N802 ignored by ruff)

## Import Order (ruff isort)

1. Standard library
2. Third-party packages
3. Local `hed` package (`known-first-party = ["hed"]`)

## Dependencies

- **Core:** click, click-option-group, pandas (\<3.0), numpy (>=2.0.2), openpyxl, defusedxml, inflect, semantic-version, portalocker
- **Dev:** ruff (>=0.8.0), typos (>=1.29.0), mdformat, mdformat-myst
- **Docs:** sphinx (\<10), furo, sphinx-copybutton, myst-parser, sphinx-autodoc-typehints, linkify-it-py
- **Test:** coverage
- **Examples:** jupyter, notebook, nbformat, nbconvert, ipykernel
- **Target:** Python 3.10+

## Common Patterns

- `defusedxml` for XML parsing (security; never use stdlib xml directly)
- DataFrames for tabular data (pandas)
- `portalocker` for file locking (schema cache at `~/.hedtools/`)
- `semantic-version` for schema version comparison
- `click` + `click-option-group` for CLI with grouped options

## Quality Metrics (qlty.toml)

- Max argument count: 4
- Max method complexity: 5
- Max method lines: 50
- Max file lines: 300
- Max method count per class: 20
- Max nested control flow: 4
- Max return statements: 4
- Similar/identical code detection enabled
