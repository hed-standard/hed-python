# Introduction to hedtools

## What is HED?

HED (Hierarchical Event Descriptors) is a framework for systematically describing events and experimental metadata in machine-actionable form. HED provides:

- **Controlled vocabulary** for annotating experimental data and events
- **Standardized infrastructure** enabling automated analysis and interpretation
- **Integration** with major neuroimaging standards (BIDS and NWB)

For more information, visit the [HED project homepage](https://www.hedtags.org).

## What is hedtools?

The **hedtools** Python package (`hed-python` repository) provides:

- **Core validation** of HED annotations against schema specifications
- **BIDS integration** for neuroimaging dataset processing
- **Analysis tools** for event summarization, temporal processing, and tag analysis
- **Transformation utilities** for converting between formats (JSON ↔ spreadsheet)
- **Command-line interface** for scripting and automation
- **Jupyter notebooks** for interactive analysis workflows

### Related tools and resources

- **[HED homepage](https://www.hedtags.org)**: Overview and links for HED
- **[HED Schemas](https://github.com/hed-standard/hed-schemas)**: Standardized vocabularies in XML/MediaWiki/OWL formats
- **[HED Specification](https://www.hedtags.org/hed-specification/)**: Formal specification defining HED annotation rules
- **[HED Online Tools](https://hedtools.org/hed)**: Web-based interface requiring no programming
- **[HED Examples](https://github.com/hed-standard/hed-examples)**: Example datasets annotated with HED
- **[HED Resources](https://www.hedtags.org/hed-resources)**: Comprehensive tutorials and documentation
- **[HED MATLAB Tools](https://www.hedtags.org/hed-resources/HedMatlabTools.html)**: MATLAB wrapper for Python tools

## Installation

### From PyPI (Recommended)

Install the latest stable release:

```bash
pip install hedtools
```

**Note**: The PyPI package includes the core hedtools library but **not the example Jupyter notebooks**. To access the notebooks, see the options below.

### For Jupyter Notebook Examples

The example notebooks are only available in the GitHub repository. Choose one of these options:

**Option 1: Clone the full repository**

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -r requirements.txt
pip install jupyter notebook
# Notebooks are in: examples/
```

**Option 2: Download just the examples directory**

```bash
svn export https://github.com/hed-standard/hed-python/trunk/examples
cd examples
pip install hedtools jupyter notebook
```

See [examples/README.md](../examples/README.md) for detailed notebook documentation.

### From GitHub (Latest Development Version)

```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

### For development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -e .
```

### Python requirements

- **Python 3.10 or later** is required
- Core dependencies: pandas, numpy, defusedxml, openpyxl
- Jupyter support: Install with `pip install jupyter notebook`

## Getting help

### Documentation resources

- **[User Guide](user_guide.md)**: Step-by-step instructions and examples
- **[API reference](api/index.html)**: Detailed function and class documentation
- **[HED specification](https://hed-specification.readthedocs.io/)**: Formal annotation rules
- **[HED resources](https://www.hedtags.org/hed-resources)**: HED tutorials and guides

### Support

- **Issues and bugs**: [Open an issue](https://github.com/hed-standard/hed-python/issues) on GitHub
- **Questions**: Use GitHub issues
- **Online validation**: Try [HED online tools](https://hedtools.org/hed) for web-based access

## Quick start

### Basic validation example

```python
from hed import HedString, load_schema, get_printable_issue_string

# Load the latest HED schema
schema = load_schema()

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))", schema)
issues = hed_string.validate(schema)

if issues:
    print(get_printable_issue_string(issues, "Validation issues found:"))
else:
    print("✓ HED string is valid!")
```

### BIDS dataset validation

```python
from hed.tools import BidsDataset

# Load and validate a BIDS dataset
dataset = BidsDataset("path/to/bids/dataset")  # the description has schema version
issues = dataset.validate()

if issues:
    print(f"Found {len(issues)} validation issues")
else:
    print("✓ Dataset HED annotations are valid!")
```

### Working with sidecars

```python
from hed import Sidecar, load_schema_version

# Load and validate a BIDS JSON sidecar
schema = load_schema_version("8.4.0")
sidecar = Sidecar("task-rest_events.json")
issues = sidecar.validate(schema)
```

## Next steps

- **Explore the [User Guide](user_guide.md)** for detailed workflows
- **Try the [Jupyter notebooks](../examples/README.md)** for interactive examples
- **Check the [API Reference](api/index.html)** for complete function documentation
- **Validate your data** using the [HED online tools](https://hedtools.org/hed) or the [HED browser-based tools](https://www.hedtags.org/hed-javascript)
