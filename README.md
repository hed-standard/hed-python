[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8056010.svg)](https://doi.org/10.5281/zenodo.8056010)
[![Maintainability](https://qlty.sh/gh/hed-standard/projects/hed-python/maintainability.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
[![Code Coverage](https://qlty.sh/gh/hed-standard/projects/hed-python/coverage.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
![Python3](https://img.shields.io/badge/python->=3.10-yellow.svg)
![PyPI - Status](https://img.shields.io/pypi/v/hedtools)
[![Documentation](https://img.shields.io/badge/docs-hed--python-blue.svg)](https://www.hedtags.org/hed-python)

# HEDTools - Python

> Python tools for validation, analysis, and transformation of HED (Hierarchical Event Descriptors) tagged datasets.

## Overview

HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory and real-world events as well as other experimental metadata. HED tags are comma-separated path strings that provide a standardized vocabulary for annotating events and experimental conditions.

**Key Features:**
- Validate HED annotations against schema specifications
- Analyze and summarize HED-tagged datasets
- Transform and remodel event data
- Full HED support in BIDS (Brain Imaging Data Structure)
- HED support in NWB (Neurodata Without Borders) when used the [ndx-hed](https://github.com/hed-standard/ndx-hed) extension.
- Platform-independent and data-neutral
- Command-line tools and Python API

## Quick start

### Online tools (no installation required)

For simple validation or transformation tasks, use the online tools at [https://hedtools.org/hed](https://hedtools.org/hed) - no installation needed!

Browser-based validation (no data upload) is available at [https://www.hedtags.org/hed-javascript](https://www.hedtags.org/hed-javascript)

A development version is available at: [https://hedtools.org/hed_dev](https://hedtools.org/hed_dev)

### Python installation

**Requirements:** Python 3.10 or higher

Install from PyPI:
```bash
pip install hedtools
```

Or install from GitHub (latest):
```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

### Basic usage

```python
from hed import HedString, load_schema_version

# Load the latest HED schema
schema = load_schema_version("8.4.0")

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))")
issues = hed_string.validate(schema)

if issues:
    print(get_printable_issue_string(issues, title="Validation issues found"))
else:
    print("HED string is valid!")
```

### Command-line tools

HEDTools provides a unified command-line interface with git-like subcommands:

```bash
# Main command (new unified interface)
hedpy --help

# Validate a BIDS dataset
hedpy validate-bids /path/to/bids/dataset

# Extract sidecar template from BIDS dataset
hedpy extract-sidecar /path/to/dataset --suffix events

# Validate HED schemas
hedpy schema validate /path/to/schema.xml

# Convert schema between formats (XML, MediaWiki, TSV, JSON)
hedpy schema convert /path/to/schema.xml

# Run remodeling operations on event files
hedpy remodel run /path/to/data /path/to/remodel_config.json
```

**Legacy commands** (deprecated, use `hedpy` instead):
```bash
validate_bids /path/to/dataset
hed_validate_schemas /path/to/schema.xml
run_remodel /path/to/data /path/to/config.json
```

For more examples, see the [user guide](https://www.hedtags.org/hed-python/user_guide.html).

## Documentation

📖 **Full Documentation:** [https://www.hedtags.org/hed-python](https://www.hedtags.org/hed-python)

- [User Guide](https://www.hedtags.org/hed-python/user_guide.html) - Usage instructions
- [API Reference](https://www.hedtags.org/hed-python/api/index.html) - Detailed API documentation  
- [HED Specification](https://www.hedtags.org/hed-specification) - Full HED standard specification

### Building docs locally

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build the documentation
cd docs
sphinx-build -b html . _build/html

# Or use the make command (if available)
make html

# View the built documentation
# Open docs/_build/html/index.html in your browser
```

### Formatting with Black

This project uses [Black](https://black.readthedocs.io/) for consistent code formatting.

```bash
# Check if code is properly formatted (without making changes)
black --check .

# Check and show what would change
black --check --diff .

# Format all Python code in the repository
black .

# Format specific files or directories
black hed/
black tests/
```

**Windows Users:** If you encounter "I/O operation on closed file" errors, use the `--workers 1` flag:
```bash
black --workers 1 --check .
black --workers 1 .
```

**Configuration:** Black settings are in `pyproject.toml` with a line length of 127 characters (matching our ruff configuration).

**Exclusions:** Black automatically excludes `.venv/`, `__pycache__/`, auto-generated files (`hed/_version.py`), and external repos (`spec_tests/hed-examples/`, `spec_tests/hed-specification/`).

**CI Integration:** All code is automatically checked for Black formatting in GitHub Actions. Run `black .` before committing to ensure your code passes CI checks.

## Related Repositories

The HED ecosystem consists of several interconnected repositories:

| Repository | Description |
|------------|-------------|
| [hed-python](https://github.com/hed-standard/hed-python) | Python validation and analysis tools (this repo) |
| [hed-web](https://github.com/hed-standard/hed-web) | Web interface and deployable Docker services |
| [hed-resources](https://github.com/hed-standard/hed-resources) | Example code in Python and MATLAB + HED resources |
| [hed-specification](https://github.com/hed-standard/hed-specification) | Official HED specification documents |
| [hed-schemas](https://github.com/hed-standard/hed-schemas) | Official HED schema repository | 
| [ndx-hed](https://github.com/hed-standard/ndx-hed) | HED support for NWB |  
| [hed-javascript](https://github.com/hed-standard/hed-javascript) | JavaScript HED validation tools |


## Contributing

We welcome contributions! Here's how you can help:

1. **Report issues:** Use [GitHub Issues](https://github.com/hed-standard/hed-python/issues) for bug reports and feature requests
2. **Submit pull requests (PRs):** PRs should target the `main` branch
3. **Improve documentation:** Help us make HED easier to use
4. **Share examples:** Contribute example code and use cases

**Development setup:**
```bash
# Clone the repository
git clone https://github.com/hed-standard/hed-python.git
cd hed-python

# Install in development mode with dependencies
pip install -e .
pip install -r requirements.txt

# Run tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests/path/to/test_file.py
```

For detailed contribution guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon).

## Configuration

### Schema caching

By default, HED schemas are cached in `~/.hedtools/` (location varies by OS).

```python
# Change the cache directory
import hed
hed.schema.set_cache_directory('/custom/path/to/cache')
```

Starting with `hedtools 0.2.0`, local copies of recent schema versions are bundled within the package for offline access.

## Citation

If you use HEDTools in your research, please cite:

```bibtex
@software{hedtools,
  author = {Ian Callanan, Robbins, Kay and others},
  title = {HEDTools: Python tools for HED},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/hed-standard/hed-python},
  doi = {10.5281/zenodo.8056010}
}
```

## License

HEDTools is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

- [Documentation](https://www.hedtags.org/hed-python)
- [GitHub Issues](https://github.com/hed-standard/hed-python/issues)
- [HED Homepage](https://www.hedtags.org)
- Contact: hed-maintainers@gmail.com
