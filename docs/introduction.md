# Introduction to HEDTools

## What is HED?

HED (Hierarchical Event Descriptors) is a framework for systematically describing events and experimental metadata in machine-actionable form. HED provides:

- **Controlled vocabulary** for annotating experimental data and events
- **Standardized infrastructure** enabling automated analysis and interpretation
- **Integration** with major neuroimaging standards (BIDS and NWB)

For more information, visit the HED project [homepage](https://www.hedtags.org) and the [resources page](https://www.hedtags.org/hed-resources). The [table-remodeler](https://www.hedtags.org/table-remodeler) tools are now in a separate repository.

## What is HEDTools?

The **hedtools** Python package (`hed-python` repository) provides:

- **Core validation** of HED annotations against schema specifications
- **BIDS integration** for neuroimaging dataset processing
- **Analysis tools** for event summarization, temporal processing, and tag analysis
- **HED schema tools** for validating, comparing and converting HED schemas
- **Command-line interface** for scripting and automation
- **Jupyter notebooks** for interactive analysis workflows

### Related tools and resources

- **[HED homepage](https://www.hedtags.org)**: Overview and links for HED
- **[HED schemas](https://github.com/hed-standard/hed-schemas)**: Standardized vocabularies in XML/MEDIAWIKI/TSV/JSON formats
- **[HED specification](https://www.hedtags.org/hed-specification/)**: Formal specification defining HED annotation rules
- **[HED online tools](https://hedtools.org/hed)**: Web-based interface requiring no programming
- **[HED examples](https://github.com/hed-standard/hed-examples)**: Example datasets annotated with HED
- **[HED resources](https://www.hedtags.org/hed-resources)**: Comprehensive tutorials and documentation
- **[HED MATLAB tools](https://www.hedtags.org/hed-matlab)**: MATLAB wrapper for Python tools
- **[Table remodeler](https://www.hedtags.org/table-remodeler)**: table analysis and transformations -- formerly part of hedtools

## Installation

### From PyPI (recommended)

Install the latest stable release:

```bash
pip install hedtools
```

**Note**: The PyPI package includes the core hedtools library but **not the example Jupyter notebooks**. To access the notebooks, see the options below.

### For Jupyter notebook examples

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

See [examples/README.md](https://github.com/hed-standard/hed-python/tree/main/examples) for detailed notebook documentation.

### From GitHub (latest development version)

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

- **[User guide](user_guide.md)**: Step-by-step instructions and examples
- **[API reference](api/index.html)**: Detailed function and class documentation
- **[HED specification](https://hed-specification.readthedocs.io/)**: Formal annotation rules
- **[HED resources](https://www.hedtags.org/hed-resources)**: HED tutorials and guides

### Support

- **Issues and bugs**: Open an [**issue**](https://github.com/hed-standard/hed-python/issues) on GitHub
- **Questions**: Use GitHub issues
- **Online validation**: Try [HED online tools](https://hedtools.org/hed) for web-based access
- **Contact**: Email [hed.maintainers@gmail.com](mailto:hed.maintainers@gmail.com)

## Quick start

### Basic validation example

```python
from hed import HedString, load_schema, get_printable_issue_string

# Load the latest HED schema
schema = load_schema('8.4.0')

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))", schema)
issues = hed_string.validate()

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
    print(get_printable_issue_string(issues, "Validation issues found:"))
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

- Explore the [**User guide**](user_guide.md) for detailed workflows
- Try the [**Jupyter notebooks**](https://github.com/hed-standard/hed-python/tree/main/examples) for interactive examples
- Check the [**API reference**](api/index.html) for complete function documentation
- Validate your data using the HED [**online tools**](https://hedtools.org/hed) or the HED [**browser-based tools**](https://www.hedtags.org/hed-javascript)
