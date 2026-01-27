![PyPI - Status](https://img.shields.io/pypi/v/hedtools) ![Python3](https://img.shields.io/badge/python-%3E=3.10-yellow.svg) [![Maintainability](https://qlty.sh/gh/hed-standard/projects/hed-python/maintainability.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python) [![Code Coverage](https://qlty.sh/gh/hed-standard/projects/hed-python/coverage.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8056010.svg)](https://doi.org/10.5281/zenodo.8056010) [![Docs](https://img.shields.io/badge/docs-hed--python-blue.svg)](https://www.hedtags.org/hed-python)

# HEDTools - Python

```{index} HEDTools, Python tools, validation, analysis
```

> Python tools for validation, analysis, and transformation of HED (Hierarchical Event Descriptors) tagged datasets.

## Overview

```{index} HED, Hierarchical Event Descriptors, BIDS, NWB
```

HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory and real-world events as well as other experimental metadata. HED tags are comma-separated path strings that provide a standardized vocabulary for annotating events and experimental conditions.

**Key Features:**

- Validate HED annotations against schema specifications
- Analyze and summarize HED-tagged datasets
- Full HED support in BIDS (Brain Imaging Data Structure)
- HED support in NWB (Neurodata Without Borders) when used the [ndx-hed](https://github.com/hed-standard/ndx-hed) extension.
- Platform-independent and data-neutral
- Command-line tools and Python API

**Note:** Table remodeling tools have been moved to a separate package. See [table-remodeler](https://pypi.org/project/table-remodeler/) on PyPI or visit [https://www.hedtags.org/table-remodeler](https://www.hedtags.org/table-remodeler) for more information.

## Quick start

```{index} quick start, getting started, installation
```

### Online tools (no installation required)

```{index} online tools, web tools, hedtools.org
```

For simple validation or transformation tasks, use the online tools at [https://hedtools.org/hed](https://hedtools.org/hed) - no installation needed!

Browser-based validation (no data upload) is available at [https://www.hedtags.org/hed-javascript](https://www.hedtags.org/hed-javascript)

A development version of the online tools is available at: [https://hedtools.org/hed_dev](https://hedtools.org/hed_dev)

### Python installation

```{index} installation; Python, pip install, PyPI
```

**Requirements:** Python 3.10 or higher

Install from PyPI:

```bash
pip install hedtools
```

Or install from GitHub (latest):

```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

### Development installation

```{index} development installation, editable install, optional dependencies
```

For development work or to access optional features, install from the cloned repository:

```bash
# Clone the repository
git clone https://github.com/hed-standard/hed-python.git
cd hed-python

# Install in editable mode with base dependencies
pip install -e .

# Install with optional dependency groups
pip install -e ".[dev]"       # Development tools (ruff, black, codespell)
pip install -e ".[docs]"      # Documentation tools (sphinx, furo)
pip install -e ".[test]"      # Testing tools (coverage)
pip install -e ".[examples]"  # Jupyter notebook support

# Install all optional dependencies
pip install -e ".[dev,docs,test,examples]"
```

**Optional dependency groups:**

- `dev` - Code quality tools: ruff (linter), black (formatter), codespell, mdformat
- `docs` - Documentation generation: sphinx, furo theme, myst-parser
- `test` - Code coverage reporting: coverage
- `examples` - Jupyter notebook support: jupyter, notebook, ipykernel

### Basic usage

```{index} usage examples, HedString, load_schema_version, validation example
```

```python
from hed import HedString, load_schema_version


# Load the latest HED schema
schema = load_schema_version("8.4.0")

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))", schema)
issues = hed_string.validate()

if issues:
    print(get_printable_issue_string(issues, title="Validation issues found"))
else:
    print("HED string is valid!")
```

### Command-line tools

```{index} command-line tools, CLI, hedpy, validate-bids, extract-sidecar
```

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

# Convert schema between formats (XML, MEDIAWIKI, TSV, JSON)
hedpy schema convert /path/to/schema.xml

```

**Legacy commands** (deprecated, use `hedpy` instead):

```bash
validate_bids /path/to/dataset
hed_validate_schemas /path/to/schema.xml
```

**Note:** The `run_remodel` command has been removed. Table remodeling functionality is now available in the separate [table-remodeler](https://pypi.org/project/table-remodeler/) package.

For more examples, see the [user guide](https://www.hedtags.org/hed-python/user_guide.html).

### Jupyter notebook examples

```{index} Jupyter notebooks, examples, interactive workflows
```

**Note:** Example notebooks are available in the [GitHub repository](https://github.com/hed-standard/hed-python/tree/main/examples) only, not in the PyPI package.

The [`examples/`](examples/) directory contains Jupyter notebooks demonstrating common HED workflows with BIDS datasets:

- **validate_bids_dataset.ipynb** - Validate HED annotations in a BIDS dataset
- **summarize_events.ipynb** - Summarize event file contents and value counts
- **sidecar_to_spreadsheet.ipynb** - Convert JSON sidecars to spreadsheet format
- **merge_spreadsheet_into_sidecar.ipynb** - Merge spreadsheet annotations into JSON sidecars
- **extract_json_template.ipynb** - Generate JSON sidecar templates from event files
- **find_event_combinations.ipynb** - Find unique combinations of event values
- **validate_bids_dataset_with_libraries.ipynb** - Validate with HED library schemas

To use these notebooks:

```bash
# Clone the repository to get the examples
git clone https://github.com/hed-standard/hed-python.git
cd hed-python

# Install HEDTools with Jupyter support
pip install -e .[examples]

# Launch Jupyter
jupyter notebook examples/
```

See [`examples/README.md`](examples/README.md) for more details.

## Documentation

```{index} documentation, user guide, API reference, Sphinx
```

📖 **Full Documentation:** [https://www.hedtags.org/hed-python](https://www.hedtags.org/hed-python)

- [User guide](https://www.hedtags.org/hed-python/user_guide.html) - Usage instructions
- [API reference](https://www.hedtags.org/hed-python/api/index.html) - Detailed API documentation
- [HED specification](https://www.hedtags.org/hed-specification) - Full HED standard specification

### Building docs locally

```{index} building documentation, sphinx-build
```

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build the documentation
cd docs
sphinx-build -b html . _build/html
```

To iew the built documentation open `docs/_build/html/index.html` in your browser

### Formatting with Black

```{index} Black, code formatting, style guide
```

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

**CI integration:** All code is automatically checked for Black formatting in GitHub Actions. Run `black .` before committing to ensure your code passes CI checks.

## Related repositories

```{index} HED ecosystem, repositories, hed-schemas, hed-specification
```

The HED ecosystem consists of several interconnected repositories:

| Repository                                                             | Description                                      |
| ---------------------------------------------------------------------- | ------------------------------------------------ |
| [hed-python](https://github.com/hed-standard/hed-python)               | Python validation and analysis tools (this repo) |
| [hed-web](https://github.com/hed-standard/hed-web)                     | Web interface and deployable Docker services     |
| [hed-resources](https://github.com/hed-standard/hed-resources)         | Tutorials and other HED resources                |
| [hed-specification](https://github.com/hed-standard/hed-specification) | Official HED specification documents             |
| [hed-schemas](https://github.com/hed-standard/hed-schemas)             | Official HED schema repository                   |
| [table-remodeler](https://github.com/hed-standard/table-remodeler)     | Table transformation and remodeling tools        |
| [ndx-hed](https://github.com/hed-standard/ndx-hed)                     | HED support for NWB                              |
| [hed-javascript](https://github.com/hed-standard/hed-javascript)       | JavaScript HED validation tools                  |

## Contributing

```{index} contributing, development setup, pull requests
```

We welcome contributions! Here's how you can help:

1. **Report issues:** Use [GitHub Issues](https://github.com/hed-standard/hed-python/issues) for bug reports and feature requests
2. **Submit pull requests (PRs):** PRs should be from a non-main fork and target the `main` branch
3. **Improve documentation:** Help us make HED easier to use
4. **Share examples:** Contribute example code and use cases

**Development setup:**

```bash
# Clone the repository
git clone https://github.com/hed-standard/hed-python.git
cd hed-python

# Install in development mode with all dependencies (including Jupyter)
pip install -e .[examples]
pip install -r requirements-dev.txt

# Or just core development dependencies
pip install -e .
pip install -r requirements.txt

# Run tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests/path/to/test_file.py

# Test notebooks (requires Jupyter dependencies)
python -m unittest tests.test_notebooks
```

For detailed contribution guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).

## Configuration

```{index} configuration, schema caching, cache directory
```

### Schema caching

~~~{index} schema; caching, ~/.hedtools
~~~

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
- [GitHub issues](https://github.com/hed-standard/hed-python/issues)
- [HED Homepage](https://www.hedtags.org)
- Contact: [hed-maintainers@gmail.com](mailto:hed-maintainers@gmail.com)
