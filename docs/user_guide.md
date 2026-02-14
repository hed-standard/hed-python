```{meta}
---
description: Complete user guide for Python HEDTools - validation, BIDS 
  integration, analysis, and command-line tools for HED annotations
keywords: HED tutorial, Python guide, validation examples, BIDS datasets, 
  sidecar files, command-line interface, Jupyter notebooks, HED overview, event 
  descriptors, neuroscience, schema
---
```

# Python HEDTools guide

```{index} user guide, tutorial, getting started, HED, Hierarchical Event Descriptors
```

HED (Hierarchical Event Descriptors) is a framework for systematically describing events and experimental metadata in machine-actionable form. This guide provides comprehensive documentation for using the HED Python tools for validation, BIDS integration, and analysis:

01. [What is HED?](#what-is-hed)
02. [Getting started](#getting-started)
03. [Working with HED schemas](#working-with-hed-schemas)
04. [Validating HED strings](#validating-hed-strings)
05. [Working with BIDS datasets](#working-with-bids-datasets)
06. [Working with sidecars](#working-with-sidecars)
07. [Jupyter notebooks](#jupyter-notebooks)
08. [Command-line tools](#command-line-tools)
09. [Best practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Getting started

```{index} installation, pip, PyPI
```

### Installation

#### From PyPI (recommended)

Install the latest stable release:

```bash
pip install hedtools
```

**Note**: The PyPI package includes the core hedtools library but **not the example Jupyter notebooks**. To access the notebooks, see the options below.

#### For Jupyter notebook examples

The example notebooks are only available in the GitHub repository. Choose one of these options:

**Option 1: Clone the full repository**

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -e .[examples]
# Notebooks are in: examples/
```

**Option 2: Download just the examples directory**

```bash
svn export https://github.com/hed-standard/hed-python/trunk/examples
cd examples
pip install hedtools jupyter notebook
```

See [examples/README.md](https://github.com/hed-standard/hed-python/tree/main/examples) for detailed notebook documentation.

#### From GitHub (latest development version)

```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

#### For development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -e .
```

#### Python requirements

- **Python 3.10 or later** is required
- Core dependencies: pandas, numpy, defusedxml, openpyxl
- Jupyter support: Install with `pip install jupyter notebook`

### Basic example

Here's a simple example to get you started with HED validation:

```python
from hed import HedString, load_schema_version, get_printable_issue_string

# Load a specific HED schema version
schema = load_schema_version("8.4.0")

# Create a HED string (schema is passed in constructor)
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))", schema)

# Validate the string
issues = hed_string.validate()

if issues:
    print(get_printable_issue_string(issues, title="Validation issues found:"))
else:
    print("✓ HED string is valid!")
```

## Working with HED schemas

```{index} schema; loading, schema; validation, load_schema, load_schema_version
```

### Loading schemas

```python
from hed import load_schema, load_schema_version


# Load a specific version (auto-cached in ~/.hedtools/)
schema = load_schema_version("8.4.0")

# Load from a local file (in this case XML -- use directory path for TSV)
schema = load_schema("path/to/schema.xml")

# Load from URL (this URL is the raw content of a HED standard prerelease)
schema = load_schema("https://raw.githubusercontent.com/hed-standard/hed-schemas/refs/heads/main/standard_schema/prerelease/HED8.5.0.json")
```

**Note:** The released schemas are automatically downloaded and cached in `~/.hedtools/` for offline use.

### Working with library schemas

```{index} schema; library, library schema, score library, lang library
```

HED supports library schemas that extend the base vocabulary.

```python
from hed import load_schema_version


# Load base schema with a library
schema = load_schema_version("score_2.1.0")

# For multiple libraries
schema = load_schema_version(["score_2.1.0", "lang_1.1.0"])
```

Note: It is now standard for a library schema to be partnered with a standard schema. In general, you should not use an earlier, non-partnered versions of a library schema.

## Validating HED strings

```{index} validation; HED strings, HedString class, validate method
```

### Basic validation

The HED string must be created with a schema, and validation is performed on the string object:

```python
from hed import HedString, load_schema_version


schema = load_schema_version("8.4.0")
hed_string = HedString("Red, Blue, Green", schema)
issues = hed_string.validate()

```

### Batch validation

```python
from hed import HedString, load_schema_version, get_printable_issue_string


schema = load_schema_version("8.4.0")

hed_strings = [
    "Sensory-event, Visual-presentation",
    "Invalid-tag, Another-invalid",
    "(Red, Square)"
]
issues = []
for i, hed_str in enumerate(hed_strings, 1):
    hed_string = HedString(hed_str, schema)
    issues += hed_string.validate()
if issues:
    print(get_printable_issue_string(issues))
```

## Working with BIDS datasets

```{index} BIDS; dataset validation, BidsDataset class, dataset_description.json
```

### Dataset-level validation

```python
from hed.tools import BidsDataset


# Load BIDS dataset (automatically loads schema from dataset_description.json)
dataset = BidsDataset("path/to/bids/dataset")

# Validate all HED annotations in the dataset
issues = dataset.validate()

if issues:
    print(f"Found {len(issues)} validation issues")
else:
    print("✓ All HED annotations are valid!")

# Include warnings in validation
issues = dataset.validate(check_for_warnings=True)
```

Since a BIDS dataset includes the HED version in its `dataset_description.json`, a HED version is not necessary for validation. The `BidsDataset` only holds information about the relevant `.tsv` and `.json` files, not the imaging data. The constructor has a number of parameters that restrict which of these files are considered. The relevant JSON files are all read in, but the `.tsv` content is only loaded when needed.

### Working with individual event files

```{index} TabularInput, event files, tsv files
```

```python
from hed import TabularInput, load_schema_version


# Load schema
schema = load_schema_version("8.4.0")

# Load events file with sidecar
tabular = TabularInput(
    file="sub-01_task-rest_events.tsv",
    sidecar="task-rest_events.json"
)

# Validate the file
issues = tabular.validate(schema)

# Extract definitions from the file
def_dict = tabular.get_def_dict(schema)
```

## Working with sidecars

```{index} Sidecar class, JSON sidecar, sidecar validation
```

### Loading and validating sidecars

```python
from hed import Sidecar, load_schema_version


schema = load_schema_version("8.4.0")

# Load a JSON sidecar
sidecar = Sidecar("task-rest_events.json")

# Validate the sidecar
issues = sidecar.validate(schema)
```

### Extracting definitions

```{index} definitions, DefinitionDict, get_def_dict
```

```python
from hed import Sidecar, load_schema_version


schema = load_schema_version("8.4.0")
sidecar = Sidecar("task-rest_events.json")

# Get all definitions from the sidecar
def_dict = sidecar.get_def_dict(schema)
```

### Saving sidecars

```python
from hed import Sidecar

sidecar = Sidecar("task-rest_events.json")

# Save as formatted JSON file
sidecar.save_as_json("output_sidecar.json")

# Get as a formatted JSON string
json_string = sidecar.get_as_json_string()
```

## Jupyter notebooks

```{index} Jupyter notebooks, examples, workflows
```

The [examples](https://github.com/hed-standard/hed-python/tree/main/examples) directory in the GitHub [hed-python](https://github.com/hed-standard/hed-python) repository contains Jupyter notebooks for BIDS annotation workflows. These notebooks are **not included in the PyPI package**.

### Available notebooks

| Notebook                                                                                                                                               | Purpose                                                            |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| [extract_json_template.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/extract_json_template.ipynb)                               | Create JSON sidecar template from all event files                  |
| [find_event_combinations.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/find_event_combinations.ipynb)                           | Extract unique combinations of column values                       |
| [merge_spreadsheet_into_sidecar.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/merge_spreadsheet_into_sidecar.ipynb)             | Merge edited spreadsheet of HED annotations back into JSON sidecar |
| [sidecar_to_spreadsheet.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/sidecar_to_spreadsheet.ipynb)                             | Convert JSON sidecar to spreadsheet for editing                    |
| [summarize_events.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/summarize_events.ipynb)                                         | Summarize event file contents and value distributions              |
| [validate_bids_dataset.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_dataset.ipynb)                               | Validate HED annotations in a BIDS dataset                         |
| [validate_bids_dataset_with_libraries.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_dataset_with_libraries.ipynb) | Validate with HED library schemas                                  |
| [validate_bids_datasets.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_datasets.ipynb)                             | Batch validate multiple BIDS datasets                              |

### Getting the notebooks

**Option 1: Clone the repository**

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -e .[examples]
```

**Option 2: Download just the examples**

```bash
svn export https://github.com/hed-standard/hed-python/trunk/examples
cd examples
pip install hedtools jupyter notebook
```

### Typical annotation workflow

1. **Summarize events** - Understand your event file structure
2. **Extract template** - Create initial JSON sidecar template
3. **Convert to spreadsheet** (optional) - Convert JSON HED to spreadsheet format for easier editing
4. **Edit annotations** - Add HED tags to your sidecar or spreadsheet
5. **Merge back** (if using spreadsheet) - Convert spreadsheet back to JSON
6. **Validate** - Check for errors and iterate until valid

See the examples [README](https://github.com/hed-standard/hed-python/tree/main/examples) for detailed documentation of each notebook.

## Command-line tools

```{index} CLI, command-line interface, hedpy, scripts
```

HEDTools provides a unified command-line interface (CLI) using a **git-style command structure**. The main command is `hedpy`, which provides subcommands for validation and schema management.

### Available commands

| Command                       | Description                                                 |
| ----------------------------- | ----------------------------------------------------------- |
| **Annotation management**     |                                                             |
| `hedpy validate bids-dataset` | Validate HED annotations in BIDS datasets                   |
| `hedpy validate string`       | Validate HED annotations in a string                        |
| `hedpy validate sidecar`      | Validate HED annotations in a JSON sidecar                  |
| `hedpy validate tabular`      | Validate HED annotations in a tabular file (TSV)            |
| `hedpy extract bids-sidecar`  | Extract JSON sidecar template from tabular (`.tsv`) files   |
| **Schema management**         |                                                             |
| `hedpy schema validate`       | Validate HED schema files                                   |
| `hedpy schema convert`        | Convert schemas between formats (XML, MEDIAWIKI, TSV, JSON) |
| `hedpy schema add-ids`        | Add unique HED IDs to schema terms                          |

### Installation and basic usage

The CLI is installed automatically with the hedtools package:

```bash
pip install hedtools
```

Get help on available commands:

```bash
# General help
hedpy --help

# Help for a specific command
hedpy validate bids-dataset --help

# Help for command groups
hedpy schema --help
```

Get version information:

```bash
hedpy --version
```

______________________________________________________________________

### BIDS validation

Validate HED annotations in BIDS datasets using `hedpy validate bids-dataset`.

#### Basic validation

```bash
# Validate a BIDS dataset
hedpy validate bids-dataset /path/to/bids/dataset

# Include warnings in addition to errors
hedpy validate bids-dataset /path/to/bids/dataset -w

# Enable verbose output
hedpy validate bids-dataset /path/to/bids/dataset -v
```

#### Output options

```bash
# Save results to a file
hedpy validate bids-dataset /path/to/bids/dataset -o validation_results.txt

# Output in compact JSON format (array of issues only)
hedpy validate bids-dataset /path/to/bids/dataset -f json -o results.json

# Pretty-printed JSON with version metadata (recommended for saving)
hedpy validate bids-dataset /path/to/bids/dataset -f json_pp -o results.json

# Print to stdout AND save to file
hedpy validate bids-dataset /path/to/bids/dataset -o results.txt -p
```

**Output format differences:**

- `text`: Human-readable format with issue counts and descriptions (default)
- `json`: Compact JSON array of issues only, suitable for piping or programmatic processing
- `json_pp`: Pretty-printed JSON object with `issues` array and `hedtools_version` metadata, with proper indentation for readability

#### Filtering validation

```bash
# Validate specific file types (default: events, participants)
hedpy validate bids-dataset /path/to/bids/dataset -s events -s participants -s sessions

# Exclude certain directories (default: sourcedata, derivatives, code, stimuli)
hedpy validate bids-dataset /path/to/bids/dataset -x derivatives -x sourcedata -x mydata

# Limit number of errors reported per error type
hedpy validate bids-dataset /path/to/bids/dataset -el 5

# Apply error limit per file instead of overall
hedpy validate bids-dataset /path/to/bids/dataset -el 5 -ef
```

#### Logging options

```bash
# Set log level
hedpy validate bids-dataset /path/to/bids/dataset -l DEBUG

# Save logs to file
hedpy validate bids-dataset /path/to/bids/dataset -lf validation.log

# Save logs to file without stderr output
hedpy validate bids-dataset /path/to/bids/dataset -lf validation.log -lq
```

#### Complete example

```bash
# Comprehensive validation with all options
hedpy validate bids-dataset /path/to/bids/dataset \
  -w \
  -v \
  -f json_pp \
  -o validation_results.json \
  -s events \
  -x derivatives \
  -el 10 \
  -lf validation.log
```

______________________________________________________________________

### String validation

Validate a HED string using `hedpy validate string`.

```bash
# Basic validation
hedpy validate string "Event, Action" -sv 8.3.0

# With definitions
hedpy validate string "Event, Def/MyDef" \
  -sv 8.4.0 \
  -d "(Definition/MyDef, (Action, Move))"

# Check for warnings
hedpy validate string "Event, Action/Button-press" -sv 8.4.0 -w
```

______________________________________________________________________

### Sidecar validation

Validate a HED JSON sidecar using `hedpy validate sidecar`.

```bash
# Basic validation
hedpy validate sidecar task-rest_events.json -sv 8.3.0

# With multiple schemas
hedpy validate sidecar task-rest_events.json -sv 8.3.0 -sv score_1.1.0

# Check for warnings and save to file
hedpy validate sidecar task-rest_events.json -sv 8.4.0 -w -o results.txt
```

______________________________________________________________________

### Tabular validation

Validate a HED tabular file (TSV) using `hedpy validate tabular`.

```bash
# Basic validation
hedpy validate tabular events.tsv -sv 8.3.0

# With a sidecar
hedpy validate tabular events.tsv -s sidecar.json -sv 8.3.0

# Limit errors
hedpy validate tabular events.tsv -sv 8.3.0 -el 5

# Check for warnings and output JSON
hedpy validate tabular events.tsv -sv 8.3.0 -w -f json -o results.json
```

______________________________________________________________________

### Sidecar template extraction

Extract a JSON sidecar template from BIDS event files using `hedpy extract bids-sidecar`.

#### Basic extraction

```bash
# Extract template for events files
hedpy extract bids-sidecar /path/to/bids/dataset -s events

# Save to specific file
hedpy extract bids-sidecar /path/to/bids/dataset -s events -o task_events.json
```

#### Column handling

```bash
# Specify value columns (use single annotation for column with # placeholder)
hedpy extract bids-sidecar /path/to/bids/dataset -s events \
  -vc response_time -vc accuracy -vc subject_id

# Skip specific columns (default: onset, duration, sample)
hedpy extract bids-sidecar /path/to/bids/dataset -s events \
  -sc onset -sc duration -sc trial_type

# Exclude certain directories
hedpy extract bids-sidecar /path/to/bids/dataset -s events \
  -x derivatives -x pilot_data
```

#### Complete example

```bash
# Extract events template with custom column handling
hedpy extract bids-sidecar /path/to/bids/dataset \
  -s events \
  -vc response_time \
  -vc reaction_time \
  -sc onset -sc duration \
  -o events_template.json \
  -v
```

______________________________________________________________________

### Schema development

```{index} schema; development, schema; conversion, schema; validation, hedpy schema
```

The `hedpy schema` command group provides tools for validating, converting, and managing HED schemas during development.

#### Schema validation

Validate HED schema files:

```bash
# Validate a single schema
hedpy schema validate /path/to/schema.xml

# Validate multiple schemas
hedpy schema validate schema1.json schema2.xml schema3.mediawiki

# Validate with verbose output
hedpy schema validate /path/to/schema.xml -v

# Validate all format versions (.xml, .mediawiki, .tsv, .json) of the schema
# This forces validation of all 4 formats and checks equivalence for prerelease schemas
hedpy schema validate /path/to/schema.xml --add-all-extensions
```

#### Schema format conversion

Convert schemas between formats (XML, MEDIAWIKI, TSV, JSON):

```bash
# Convert schema (format auto-detected from extension)
hedpy schema convert schema.xml  # Creates schema.mediawiki, schema.tsv, etc.

# Convert multiple schemas
hedpy schema convert schema1.xml schema2.xml
```

**Supported formats:**

- `.xml` - XML format (standard)
- `.mediawiki` - MEDIAWIKI format
- `.tsv` - TSV (tab-separated value) format
- `.json` - JSON format

______________________________________________________________________

### Schema release

Once a schema has been developed and tested, these commands prepare it for official release. These operations are performed by the HED maintainers on schemas in the **prerelease directory** of the hed-schemas repository before moving them to the stable release directory.

#### Add HED IDs

```{index} HED IDs, schema; IDs, schema; release
```

HED IDs are unique identifiers assigned to each schema term, enabling stable references across schema versions and format conversions. These IDs must be added before releasing a schema.

```bash
# Add IDs to a standard schema prerelease
hedpy schema add-ids /path/to/hed-schemas standard 8.5.0

# Add IDs to a library schema prerelease
hedpy schema add-ids /path/to/hed-schemas score 2.2.0
```

**Requirements:**

- Path must be to a hed-schemas repository clone
- Schema name and version must match directory structure
- **Only works on schemas in a prerelease directory**
- Modifies all schema formats (XML, MEDIAWIKI, TSV, JSON) in-place
- Should be run after all schema content changes are finalized

**Best practices:**

1. Validate schema thoroughly before adding IDs
2. Convert to all formats and verify equivalence
3. Add HED IDs only once - they should remain stable
4. Commit changes to version control before moving to stable release

**Note:** Ontology generation (OMN/OWL format) has been moved to the separate [hed-ontology](https://github.com/hed-standard/hed-ontology) repository.

______________________________________________________________________

### Legacy script access

For backward compatibility, you can still access scripts directly using Python module syntax:

```bash
# Validation
python -m hed.scripts.validate_bids /path/to/dataset --check-warnings
python -m hed.scripts.validate_hed_string "Event, Action" -sv 8.3.0
python -m hed.scripts.validate_hed_sidecar sidecar.json -sv 8.3.0
python -m hed.scripts.validate_hed_tabular events.tsv -sv 8.3.0

# Sidecar extraction
python -m hed.scripts.hed_extract_bids_sidecar /path/to/dataset -s events

# Schema validation
python -m hed.scripts.validate_schemas schema.xml
```

**However, the `hedpy` CLI is the recommended interface** as it provides a more consistent and discoverable command structure.

______________________________________________________________________

### Common workflows

#### Workflow 1: Getting help

Each command provides help at several levels

```bash
# Top-level help
hedpy --help

# Command-specific help
hedpy validate bids-dataset --help
hedpy schema validate --help

# Command group help
hedpy schema --help
```

#### Workflow 2: First-time BIDS dataset validation

```bash
# Step 1: Extract sidecar template
hedpy extract bids-sidecar /path/to/dataset -s events -o events.json

# Step 2: Edit events.json to add HED tags
# (manual editing step)

# Step 3: Validate with warnings
hedpy validate bids-dataset /path/to/dataset -w -v -o validation.txt

# Step 4: Fix issues and re-validate
hedpy validate bids-dataset /path/to/dataset -w
```

#### Workflow 3: Schema development and testing

```bash
# Step 1: Validate schema
hedpy schema validate my_schema.xml -v

# Step 2: Convert to all formats
hedpy schema convert my_schema.xml

# Step 3: Validate all formats are equivalent (for prerelease schemas)
hedpy schema validate my_schema.xml --add-all-extensions
```

#### Workflow 4: Preparing for schema release

```bash
# Add HED IDs
hedpy schema add-ids /path/to/hed-schemas my_library 1.0.0
```

______________________________________________________________________

### Debugging tips

1. **Use verbose mode (`-v`)** during development to see detailed progress
2. **Save output to files (`-o`)** for documentation and tracking
3. **Choose the right output format**:
   - Use `json_pp` for human-readable saved results with version tracking
   - Use `json` for compact output when piping to other tools
   - Use `text` (default) for quick reviews with error counts
4. **Leverage tab completion** in your shell for command discovery
5. **Use `--help` liberally** to explore options for each command
6. **Test on small datasets first** before processing large corpora

## Best practices

```{index} best practices, schema management, validation workflow
```

### Schema management

1. **Don't modify released schemas** - they're immutable and shared
2. **Check and recheck prerelease schema validity** - once released it's permanent
3. **Compare the schema with previous version** - make sure that changes are not breaking (major semantic version change)

### Validation workflow

1. **Validate early and often** during annotation development
2. **Fix errors before warnings** - errors indicate invalid HED
3. **Validate sidecars first** before validating full dataset
4. **Use the online tools** at [hedtools.org/hed](https://hedtools.org/hed) for quick checks

### Annotation strategy (BIDS)

1. **Create a single root-level `events.json`** sidecar when possible
2. **Use `#` placeholders** for value columns with continuous data
3. **Skip BIDS-predefined columns** like `onset`, `duration`, `sample`
4. **Use the latest versions of the schemas** later versions have improved linkage
5. **Document your annotations** using descriptions in the sidecar

If you are annotating an NWB dataset, the instructions are somewhat similar but haven't been finalized.

### Code organization

1. **Import from top-level `hed` package**:

   ```python
   # Recommended
   from hed import HedString, Sidecar, load_schema_version

   # Works but not recommended
   from hed.models.hed_string import HedString
   ```

2. **Handle errors gracefully**:

   ```python
   try:
       issues = dataset.validate()
   except Exception as e:
       print(f"Validation failed: {e}")
   ```

## Troubleshooting

```{index} troubleshooting, errors, debugging
```

### Common issues

#### Schema loading errors

**Problem:** Cannot find or load schema

**Solutions:**

- Check internet connection (schemas are downloaded from GitHub)
- Verify the schema version exists at [HED Schemas](https://github.com/hed-standard/hed-schemas)
- Check cache directory: `~/.hedtools/`

```python
# Check cache location
from hed.schema import get_cache_directory
print(get_cache_directory())
```

#### Validation errors

**Problem:** Unexpected validation issues

**Solutions:**

1. Check HED syntax - ensure proper comma separation and parentheses
2. Verify the tag exists in your schema version
3. Validate incrementally - test small pieces first

#### File format issues

**Problem:** Cannot read TSV/CSV/JSON files

**Solutions:**

- Ensure TSV files are **tab-separated** (not spaces or commas)
- Check **character encoding** (UTF-8 is recommended)
- Verify **JSON syntax** in sidecars using a JSON validator
- Check for hidden characters or BOM markers

#### BIDS dataset issues

**Problem:** Files not found or inheritance not working

**Solutions:**

- Ensure BIDS directory structure is correct (`sub-XX/ses-YY/...`)
- Check that `dataset_description.json` exists in dataset root
- Verify file naming follows BIDS conventions
- Exclude non-data directories: `derivatives`, `code`, `stimuli`, `sourcedata`

### Getting help

#### Documentation resources

- **[API reference](api/index.html)**: Detailed function and class documentation
- **[HED specification](https://www.hedtags.org/hed-specification)**: Formal annotation rules
- **[HED resources](https://www.hedtags.org/hed-resources)**: HED tutorials and guides
- **[HED online tools](https://hedtools.org/hed)**: Web-based interface requiring no programming
- **[Example datasets](https://github.com/hed-standard/hed-examples)**: HED-annotated example datasets

#### Support

- **Issues and bugs**: Open an [issue](https://github.com/hed-standard/hed-python/issues) on GitHub
- **Questions and ideas**: Contribute to the [HED organization discussions](https://github.com/orgs/hed-standard/discussions)
- **Online validation**: Try [HED online tools](https://hedtools.org/hed) for web-based access
- **Contact**: Email [hed.maintainers@gmail.com](mailto:hed.maintainers@gmail.com)

#### Before opening an issue

1. Try the [online tools](https://hedtools.org) to isolate the problem
2. Search [existing issues](https://github.com/hed-standard/hed-python/issues)

#### Opening an issue

Include:

- HEDTools version: `pip show hedtools`
- Python version: `python --version`
- Schema version being used
- Minimal code example that reproduces the problem
- Full error traceback
- Expected vs actual behavior
