# Jupyter Notebooks for BIDS-HED Annotation

This directory contains Jupyter notebooks specifically designed to support HED annotation for BIDS datasets. These notebooks provide interactive workflows for annotation, validation, and analysis.

**📖 For detailed documentation, see the [User Guide - Jupyter Notebooks section](../docs/user_guide.md#jupyter-notebooks-for-bids)**

## Available Notebooks

| Notebook | Purpose |
|----------|---------|
| [extract_json_template.ipynb](extract_json_template.ipynb) | Create JSON sidecar template from all event files in dataset |
| [find_event_combinations.ipynb](find_event_combinations.ipynb) | Extract unique combinations of column values |
| [merge_spreadsheet_into_sidecar.ipynb](merge_spreadsheet_into_sidecar.ipynb) | Merge edited 4-column spreadsheet back into JSON sidecar |
| [sidecar_to_spreadsheet.ipynb](sidecar_to_spreadsheet.ipynb) | Convert JSON sidecar to 4-column spreadsheet for editing |
| [summarize_events.ipynb](summarize_events.ipynb) | Summarize event file contents and value distributions |
| [validate_bids_dataset.ipynb](validate_bids_dataset.ipynb) | Validate HED annotations in a BIDS dataset |
| [validate_bids_dataset_with_libraries.ipynb](validate_bids_dataset_with_libraries.ipynb) | Validate with HED library schemas |
| [validate_bids_datasets.ipynb](validate_bids_datasets.ipynb) | Batch validate multiple BIDS datasets |

## Quick Start

### Prerequisites

- **Python 3.10+** required
- These notebooks are only available in the [GitHub repository](https://github.com/hed-standard/hed-python), not in the PyPI distribution

### Installation Option 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/hed-standard/hed-python.git
cd hed-python/examples

# Install dependencies
pip install hedtools jupyter notebook

# Launch Jupyter
jupyter notebook
```

### Installation Option 2: Download Examples Only

```bash
# Download just the examples directory
svn export https://github.com/hed-standard/hed-python/trunk/examples

cd examples
pip install hedtools jupyter notebook
jupyter notebook
```

## Typical Annotation Workflow

A recommended workflow for annotating a new BIDS dataset:

1. **📊 Summarize events** → Understand your event structure
2. **📝 Extract template** → Create initial JSON sidecar
3. **📋 Convert to spreadsheet** → Easier editing format
4. **✏️ Edit annotations** → Add HED tags in spreadsheet
5. **🔄 Merge back** → Convert spreadsheet to JSON
6. **✅ Validate** → Check for errors, iterate until valid

See the [User Guide](../docs/user_guide.md#typical-annotation-workflow) for detailed steps.

## Notebook Descriptions

### Extract JSON Template
Creates a JSON sidecar template based on all unique values found across all event files in your BIDS dataset.

**Key parameters**: `dataset_path`, `exclude_dirs`, `skip_columns`, `value_columns`

### Find Event Combinations
Extracts all unique combinations of values across specified columns, useful for understanding column relationships or creating recoding mappings.

**Key parameters**: `dataset_path`, `key_columns`, `output_path`

### Merge Spreadsheet into Sidecar
Merges a 4-column spreadsheet (with edited HED annotations) back into a BIDS JSON sidecar file.

**Key parameters**: `spreadsheet_path`, `sidecar_path`, `description_tag`, `output_path`

### Sidecar to Spreadsheet
Converts the HED content of a JSON sidecar into a 4-column spreadsheet for easier viewing and editing.

**Output format**: `column_name | column_value | description | HED`

### Summarize Events
Provides an overview of event file structure, column names, and value distributions across the entire dataset.

**Key parameters**: `dataset_path`, `exclude_dirs`, `skip_columns`, `value_columns`

### Validate BIDS Dataset
Validates all HED annotations in a BIDS dataset against the specified schema.

**Key parameters**: `dataset_path`, `check_for_warnings`

**Note**: This validates HED only, not full BIDS compliance.

### Validate BIDS Dataset with Libraries
Demonstrates validation using multiple schemas (base schema + library schemas like SCORE).

**Use case**: Datasets using specialized vocabularies beyond the base HED schema.

### Validate Multiple Datasets
Convenience notebook for batch validation across multiple BIDS datasets.

## Additional Resources

- **📚 Full Documentation**: [docs/user_guide.md](../docs/user_guide.md)
- **🔧 API Reference**: [docs/api/index.rst](../docs/api/index.rst)
- **🌐 Online Tools**: [hedtools.org](https://hedtools.org) - No programming required
- **📖 HED Specification**: [hed-specification.readthedocs.io](https://hed-specification.readthedocs.io/)
- **🎓 HED Resources**: [hed-resources.org](https://www.hed-resources.org)
- **💬 Get Help**: [GitHub Issues](https://github.com/hed-standard/hed-python/issues)

## Notes

- **BIDS Structure Required**: These notebooks expect standard BIDS directory structure
- **Inheritance Handling**: Automatically processes BIDS sidecar inheritance
- **Exclude Directories**: Always exclude `derivatives`, `code`, `stimuli`, `sourcedata`
- **Skip Columns**: Typically skip `onset`, `duration`, `sample` (BIDS-predefined)
- **Value Columns**: Columns with continuous data (annotated with `#` placeholder)

