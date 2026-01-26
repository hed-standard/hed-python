# Jupyter notebooks for annotation

```{index} Jupyter notebooks, annotation workflows, examples
```

This directory contains Jupyter notebooks that provide interactive workflows for annotation, validation, and analysis.

**📖 For detailed documentation, see the [Jupyter notebooks section](../docs/user_guide.md#jupyter-notebooks)**

## Available Notebooks

```{index} notebooks list, extract template, validate dataset, sidecar conversion
```

| Notebook                                                                                 | Purpose                                                      |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [extract_json_template.ipynb](extract_json_template.ipynb)                               | Create JSON sidecar template from all event files in dataset |
| [find_event_combinations.ipynb](find_event_combinations.ipynb)                           | Extract unique combinations of column values                 |
| [merge_spreadsheet_into_sidecar.ipynb](merge_spreadsheet_into_sidecar.ipynb)             | Merge edited 4-column spreadsheet back into JSON sidecar     |
| [sidecar_to_spreadsheet.ipynb](sidecar_to_spreadsheet.ipynb)                             | Convert JSON sidecar to 4-column spreadsheet for editing     |
| [summarize_events.ipynb](summarize_events.ipynb)                                         | Summarize event file contents and value distributions        |
| [validate_bids_dataset.ipynb](validate_bids_dataset.ipynb)                               | Validate HED annotations in a BIDS dataset                   |
| [validate_bids_dataset_with_libraries.ipynb](validate_bids_dataset_with_libraries.ipynb) | Validate with HED library schemas                            |
| [validate_bids_datasets.ipynb](validate_bids_datasets.ipynb)                             | Batch validate multiple BIDS datasets                        |

## Quick Start

```{index} quick start; notebooks, installation; notebooks
```

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

```{index} annotation workflow, BIDS annotation, workflow steps
```

A recommended workflow for annotating a new BIDS dataset:

1. **📊 Summarize events** → Understand your event structure
2. **📝 Extract template** → Create initial JSON sidecar
3. **📋 Convert to spreadsheet** → Easier editing format
4. **✏️ Edit annotations** → Add HED tags in spreadsheet
5. **🔄 Merge back** → Convert spreadsheet to JSON
6. **✅ Validate** → Check for errors, iterate until valid

## Notebook descriptions

```{index} notebook descriptions, templates, validation, spreadsheet conversion
```

### Extract JSON template

```{index} extract template, JSON template, sidecar template
```

Creates a JSON sidecar template based on all unique values found across all event files in your BIDS dataset.

**Key parameters**: `dataset_path`, `exclude_dirs`, `skip_columns`, `value_columns`

### Find event combinations

```{index} event combinations, column relationships
```

Extracts all unique combinations of values across specified columns, useful for understanding column relationships or creating recoding mappings.

**Key parameters**: `dataset_path`, `key_columns`, `output_path`

### Merge spreadsheet into sidecar

```{index} merge spreadsheet, spreadsheet to JSON, annotation merging
```

Merges a 4-column spreadsheet (with edited HED annotations) back into a BIDS JSON sidecar file (which could be empty).

**Key parameters**: `spreadsheet_path`, `sidecar_path`, `description_tag`, `output_path`

### Sidecar to Spreadsheet

```{index} sidecar to spreadsheet, JSON to spreadsheet, 4-column format
```

Converts the HED content of a JSON sidecar into a 4-column spreadsheet for easier viewing and editing.

**Output format**: `column_name | column_value | description | HED`

### Summarize events

```{index} summarize events, event analysis, value distributions
```

Provides an overview of event file structure, column names, and value distributions across the entire dataset.

**Key parameters**: `dataset_path`, `exclude_dirs`, `skip_columns`, `value_columns`

### Validate BIDS dataset

```{index} validate BIDS, dataset validation, HED validation
```

Validates all HED annotations in a BIDS dataset against the specified schema.

**Key parameters**: `dataset_path`, `check_for_warnings`

**Note**: This validates HED only, not full BIDS compliance.

### Validate BIDS dataset with libraries

Demonstrates validation using multiple schemas (base schema + library schemas like SCORE).

**Use case**: Datasets using specialized vocabularies beyond the base HED schema.

### Validate multiple datasets

Convenience notebook for batch validation across multiple BIDS datasets.

## Additional resources

- **📚 Full documentation**: [docs/user_guide.md](../docs/user_guide.md)
- **🔧 API reference**: [docs/api/index.rst](../docs/api/index.rst)
- **🌐 Online tools**: [hedtools.org/hed](https://hedtools.org/hed) - No programming required
- **📖 HED specification**: [www.hedtags.org/hed-specification](https://www.hedtags.org/hed-specification)
- **🎓 HED resources**: [www.hedtags.org/hed-resources](https://www.hedtags.org/hed-resources)
- **💬 Get help**: GitHub [issues](https://github.com/hed-standard/hed-python/issues)

## Notes

- **BIDS structure required**: These notebooks expect standard BIDS directory structure
- **Inheritance handling**: Automatically processes BIDS sidecar inheritance
- **Exclude directories**: Always exclude `derivatives`, `code`, `stimuli`, `sourcedata`
- **Skip columns**: Typically skip `onset`, `duration`, `sample` (BIDS-predefined)
- **Value columns**: Columns with continuous data (annotated with `#` placeholder)
