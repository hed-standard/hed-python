# Errors

Error handling and exception classes for HED validation and processing.

## Exception Classes

Core exception classes for HED-related errors.

### HedFileError

::: hed.errors.exceptions.HedFileError
    options:
      show_source: false
      heading_level: 4

### HedExceptions

::: hed.errors.exceptions.HedExceptions
    options:
      show_source: false
      heading_level: 4

## Error Reporting

Classes for collecting, managing, and reporting validation errors.

### ErrorHandler

::: hed.errors.error_reporter.ErrorHandler
    options:
      show_source: false
      heading_level: 4

### Error Reporting Functions

::: hed.errors.error_reporter.get_printable_issue_string
    options:
      show_source: false
      heading_level: 4

::: hed.errors.error_reporter.sort_issues
    options:
      show_source: false
      heading_level: 4

::: hed.errors.error_reporter.replace_tag_references
    options:
      show_source: false
      heading_level: 4

### ErrorContext

::: hed.errors.error_types.ErrorContext
    options:
      show_source: false
      heading_level: 4

### ErrorSeverity

::: hed.errors.error_types.ErrorSeverity
    options:
      show_source: false
      heading_level: 4

## Error Types

Specific error categories for different types of validation issues.

### ValidationErrors

::: hed.errors.error_types.ValidationErrors
    options:
      show_source: false
      heading_level: 4

### SchemaErrors

::: hed.errors.error_types.SchemaErrors
    options:
      show_source: false
      heading_level: 4

### SchemaWarnings

::: hed.errors.error_types.SchemaWarnings
    options:
      show_source: false
      heading_level: 4

### SidecarErrors

::: hed.errors.error_types.SidecarErrors
    options:
      show_source: false
      heading_level: 4

### ColumnErrors

::: hed.errors.error_types.ColumnErrors
    options:
      show_source: false
      heading_level: 4

### DefinitionErrors

::: hed.errors.error_types.DefinitionErrors
    options:
      show_source: false
      heading_level: 4

### TemporalErrors

::: hed.errors.error_types.TemporalErrors
    options:
      show_source: false
      heading_level: 4
