# Models

Core data models for working with HED data structures.

## Core Models

The fundamental data structures for HED annotations and tags.

### HedString

::: hed.models.hed_string.HedString
    options:
      show_source: false
      heading_level: 4

### HedTag

::: hed.models.hed_tag.HedTag
    options:
      show_source: false
      heading_level: 4

### HedGroup

::: hed.models.hed_group.HedGroup
    options:
      show_source: false
      heading_level: 4

### DefinitionDict

::: hed.models.definition_dict.DefinitionDict
    options:
      show_source: false
      heading_level: 4

### DefinitionEntry

::: hed.models.definition_entry.DefinitionEntry
    options:
      show_source: false
      heading_level: 4

## Input Models

Classes for handling different types of input data formats.

### BaseInput

::: hed.models.base_input.BaseInput
    options:
      show_source: false
      heading_level: 4

### TabularInput

::: hed.models.tabular_input.TabularInput
    options:
      show_source: false
      heading_level: 4

### SpreadsheetInput

::: hed.models.spreadsheet_input.SpreadsheetInput
    options:
      show_source: false
      heading_level: 4

### TimeseriesInput

::: hed.models.timeseries_input.TimeseriesInput
    options:
      show_source: false
      heading_level: 4

### Sidecar

::: hed.models.sidecar.Sidecar
    options:
      show_source: false
      heading_level: 4

## Query Models

Classes for searching and querying HED data.

### QueryHandler

::: hed.models.query_handler.QueryHandler
    options:
      show_source: false
      heading_level: 4

### Query Service Functions

::: hed.models.query_service.get_query_handlers
    options:
      show_source: false
      heading_level: 4

::: hed.models.query_service.search_hed_objs
    options:
      show_source: false
      heading_level: 4

## Utility Models

Support classes for data management and processing.

### ColumnMapper

::: hed.models.column_mapper.ColumnMapper
    options:
      show_source: false
      heading_level: 4

### ColumnMetadata

::: hed.models.column_metadata.ColumnMetadata
    options:
      show_source: false
      heading_level: 4

### ColumnType

::: hed.models.column_metadata.ColumnType
    options:
      show_source: false
      heading_level: 4

### DataFrame Utilities

::: hed.models.df_util.convert_to_form
    options:
      show_source: false
      heading_level: 4

::: hed.models.df_util.shrink_defs
    options:
      show_source: false
      heading_level: 4

::: hed.models.df_util.expand_defs
    options:
      show_source: false
      heading_level: 4

::: hed.models.df_util.process_def_expands
    options:
      show_source: false
      heading_level: 4
