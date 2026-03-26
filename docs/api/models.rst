Models
======

Core data models for working with HED data structures.

Core models
-----------

The fundamental data structures for HED annotations and tags.

HedString
~~~~~~~~~

.. autoclass:: hed.models.hed_string.HedString
   :members:
   :undoc-members:
   :show-inheritance:

HedTag
~~~~~~

.. autoclass:: hed.models.hed_tag.HedTag
   :members:
   :undoc-members:
   :show-inheritance:

HedGroup
~~~~~~~~

.. autoclass:: hed.models.hed_group.HedGroup
   :members:
   :undoc-members:
   :show-inheritance:

DefinitionDict
~~~~~~~~~~~~~~

.. autoclass:: hed.models.definition_dict.DefinitionDict
   :members:
   :undoc-members:
   :show-inheritance:

DefinitionEntry
~~~~~~~~~~~~~~~

.. autoclass:: hed.models.definition_entry.DefinitionEntry
   :members:
   :undoc-members:
   :show-inheritance:

DefExpandGatherer
~~~~~~~~~~~~~~~~~

.. autoclass:: hed.models.def_expand_gather.DefExpandGatherer
   :members:
   :undoc-members:
   :show-inheritance:

Constants
---------

Enumerations and named constants used across the models layer.

DefTagNames
~~~~~~~~~~~

.. autoclass:: hed.models.model_constants.DefTagNames
   :members:
   :undoc-members:
   :show-inheritance:

TopTagReturnType
~~~~~~~~~~~~~~~~

.. autoclass:: hed.models.model_constants.TopTagReturnType
   :members:
   :undoc-members:
   :show-inheritance:

Input models
------------

Models for handling different types of input data.

BaseInput
~~~~~~~~~

.. autoclass:: hed.models.base_input.BaseInput
   :members:
   :undoc-members:
   :show-inheritance:

Sidecar
~~~~~~~

.. autoclass:: hed.models.sidecar.Sidecar
   :members:
   :undoc-members:
   :show-inheritance:

TabularInput
~~~~~~~~~~~~

.. autoclass:: hed.models.tabular_input.TabularInput
   :members:
   :undoc-members:
   :show-inheritance:

SpreadsheetInput
~~~~~~~~~~~~~~~~

.. autoclass:: hed.models.spreadsheet_input.SpreadsheetInput
   :members:
   :undoc-members:
   :show-inheritance:

TimeseriesInput
~~~~~~~~~~~~~~~

.. autoclass:: hed.models.timeseries_input.TimeseriesInput
   :members:
   :undoc-members:
   :show-inheritance:

ColumnMapper
~~~~~~~~~~~~

.. autoclass:: hed.models.column_mapper.ColumnMapper
   :members:
   :undoc-members:
   :show-inheritance:

ColumnMetadata
~~~~~~~~~~~~~~

.. autoclass:: hed.models.column_metadata.ColumnMetadata
   :members:
   :undoc-members:
   :show-inheritance:

ColumnType
~~~~~~~~~~

.. autoclass:: hed.models.column_metadata.ColumnType
   :members:
   :undoc-members:
   :show-inheritance:

Query models
------------

Classes and functions for searching and querying HED annotations.

QueryHandler
~~~~~~~~~~~~

.. autoclass:: hed.models.query_handler.QueryHandler
   :members:
   :undoc-members:
   :show-inheritance:

SearchResult
~~~~~~~~~~~~

.. autoclass:: hed.models.query_util.SearchResult
   :members:
   :undoc-members:
   :show-inheritance:

get_query_handlers
~~~~~~~~~~~~~~~~~~

.. autofunction:: hed.models.query_service.get_query_handlers

search_hed_objs
~~~~~~~~~~~~~~~

.. autofunction:: hed.models.query_service.search_hed_objs

DataFrame utilities
-------------------

Functions for transforming HED strings within pandas DataFrames.

convert_to_form
~~~~~~~~~~~~~~~

.. autofunction:: hed.models.df_util.convert_to_form

expand_defs
~~~~~~~~~~~

.. autofunction:: hed.models.df_util.expand_defs

shrink_defs
~~~~~~~~~~~

.. autofunction:: hed.models.df_util.shrink_defs

process_def_expands
~~~~~~~~~~~~~~~~~~~

.. autofunction:: hed.models.df_util.process_def_expands

sort_dataframe_by_onsets
~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: hed.models.df_util.sort_dataframe_by_onsets

filter_series_by_onset
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: hed.models.df_util.filter_series_by_onset

split_delay_tags
~~~~~~~~~~~~~~~~

.. autofunction:: hed.models.df_util.split_delay_tags
