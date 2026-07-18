---
html_meta:
  description: Complete user guide for Python HEDTools - validation, BIDS integration, analysis, and command-line tools for HED annotations
  keywords: HED tutorial, Python guide, validation examples, BIDS datasets, sidecar files, command-line interface, Jupyter notebooks, HED overview, event descriptors, neuroscience, schema
---

```{index} user guide, tutorial, getting started, HED, Hierarchical Event Descriptors
```

# Python HEDTools guide

HED (Hierarchical Event Descriptors) is a framework for systematically describing events and experimental metadata in machine-actionable form. This guide provides comprehensive documentation for using the HED Python tools for validation, BIDS integration, and analysis.

## Installation

```{index} installation, pip, PyPI
```

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

### From GitHub (latest development version)

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

### Python requirements

- **Python 3.10 or later** is required
- Core dependencies: pandas, numpy, defusedxml, openpyxl
- Jupyter support: Install with `pip install jupyter notebook`

## Basic usage

### A starter example

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

### Loading schemas

```{index} schema; loading, schema; validation, load_schema, load_schema_version
```

A HED schema specifies an allowed HED vocabulary. The official HED schemas are hosted in the [hed-standard/hed-schemas](https://github.com/hed-standard/hed-schemas) GitHub repository. Most HEDTools operations require that you specify which versions of the HED schemas that you are using. You may also specify a file with your own schema for testing and development. The HEDTools assume that the HED schema that you are using has been validated.

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

### Validating HED strings

```{index} validation; HED strings, HedString class, validate method
```

The HED string must be created with a schema, and validation is performed on the string object:

```python
from hed import HedString, load_schema_version


schema = load_schema_version("8.4.0")
hed_string = HedString("Red, Blue, Green", schema)
issues = hed_string.validate()

```

### Validating a BIDS dataset

```{index} BIDS; dataset validation, BidsDataset class, dataset_description.json
```

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

### Validating a tabular file

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

### Using sidecars

```{index} Sidecar class, JSON sidecar, sidecar validation
```

Sidecars are JSON files that are a BIDS mechanism for containing metadata. NWB has an equivalent mechanism.

#### Validating a sidecar

```python
from hed import Sidecar, load_schema_version


schema = load_schema_version("8.4.0")

# Load a JSON sidecar
sidecar = Sidecar("task-rest_events.json")

# Validate the sidecar
issues = sidecar.validate(schema)
```

#### Extracting definitions

```{index} definitions, DefinitionDict, get_def_dict
```

```python
from hed import Sidecar, load_schema_version


schema = load_schema_version("8.4.0")
sidecar = Sidecar("task-rest_events.json")

# Get all definitions from the sidecar
def_dict = sidecar.get_def_dict(schema)
```

#### Saving sidecars

```python
from hed import Sidecar

sidecar = Sidecar("task-rest_events.json")

# Save as formatted JSON file
sidecar.save_as_json("output_sidecar.json")

# Get as a formatted JSON string
json_string = sidecar.get_as_json_string()
```

### Schema validation

```{index} schema validation, check_compliance, SchemaValidator, ComplianceSummary
```

HED schemas can be validated for compliance — checking that attribute domains, ranges, and semantic rules are all satisfied. There are three levels of access depending on how much control you need.

#### Quick check via HedSchema

The simplest approach calls `check_compliance()` directly on a loaded schema. It returns a list of issue dictionaries in the standard HED issue format, so you can use `get_printable_issue_string` just like any other HED validation result:

```python
from hed import load_schema_version
from hed.errors import get_printable_issue_string

schema = load_schema_version("8.4.0")
issues = schema.check_compliance()
if issues:
    print(get_printable_issue_string(issues, title="Schema compliance issues"))
else:
    print("Schema is compliant")
```

Pass `check_for_warnings=False` to suppress formatting warnings and report only errors:

```python
issues = schema.check_compliance(check_for_warnings=False)
```

#### Getting a structured summary

The returned list carries a `compliance_summary` attribute (`ComplianceSummary`) that provides a human-readable report of what was checked:

```python
issues = schema.check_compliance()
print(issues.compliance_summary.get_summary())
```

The summary shows each of the five checks (prerelease version, prologue/epilogue, invalid characters, attributes, and duplicate names) with pass/fail status, entry counts, and sub-check details.

#### Using SchemaValidator directly

For fine-grained control you can instantiate `SchemaValidator` and run individual checks:

```python
from hed.errors.error_reporter import ErrorHandler
from hed.schema.schema_validation.compliance import SchemaValidator

schema = load_schema_version("8.4.0")
error_handler = ErrorHandler(check_for_warnings=True)
sv = SchemaValidator(schema, error_handler)

# Run only the checks you need
issues = sv.check_attributes()
issues += sv.check_invalid_characters()
```

The five available checks are:

| Method                          | What it validates                                        |
| ------------------------------- | -------------------------------------------------------- |
| `check_if_prerelease_version()` | Warns if the version is newer than all known releases    |
| `check_prologue_epilogue()`     | Validates characters in prologue and epilogue text       |
| `check_invalid_characters()`    | Validates entry names and descriptions for illegal chars |
| `check_attributes()`            | Domain, range, and semantic validation of all attributes |
| `check_duplicate_names()`       | Detects duplicate entry names within or across libraries |

Each method returns a list of issue dictionaries and updates `sv.summary` (a `ComplianceSummary` instance) with what was checked.

## Schema caching

```{index} schema caching, cache directory, offline use, GitHub rate limits, HED_GITHUB_TOKEN
```

The official HED schemas live in the [hed-standard/hed-schemas](https://github.com/hed-standard/hed-schemas) GitHub repository. HEDTools caches schema data locally so that repeated validation runs — and repeated program starts — don't re-download the same content from GitHub every time. This section explains what gets cached, where, and how to control it.

### The cache directory

By default, schemas are cached in `~/.hedtools/hed_cache/`. You can check or change this location:

```python
from hed.schema import get_cache_directory, set_cache_directory

# Check the current cache location
print(get_cache_directory())

# Use a custom location instead (e.g. a writable path in a container image)
set_cache_directory("/data/hed_cache")
```

A few common schema versions also ship *inside* the hedtools package itself (the "installed cache"), so a fresh install can validate against those versions with no network access at all, before anything has been downloaded.

### How `load_schema_version()` uses the cache

```{index} load_schema_version; caching
```

When you call `load_schema_version("8.4.0")`, HEDTools looks for that version in the local cache first (including its `prerelease/` subfolder). If it's not there, it downloads just that one version's XML content from GitHub and stores it in the cache directory — a one-time cost per version, per machine:

```python
from hed.schema import load_schema_version

schema = load_schema_version("8.4.0")   # downloaded and cached on first use
schema = load_schema_version("8.4.0")   # reused from disk on every call after that
```

Nothing here is fetched again once a version is cached, since released schemas are immutable — the same version number never changes content.

### Listing available versions without downloading

```{index} get_available_hed_versions, get_hed_versions, version picker
```

There are two different functions for listing versions, and it's easy to reach for the wrong one:

| Function                       | Where it looks                            | Network calls                             |
| ------------------------------ | ----------------------------------------- | ----------------------------------------- |
| `get_hed_versions()`           | Local cache only (installed + downloaded) | None                                      |
| `get_available_hed_versions()` | GitHub, live                              | Small listing requests, no schema content |

`get_available_hed_versions()` is the right choice for something like a version-picker dropdown — it tells you everything currently published on GitHub without downloading any of it:

```python
from hed.schema import get_available_hed_versions, load_schema_version

# Standard schema versions only, newest first
versions = get_available_hed_versions()
# ['8.4.0', '8.3.0', '8.2.0', ...]

# Everything: standard schema plus every library, keyed by library name
# (the standard schema is under the None key)
all_versions = get_available_hed_versions(library_name="all")
# {None: ['8.4.0', ...], 'score': ['2.1.0', '1.0.0'], 'lang': ['1.1.0']}

# Include prerelease (in-development) versions
versions_with_prerelease = get_available_hed_versions(check_prerelease=True)

# Once the user picks one, load it — this is the step that actually downloads content
schema = load_schema_version(versions[0])
```

If GitHub can't be reached (offline, rate-limited, etc.), `get_available_hed_versions()` returns an empty list or dict rather than raising, so it's safe to call from a user-facing listing without wrapping it in a try/except.

### How repeated calls stay cheap

```{index} caching; rate limits, ETag, ETag-conditional
```

`get_available_hed_versions()` is designed to be called often — e.g. every time a web page loads — without adding up to a lot of GitHub traffic.

For the standard hed-schemas repository it reads a single repository-level manifest (`schema_versions.json`) from GitHub's raw/CDN host in one request. That host is *not* subject to GitHub's REST API rate limit, so this stays cheap even for an unauthenticated, frequently-polling caller. If that manifest can't be read — for example when you point the function at a custom or forked URL set, or the fetch fails — it falls back to crawling the REST API directory listings, backed by its own small on-disk cache (separate from the downloaded schema content) checked in two increasingly cheap tiers before making a real request:

1. **Recently checked** — if a given piece of information was checked within the last `cache_time_threshold` seconds (60 by default), it's reused with no network call at all.
2. **Confirmed unchanged** — otherwise, a conditional request is made using a stored ETag. If GitHub confirms nothing changed (a 304 response), the previous result is reused.

For most uses the defaults are fine. To force an immediate, confirmed-fresh answer (e.g. right after publishing a release):

```python
get_available_hed_versions(force_refresh=True)
```

### Authenticating with GitHub

```{index} GITHUB_TOKEN, HED_GITHUB_TOKEN, authentication, rate limits
```

GitHub's API allows 60 requests per hour per IP address for unauthenticated callers, versus 5,000 per hour for authenticated ones. Authentication also makes conditional (ETag) requests free of charge against that limit — for unauthenticated callers, even a confirmed-unchanged response still counts against the 60/hour budget.

If your use of HEDTools makes frequent GitHub calls — a web service checking for new versions, a CI pipeline, a container that restarts often — set a GitHub personal access token (no special scopes needed; it only needs to read a public repository) as an environment variable:

```bash
export HED_GITHUB_TOKEN=ghp_your_token_here
# GITHUB_TOKEN is also recognized (checked second), which many CI systems set automatically
```

HEDTools picks this up automatically; no code changes are needed.

### Working offline / pre-populating the cache

```{index} cache_xml_versions, offline, pre-populating cache
```

To prepare an environment that won't have network access later (an offline workstation, a Docker image built once and deployed many times), pre-download everything with `cache_xml_versions()`:

```python
from hed.schema import cache_xml_versions, set_cache_directory

set_cache_directory("/opt/hed_cache")   # optional: a specific location to ship or mount
cache_xml_versions()                    # downloads every discovered version's full content
```

This is a much heavier operation than `get_available_hed_versions()` — it downloads every version it finds, not just a listing — so it's meant to be run once (e.g. during image build or setup), not on a request-handling hot path. It's throttled independently (won't re-run within 30 minutes of its last successful run in the same cache folder) to avoid accidental repeated use.

### Clearing the cache

There's no dedicated CLI command for this; the cache is just a regular directory, so you can remove it directly and it will be rebuilt automatically the next time it's needed:

```python
import shutil
from hed.schema import get_cache_directory

shutil.rmtree(get_cache_directory(), ignore_errors=True)
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

See the [Schema caching](#schema-caching) chapter for more on how the cache works, working offline, and avoiding GitHub rate limits.

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
