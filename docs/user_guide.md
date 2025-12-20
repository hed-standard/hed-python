# User guide for hedtools

This guide provides step-by-step instructions for using the HED Python tools for validation, BIDS integration, and analysis.

## Quick links

- 📚 [API Reference](api/index.html)
- 📓 [Jupyter notebook examples](https://github.com/hed-standard/hed-python/tree/main/examples)
- 🐛 [GitHub issues](https://github.com/hed-standard/hed-python/issues)
- 📖 [HED Specification](https://www.hedtags.org/)
- 🌐 [Online Tools](https://hedtools.org/hed)

## Table of contents

1. [Getting started](#getting-started)
2. [Working with HED schemas](#working-with-hed-schemas)
3. [Validating HED strings](#validating-hed-strings)
4. [Working with BIDS datasets](#working-with-bids-datasets)
5. [Working with sidecars](#working-with-sidecars)
6. [Jupyter notebooks for BIDS](#jupyter-notebooks-for-bids)
7. [Command-line tools](#command-line-tools)
8. [Best practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Getting started

### Installation

Install HEDTools from PyPI:

```bash
pip install hedtools
```

For the latest development version from GitHub:

```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

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

### Loading schemas

```python
from hed import load_schema, load_schema_version


# Load a specific version (auto-cached in ~/.hedtools/)
schema = load_schema_version("8.4.0")

# Load from a local file
schema = load_schema("path/to/schema.xml")

# Load from URL
schema = load_schema("https://example.com/schema.xml")
```

**Note:** Schemas are automatically downloaded and cached in `~/.hedtools/` for offline use.

### Working with library schemas

HED supports library schemas that extend the base vocabulary. Starting with HED 8.3.0, library schemas are typically "partnered" with a specific standard schema version.

```python
from hed import load_schema_version

# Load base schema with a library
schema = load_schema_version("score_2.1.0")

# For multiple libraries
schema = load_schema_version(["score_2.1.0", "lang_1.1.0"])

```

Note: It is now standard for a library schema to be partnered with a standard schema. In general, you should not use an earlier, non-partnered versions of a library schema.

## Validating HED strings

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
from hed import HedString, load_schema_version

schema = load_schema_version("8.4.0")

hed_strings = [
    "Sensory-event, Visual-presentation",
    "Invalid-tag, Another-invalid",
    "(Red, Square)"
]

for i, hed_str in enumerate(hed_strings, 1):
    hed_string = HedString(hed_str, schema)
    issues = hed_string.validate()
    if issues:
        print(f"String {i} has {len(issues)} issues")
```

## Working with BIDS datasets

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

### Working with individual event files

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

### Loading and validating sidecars

```python
from hed import Sidecar, load_schema_version

schema = load_schema_version("8.4.0")

# Load a JSON sidecar
sidecar = Sidecar("task-rest_events.json")

# Validate the sidecar
issues = sidecar.validate(schema)

# Get the definition dictionary from the sidecar
def_dict = sidecar.get_def_dict(schema)
```

### Extracting definitions

```python
from hed import Sidecar, load_schema_version

schema = load_schema_version("8.4.0")
sidecar = Sidecar("task-rest_events.json")

# Extract all definitions from the sidecar
def_dict = sidecar.extract_definitions(schema)
```

### Saving sidecars

```python
from hed import Sidecar

sidecar = Sidecar("task-rest_events.json")

# Save as JSON file
sidecar.save_as_json("output_sidecar.json")

# Get as JSON string
json_string = sidecar.get_as_json_string()
```

## Jupyter notebooks for BIDS

The `examples/` directory in the [GitHub repository](https://github.com/hed-standard/hed-python/tree/main/examples) contains Jupyter notebooks for BIDS annotation workflows. These notebooks are **not included in the PyPI package**.

### Available notebooks

| Notebook                                                                                                                                               | Purpose                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| [extract_json_template.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/extract_json_template.ipynb)                               | Create JSON sidecar template from all event files     |
| [find_event_combinations.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/find_event_combinations.ipynb)                           | Extract unique combinations of column values          |
| [merge_spreadsheet_into_sidecar.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/merge_spreadsheet_into_sidecar.ipynb)             | Merge edited spreadsheet back into JSON sidecar       |
| [sidecar_to_spreadsheet.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/sidecar_to_spreadsheet.ipynb)                             | Convert JSON sidecar to spreadsheet for editing       |
| [summarize_events.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/summarize_events.ipynb)                                         | Summarize event file contents and value distributions |
| [validate_bids_dataset.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_dataset.ipynb)                               | Validate HED annotations in a BIDS dataset            |
| [validate_bids_dataset_with_libraries.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_dataset_with_libraries.ipynb) | Validate with HED library schemas                     |
| [validate_bids_datasets.ipynb](https://github.com/hed-standard/hed-python/blob/main/examples/validate_bids_datasets.ipynb)                             | Batch validate multiple BIDS datasets                 |

### Getting the notebooks

**Option 1: Clone the repository**

```bash
git clone https://github.com/hed-standard/hed-python.git
cd hed-python
pip install -r requirements.txt
pip install jupyter notebook
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
3. **Convert to spreadsheet** (optional) - Convert to spreadsheet format for easier editing
4. **Edit annotations** - Add HED tags to your sidecar or spreadsheet
5. **Merge back** (if using spreadsheet) - Convert spreadsheet back to JSON
6. **Validate** - Check for errors and iterate until valid

See the [examples README](https://github.com/hed-standard/hed-python/tree/main/examples) for detailed documentation of each notebook.

## Command-line tools

HEDTools provides a unified command-line interface (CLI) using a **git-style command structure**. The main command is `hedpy`, which provides subcommands for validation and schema management.

### Available commands

| Command                        | Description                                                 |
| ------------------------------ | ----------------------------------------------------------- |
| `hedpy validate-bids`          | Validate HED annotations in BIDS datasets                   |
| `hedpy extract-sidecar`        | Extract JSON sidecar template from BIDS event files         |
| **Schema Management**          |                                                             |
| `hedpy schema validate`        | Validate HED schema files                                   |
| `hedpy schema convert`         | Convert schemas between formats (XML, MEDIAWIKI, TSV, JSON) |
| `hedpy schema add-ids`         | Add unique HED IDs to schema terms                          |
| `hedpy schema create-ontology` | Generate OWL ontology files from HED schemas                |

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
hedpy validate-bids --help

# Help for command groups
hedpy schema --help
```

Get version information:

```bash
hedpy --version
```

______________________________________________________________________

### BIDS validation

Validate HED annotations in BIDS datasets using `hedpy validate-bids`.

#### Basic validation

```bash
# Validate a BIDS dataset
hedpy validate-bids /path/to/bids/dataset

# Include warnings in addition to errors
hedpy validate-bids /path/to/bids/dataset -w

# Enable verbose output
hedpy validate-bids /path/to/bids/dataset -v
```

#### Output options

```bash
# Save results to a file
hedpy validate-bids /path/to/bids/dataset -o validation_results.txt

# Output in JSON format
hedpy validate-bids /path/to/bids/dataset -f json -o results.json

# Pretty-printed JSON
hedpy validate-bids /path/to/bids/dataset -f json_pp -o results.json

# Print to stdout AND save to file
hedpy validate-bids /path/to/bids/dataset -o results.txt -p
```

#### Filtering validation

```bash
# Validate specific file types (default: events, participants)
hedpy validate-bids /path/to/bids/dataset -s events -s participants -s sessions

# Exclude certain directories (default: sourcedata, derivatives, code, stimuli)
hedpy validate-bids /path/to/bids/dataset -x derivatives -x sourcedata -x mydata

# Limit number of errors reported per error type
hedpy validate-bids /path/to/bids/dataset -ec 5

# Apply error limit per file instead of overall
hedpy validate-bids /path/to/bids/dataset -ec 5 -ef
```

#### Logging options

```bash
# Set log level
hedpy validate-bids /path/to/bids/dataset -l DEBUG

# Save logs to file
hedpy validate-bids /path/to/bids/dataset -lf validation.log

# Save logs to file without stderr output
hedpy validate-bids /path/to/bids/dataset -lf validation.log -lq
```

#### Complete example

```bash
# Comprehensive validation with all options
hedpy validate-bids /path/to/bids/dataset \
  -w \
  -v \
  -f json_pp \
  -o validation_results.json \
  -s events \
  -x derivatives \
  -ec 10 \
  -lf validation.log
```

______________________________________________________________________

### Sidecar template extraction

Extract a JSON sidecar template from BIDS event files using `hedpy extract-sidecar`.

#### Basic extraction

```bash
# Extract template for events files
hedpy extract-sidecar /path/to/bids/dataset -s events

# Save to specific file
hedpy extract-sidecar /path/to/bids/dataset -s events -o task_events.json
```

#### Column handling

```bash
# Specify value columns (columns with unique values needing # placeholders)
hedpy extract-sidecar /path/to/bids/dataset -s events \
  -vc response_time -vc accuracy -vc subject_id

# Skip specific columns (default: onset, duration, sample)
hedpy extract-sidecar /path/to/bids/dataset -s events \
  -sc onset -sc duration -sc trial_type

# Exclude certain directories
hedpy extract-sidecar /path/to/bids/dataset -s events \
  -x derivatives -x pilot_data
```

#### Complete example

```bash
# Extract events template with custom column handling
hedpy extract-sidecar /path/to/bids/dataset \
  -s events \
  -vc response_time \
  -vc reaction_time \
  -sc onset -sc duration \
  -o events_template.json \
  -v
```

______________________________________________________________________

### Schema management

The `hedpy schema` command group provides tools for validating, converting, and managing HED schemas.

#### Schema validation

Validate HED schema files:

```bash
# Validate a single schema
hedpy schema validate /path/to/schema.xml

# Validate multiple schemas
hedpy schema validate schema1.xml schema2.xml schema3.xml

# Validate with verbose output
hedpy schema validate /path/to/schema.xml -v

# Verify all format versions are equivalent
hedpy schema validate /path/to/schema.xml --add-all-extensions
```

#### Schema format conversion

Convert schemas between formats (XML, MEDIAWIKI, TSV, JSON):

```bash
# Convert schema (format auto-detected from extension)
hedpy schema convert schema.xml  # Creates schema.mediawiki, schema.tsv, etc.

# Convert multiple schemas
hedpy schema convert schema1.xml schema2.xml

# Convert and set/update HED IDs
hedpy schema convert schema.xml --set-ids
```

**Supported formats:**

- `.xml` - XML format (standard)
- `.mediawiki` - MEDIAWIKI format
- `.tsv` - TSV (tab-separated value) format
- `.json` - JSON format

#### Add HED IDs to schema

Add unique HED IDs to schema terms:

```bash
# Add IDs to a standard schema
hedpy schema add-ids /path/to/hed-schemas standard 8.4.0

# Add IDs to a library schema
hedpy schema add-ids /path/to/hed-schemas score 2.1.0
```

**Requirements:**

- Path must be to a hed-schemas repository clone
- Schema name and version must match directory structure
- Modifies the schema in-place

#### Create ontology from schema

Generate OWL ontology files from HED schemas:

```bash
# Create ontology for a schema
hedpy schema create-ontology /path/to/hed-schemas standard 8.4.0

# Specify output directory
hedpy schema create-ontology /path/to/hed-schemas standard 8.4.0 \
  --dest /path/to/output

# Create ontology for library schema
hedpy schema create-ontology /path/to/hed-schemas score 2.1.0 \
  --dest ./ontologies
```

______________________________________________________________________

### Legacy script access

For backward compatibility, you can still access scripts directly using Python module syntax:

```bash
# Validation
python -m hed.scripts.validate_bids /path/to/dataset --check-warnings

# Sidecar extraction
python -m hed.scripts.hed_extract_bids_sidecar /path/to/dataset -s events

# Schema validation
python -m hed.scripts.validate_schemas schema.xml
```

**However, the `hedpy` CLI is the recommended interface** as it provides a more consistent and discoverable command structure.

______________________________________________________________________

### Common workflows

#### Workflow 1: First-time BIDS dataset validation

```bash
# Step 1: Extract sidecar template
hedpy extract-sidecar /path/to/dataset -s events -o events.json

# Step 2: Edit events.json to add HED tags
# (manual editing step)

# Step 3: Validate with warnings
hedpy validate-bids /path/to/dataset -w -v -o validation.txt

# Step 4: Fix issues and re-validate
hedpy validate-bids /path/to/dataset -w
```

#### Workflow 2: Schema development and testing

```bash
# Step 1: Validate schema
hedpy schema validate my_schema.xml -v

# Step 2: Convert to all formats
hedpy schema convert my_schema.xml

# Step 3: Verify all formats are equivalent
hedpy schema validate my_schema.xml --add-all-extensions

# Step 4: Add HED IDs
hedpy schema add-ids /path/to/hed-schemas my_library 1.0.0

# Step 5: Generate ontology
hedpy schema create-ontology /path/to/hed-schemas my_library 1.0.0
```

______________________________________________________________________

### Tips and best practices

1. **Use verbose mode (`-v`)** during development to see detailed progress
2. **Save output to files (`-o`)** for documentation and tracking
3. **Use JSON output format (`-f json_pp`)** for programmatic processing
4. **Leverage tab completion** in your shell for command discovery
5. **Use `--help` liberally** to explore options for each command
6. **Test on small datasets first** before processing large corpora

### Getting help

Each command provides detailed help:

```bash
# Top-level help
hedpy --help

# Command-specific help
hedpy validate-bids --help
hedpy schema validate --help

# Command group help
hedpy schema --help
```

## Best practices

### Schema management

1. **Always use specific schema versions** for reproducibility:

   ```python
   # Good: Explicit version
   schema = load_schema_version("8.4.0")

   # Avoid: Unspecified version may change over time
   schema = load_schema()  # Loads latest, which changes
   ```

2. **Cache schemas** - Load once and reuse:

   ```python
   schema = load_schema_version("8.4.0")  # Cached automatically

   for file in event_files:
       tabular = TabularInput(file, sidecar=sidecar)
       issues = tabular.validate(schema)  # Reuses cached schema
   ```

3. **Don't modify schemas** - they're immutable and shared

### Validation workflow

1. **Validate early and often** during annotation development
2. **Fix errors before warnings** - errors indicate invalid HED
3. **Validate sidecars first** before validating full dataset
4. **Use the online tools** at [hedtools.org](https://hedtools.org) for quick checks

### BIDS annotation strategy

1. **Create a single root-level `events.json`** sidecar when possible
2. **Use `#` placeholders** for value columns with continuous data
3. **Skip BIDS-predefined columns** like `onset`, `duration`, `sample`
4. **Document your annotations** using descriptions in the sidecar

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
3. HED tags are case-sensitive - check capitalization
4. Validate incrementally - test small pieces first

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

#### Before opening an issue

1. Check the [HED Specification](https://www.hedtags.org/)
2. Try the [online tools](https://hedtools.org) to isolate the problem
3. Search [existing issues](https://github.com/hed-standard/hed-python/issues)

#### Opening an issue

Include:

- HEDTools version: `pip show hedtools`
- Python version: `python --version`
- Schema version being used
- Minimal code example that reproduces the problem
- Full error traceback
- Expected vs actual behavior

#### Additional resources

- **HED Specification**: [www.hedtags.org](https://www.hedtags.org/)
- **HED Resources**: [www.hed-resources.org](https://www.hed-resources.org)
- **HED Online Tools**: [hedtools.org](https://hedtools.org)
- **GitHub Discussions**: [hed-python discussions](https://github.com/hed-standard/hed-python/discussions)
- **Example Datasets**: [hed-examples](https://github.com/hed-standard/hed-examples)
