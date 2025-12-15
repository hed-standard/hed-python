### Jupyter notebooks to demo HED processing with BIDS

The Jupyter notebooks in this directory are useful for annotating,
validating, summarizing, and analyzing your BIDS datasets.

**Table 1:** Useful Jupyter notebooks for processing BIDS datasets.

| Notebooks                                                                                                                                                              | Purpose                                                                 | 
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------| 
| [`extract_json_template`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/extract_json_template.ipynb)                               | Creates a JSON sidecar based on all the event files in a dataset.       |
| [`find_event_combinations`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/find_event_combinations.ipynb)                           | Creates a spreadsheet of unique combinations of event values.           |
| [`merge_spreadsheet_into_sidecar`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/merge_spreadsheet_into_sidecar.ipynb)             | Merges a spreadsheet version of a sidecar into a JSON sidecar.          |
| [`sidecar_to_spreadsheet`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/sidecar_to_spreadsheet.ipynb)                             | Converts the HED portion of a JSON sidecar into a 4-column spreadsheet. |
| [`summarize_events`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/summarize_events.ipynb)                                         | Summarizes the contents of the event files, including value counts.     |  
| [`validate_bids_dataset`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/validate_bids_dataset.ipynb)                               | Validates the HED annotations in a BIDS dataset.                        |
| [`validate_bids_dataset_with_libraries`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/validate_bids_dataset_with_libraries.ipynb) | Demonstrates use of HED libraries in validation.                        |  
| [`validate_bids_datasets`](https://github.com/hed-standard/hed-examples/blob/main/src/jupyter_notebooks/bids/validate_bids_datasets.ipynb)                             | Validates the HED annotations in a list of BIDS datasets.               |  

## Getting Started

**Note:** These example notebooks are only available in the [GitHub repository](https://github.com/hed-standard/hed-python),
not in the PyPI distribution. To use them, clone or download the repository.

### Installation

1. **Clone the repository** (to get the example notebooks):
   ```bash
   git clone https://github.com/hed-standard/hed-python.git
   cd hed-python/examples
   ```

2. **Install HEDTools with Jupyter support**:
   
   From PyPI:
   ```bash
   pip install hedtools jupyter notebook
   ```
   
   Or from the repository root in development mode:
   ```bash
   cd ..
   pip install -e .[examples]
   ```

3. **Launch Jupyter** and open the notebooks:
   ```bash
   jupyter notebook
   ```

### Alternative: Download examples separately

If you already have `hedtools` installed from PyPI, you can download just the examples:

```bash
# Download the examples directory from GitHub
svn export https://github.com/hed-standard/hed-python/trunk/examples

# Or manually download from:
# https://github.com/hed-standard/hed-python/tree/main/examples
```

### Requirements

- Python 3.10 or greater
- HEDTools package
- Jupyter notebook environment

