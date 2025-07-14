# HED Python Tools

![HED Logo](assets/images/croppedWideLogo.png){ width="220" }

Welcome to the Hierarchical Event Descriptor (HED) Python Tools documentation. This library provides comprehensive tools for working with HED schemas and annotations.

## What is HED?

HED (Hierarchical Event Descriptor) is a system for describing events in machine-actionable form. HED tags are comma-separated path strings that describe what happened, when it happened, and other relevant properties.

## Quick Start

Install HED Python tools:

```bash
pip install hedtools
```

Basic usage:

```python
from hed import HedString, load_schema

# Load a HED schema
schema = load_schema()

# Create and validate a HED string
hed_string = HedString("Sensory-event, Visual-presentation")
issues = hed_string.validate(schema)
```

## Features

- **Schema Management**: Load, validate, and work with HED schemas
- **String Validation**: Validate HED annotation strings
- **BIDS Integration**: Tools for working with BIDS datasets
- **Spreadsheet Support**: Import/export HED annotations from spreadsheets
- **Sidecar Processing**: Handle BIDS sidecar files

## Navigation

- **[Introduction](introduction.md)**: Learn about HED concepts and terminology
- **[User Guide](user_guide.md)**: Step-by-step tutorials and examples
- **[API Reference](api/index.md)**: Complete API documentation

## Links

- [Source Code](https://github.com/hed-standard/hed-python)
- [HED Standard](https://www.hedtags.org/)
- [BIDS](https://bids.neuroimaging.io/)

## Support

For questions and support, please visit our [GitHub repository](https://github.com/hed-standard/hed-python/issues).
