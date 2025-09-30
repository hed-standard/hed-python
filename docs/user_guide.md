# HED Python Tools - User Guide

This comprehensive guide provides step-by-step instructions for using HED Python tools in various scenarios, from basic validation to advanced analysis workflows.

## Quick Links

- 📚 [API Reference](api/index.md)
- 🐛 [GitHub Issues](https://github.com/hed-standard/hed-python/issues)
- 📖 [HED Specification](https://hed-specification.readthedocs.io/)
- 🌐 [Online Tools](https://hedtools.org)

## Table of Contents

1. [Getting Started](#getting-started)
2. [Working with HED Schemas](#working-with-hed-schemas)
3. [Validating HED Strings](#validating-hed-strings)
4. [Working with BIDS Datasets](#working-with-bids-datasets)
5. [Spreadsheet Integration](#spreadsheet-integration)
6. [Advanced Usage](#advanced-usage)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

Install HEDTools from PyPI:
```bash
pip install hedtools
```

For the latest development version from GitHub:
```bash
pip install git+https://github.com/hed-standard/hed-python/@main
```

### Basic Example

Here's a simple example to get you started with HED validation:

```python
from hed import HedString, load_schema

# Load the latest HED schema
schema = load_schema()

# Create a HED string
hed_string = HedString("Sensory-event, Visual-presentation, (Onset, (Red, Square))")

# Validate the string
issues = hed_string.validate(schema)
if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✓ HED string is valid!")
```

## Working with HED Schemas

### Loading Schemas

```python
from hed import load_schema

# Load the latest official schema
schema = load_schema()

# Load a specific version
schema = load_schema(version="8.2.0")

# Load from a local file
schema = load_schema("path/to/schema.xml")

# Load from URL
schema = load_schema("https://example.com/schema.xml")
```

### Schema Information

```python
# Get schema version
print(f"Schema version: {schema.version}")

# Get all tags
all_tags = schema.get_all_tags()

# Check if a tag exists
exists = schema.check_compliance("Sensory-event")

# Get tag attributes
attributes = schema.get_tag_attributes("Sensory-event")
```

## Validating HED Strings

### Basic Validation

```python
from hed import HedString

hed_string = HedString("Red, Blue, Green")
issues = hed_string.validate(schema)

# Check for specific types of errors
syntax_issues = [issue for issue in issues if issue.code == 'SYNTAX_ERROR']
```

### Batch Validation

```python
hed_strings = [
    "Sensory-event, Visual-presentation",
    "Invalid-tag, Another-invalid",
    "Onset, (Red, Square)"
]

for i, hed_str in enumerate(hed_strings):
    hed_string = HedString(hed_str)
    issues = hed_string.validate(schema)
    if issues:
        print(f"String {i+1} has {len(issues)} issues")
```

## Working with BIDS Datasets

### Validating BIDS Events

```python
from hed.models import TabularInput
import pandas as pd

# Load events file
events_df = pd.read_csv("sub-01_task-rest_events.tsv", sep='\t')

# Create tabular input
tabular = TabularInput(events_df, name="events")

# Validate HED annotations
issues = tabular.validate(schema)
```

### Sidecar Processing

```python
from hed.models import Sidecar

# Load and validate sidecar
sidecar = Sidecar("task-rest_events.json")
issues = sidecar.validate(schema)

# Extract HED strings
hed_dict = sidecar.extract_definitions(schema)
```

## Spreadsheet Integration

### Reading from Excel/CSV

```python
from hed.models import SpreadsheetInput

# Load spreadsheet
spreadsheet = SpreadsheetInput("data.xlsx", worksheet_name="Sheet1")

# Validate HED columns
issues = spreadsheet.validate(schema, hed_columns=[2, 3])
```

### Processing Multiple Files

```python
import os
from pathlib import Path

data_dir = Path("data/")
for file_path in data_dir.glob("*.xlsx"):
    spreadsheet = SpreadsheetInput(str(file_path))
    issues = spreadsheet.validate(schema)
    if issues:
        print(f"Issues in {file_path.name}: {len(issues)}")
```

## Advanced Usage

### Custom Validation

```python
from hed.validator import HedValidator

validator = HedValidator(schema)

# Custom validation rules
def custom_validation(hed_string):
    # Your custom logic here
    return []

# Apply custom validation
issues = custom_validation(hed_string)
```

### Schema Manipulation

```python
# Compare schemas
from hed.schema import schema_comparer

differences = schema_comparer.compare_schemas(old_schema, new_schema)

# Merge schemas
merged_schema = old_schema.merge_with(extension_schema)
```

### Error Handling

```python
from hed.errors import HedFileError, ErrorHandler

try:
    schema = load_schema("invalid_path.xml")
except HedFileError as e:
    print(f"Error loading schema: {e}")

# Custom error handling
error_handler = ErrorHandler()
error_handler.add_context("Processing file: data.xlsx")
```

## Best Practices

1. **Always validate your HED strings** before using them in analysis
2. **Use the latest schema version** unless you have specific requirements
3. **Handle errors gracefully** in production code
4. **Cache schemas** when processing multiple files
5. **Use batch processing** for large datasets

## Troubleshooting

### Common Issues

- **Schema not found**: Ensure you have internet connection for downloading schemas
- **Validation errors**: Check HED syntax and schema compliance
- **File format issues**: Ensure your files are properly formatted TSV/CSV/JSON

### Getting Help

- Check the [API Reference](api/index.md) for detailed function documentation
- Visit our [GitHub Issues](https://github.com/hed-standard/hed-python/issues) page
- Consult the [HED specification](https://hed-specification.readthedocs.io/)
