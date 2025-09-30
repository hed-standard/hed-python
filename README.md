[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8056010.svg)](https://doi.org/10.5281/zenodo.8056010)
[![Maintainability](https://qlty.sh/gh/hed-standard/projects/hed-python/maintainability.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
[![Code Coverage](https://qlty.sh/gh/hed-standard/projects/hed-python/coverage.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
![Python3](https://img.shields.io/badge/python->=3.9-yellow.svg)
![PyPI - Status](https://img.shields.io/pypi/v/hedtools)
[![Documentation](https://img.shields.io/badge/docs-hedtags.org-blue.svg)](https://www.hedtags.org/hed-python)

# HEDTools - Python

> Python tools for validation, analysis, and transformation of HED (Hierarchical Event Descriptors) tagged datasets.

## Overview

HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory and real-world events as well as other experimental metadata. HED tags are comma-separated path strings that provide a standardized vocabulary for annotating events and experimental conditions.

**Key Features:**
- ✅ Validate HED annotations against schema specifications
- 📊 Analyze and summarize HED-tagged datasets
- 🔄 Transform and remodel event data
- 📁 Full BIDS (Brain Imaging Data Structure) dataset support
- 🌐 Platform-independent and data-neutral
- 🔧 Command-line tools and Python API

## Quick Start

### Online Tools (No Installation Required)

For simple validation or transformation tasks, use the online tools at [https://hedtools.org](https://hedtools.org) - no installation needed!

A development version is available at: [https://hedtools.org/hed_dev](https://hedtools.org/hed_dev)

### Python Installation

**Requirements:** Python 3.9 or higher

Install from PyPI:
```bash
pip install hedtools
```

Or install from GitHub (latest):
```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

### Basic Usage

```python
from hed import HedString, load_schema

# Load the latest HED schema
schema = load_schema()

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))")
issues = hed_string.validate(schema)

if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✓ HED string is valid!")
```

### Command-Line Tools

HEDTools includes several command-line utilities:

```bash
# Validate a BIDS dataset
validate_bids /path/to/bids/dataset

# Run remodeling operations on event files
run_remodel /path/to/remodel_config.json /path/to/data

# Validate HED schemas
hed_validate_schemas /path/to/schema.xml
```

For more examples, see the [user guide](https://www.hedtags.org/hed-python/user_guide.html).

## Documentation

📖 **Full Documentation:** [https://www.hedtags.org/hed-python](https://www.hedtags.org/hed-python)

- [User Guide](https://www.hedtags.org/hed-python/user_guide.html) - Comprehensive usage instructions
- [API Reference](https://www.hedtags.org/hed-python/api/index.html) - Detailed API documentation  
- [HED Specification](https://hed-specification.readthedocs.io/) - Full HED standard specification

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Build the documentation
mkdocs build

# Serve locally with live reload at http://localhost:8000
mkdocs serve
```

## Related Repositories

The HED ecosystem consists of several interconnected repositories:

| Repository | Description |
|------------|-------------|
| [hed-python](https://github.com/hed-standard/hed-python) | Python validation and analysis tools (this repo) |
| [hed-web](https://github.com/hed-standard/hed-web) | Web interface and deployable Docker services |
| [hed-examples](https://github.com/hed-standard/hed-examples) | Example code in Python and MATLAB + HED resources |
| [hed-specification](https://github.com/hed-standard/hed-specification) | Official HED specification documents |
| [hed-schemas](https://github.com/hed-standard/hed-schemas) | Official HED schema repository |

### Branch Strategy

| Branch | Purpose | Synchronized With |
|--------|---------|-------------------|
| `stable` | Officially released on PyPI as tagged versions | `stable@hed-web`, `stable@hed-specification`, `stable@hed-examples` |
| `main` | Latest stable development version | `latest@hed-web`, `latest@hed-specification`, `latest@hed-examples` |

## Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues:** Use [GitHub Issues](https://github.com/hed-standard/hed-python/issues) for bug reports and feature requests
2. **Submit Pull Requests:** PRs should target the `main` branch
3. **Improve Documentation:** Help us make HED easier to use
4. **Share Examples:** Contribute example code and use cases

**Development Setup:**
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

### Schema Caching

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
  author = {Robbins, Kay and others},
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

- 📖 [Documentation](https://www.hedtags.org/hed-python)
- 💬 [GitHub Issues](https://github.com/hed-standard/hed-python/issues)
- 🌐 [HED Homepage](https://www.hedtags.org)
- 📧 Contact: Kay.Robbins@utsa.edu
