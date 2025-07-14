# API Reference

This section provides comprehensive documentation for all HED Python tools modules and classes.

## Core Modules

### [Models](models.md)
Core data models for working with HED data:

- **HedString**: Represents and validates HED annotation strings
- **HedTag**: Individual HED tag manipulation
- **HedGroup**: Grouped HED annotations
- **Sidecar**: BIDS sidecar file handling
- **TabularInput**: Spreadsheet and tabular data processing

### [Schema](schema.md)
HED schema management and validation:

- **HedSchema**: Main schema class for loading and querying schemas
- **HedSchemaIO**: Schema input/output operations
- **SchemaComparer**: Compare different schema versions

### [Validator](validator.md)
Validation tools and error handling:

- **HedValidator**: Main validation engine
- **ErrorReporter**: Error collection and reporting
- **ValidationContext**: Validation state management

### [Tools](tools.md)
Utility tools and scripts:

- **BidsTabularSummary**: BIDS dataset analysis
- **ReorderColumns**: Spreadsheet manipulation
- **TagCompareUtil**: Tag comparison utilities

### [Errors](errors.md)
Error handling and exception classes:

- **HedFileError**: File-related errors
- **HedExceptions**: General HED exceptions
- **ErrorMessages**: Error message definitions

## Quick Reference

### Loading and Using Schemas

::: hed.load_schema
    options:
      show_source: true

### Basic Validation

::: hed.HedString
    options:
      show_source: true
      members:
        - __init__
        - validate
        - remove_definitions

### Working with BIDS Data

::: hed.models.Sidecar
    options:
      show_source: true
      members:
        - __init__
        - validate
        - extract_definitions
