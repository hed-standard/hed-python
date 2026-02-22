# HED-Python Test Helpers

Utility scripts for test data management and maintenance.

## update_test_schemas.py

Updates test schemas from the hed-schemas submodule (excludes deprecated schemas).

### Usage

**Prerequisites:**
First initialize the hed-schemas submodule:
```bash
git submodule update --init --recursive
```

**Basic usage (copy standard schemas only):**
```bash
python tests/helpers/update_test_schemas.py
```

**Copy library schemas too:**
```bash
python tests/helpers/update_test_schemas.py --library
```

**Copy different format:**
```bash
python tests/helpers/update_test_schemas.py --format xml
python tests/helpers/update_test_schemas.py --format json
python tests/helpers/update_test_schemas.py --format tsv
```

**Preview what will be copied:**
```bash
python tests/helpers/update_test_schemas.py --dry-run
python tests/helpers/update_test_schemas.py --dry-run --library
```

### Options

- `--format {mediawiki,xml,json,tsv}` - Schema format to copy (default: mediawiki)
- `--library` - Also copy library schemas (default: False, only standard schemas)
- `--dry-run` - Show what would be copied without actually copying

### GitHub Action

You can also trigger this via GitHub Actions:
1. Go to Actions tab in the repository
2. Select "Update Test Schemas" workflow
3. Click "Run workflow"
4. Choose format and whether to include libraries
5. The action will create a PR with the updated schemas

### What it does

- Copies non-deprecated schemas from `hed-schemas/` submodule to `tests/data/schema_tests/`
- Skips schemas in `deprecated/` directories
- Skips README, CHANGELOG, LICENSE files
- Can copy standard schemas and/or library schemas (lang, score, testlib, etc.)

### Notes

- The `hed-schemas/` directory is in `.gitignore` - only the submodule reference is tracked
- Schemas are copied on-demand using this script, either locally or via GitHub Action
- This ensures tests have access to all schema versions without bloating the repository
