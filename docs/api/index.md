# API Reference

This section provides comprehensive documentation for all HED Python tools modules and classes.

## Core Modules

### [Models](models.md)
Core data models for working with HED data:

- **Core Models**: HedString, HedTag, HedGroup, DefinitionDict, DefinitionEntry
- **Input Models**: BaseInput, TabularInput, SpreadsheetInput, TimeseriesInput, Sidecar
- **Query Models**: QueryHandler and query service functions
- **Utility Models**: ColumnMapper, ColumnMetadata, DataFrame utilities

### [Schema](schema.md)
HED schema management and validation:

- **Core Schema**: HedSchema, HedSchemaEntry, HedSchemaGroup, HedSchemaSection
- **Schema I/O**: Schema loading, caching, and file operations
- **Schema Utilities**: Comparison tools, validation utilities, compliance checking

### [Validator](validator.md)
Validation tools and error handling:

- **Core Validators**: HedValidator, SidecarValidator
- **Specialized Validators**: Definition validator, onset validator, spreadsheet validator

### [Tools](tools.md)
Utility tools and data transformation operations:

- **Analysis Tools**: TabularSummary, annotation utilities, tag counting
- **Remodeling Operations**: Comprehensive set of data transformation operations
- **Remodeling Utilities**: Remodeler, backup manager, dispatcher

### [Errors](errors.md)
Error handling and exception classes:

- **Exception Classes**: HedFileError, HedExceptions
- **Error Reporting**: ErrorHandler, ErrorReporter, validation context
- **Error Messages**: Comprehensive error message definitions

## Quick Reference

### Loading Schemas

::: hed.load_schema
    options:
      show_source: false
      heading_level: 3

::: hed.load_schema_version
    options:
      show_source: false
      heading_level: 3

### Working with HED Strings

::: hed.HedString
    options:
      show_source: false
      heading_level: 3
      members: []
