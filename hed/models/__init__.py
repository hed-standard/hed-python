"""HED data models: strings, tags, groups, inputs, queries, and definitions.

This module provides the core data structures used to represent, validate, and
transform HED-annotated data.  A loaded :class:`~hed.schema.HedSchema` (from
``hed.schema``) is typically passed in when constructing these objects.

Typical usage
-------------
Parse and validate a raw HED string::

    from hed.schema import load_schema_version
    from hed.models import HedString

    schema = load_schema_version("8.3.0")
    hs = HedString("Sensory-event, (Action, Move/Flexion)", schema)
    issues = hs.validate(schema)

Load a BIDS events file with a sidecar::

    from hed.models import TabularInput, Sidecar

    sidecar = Sidecar("task-rest_events.json", name="MySidecar")
    events  = TabularInput("sub-01_task-rest_events.tsv", sidecar=sidecar)
    issues  = events.validate(schema)

Search HED annotations with a query::

    from hed.models import QueryHandler

    query   = QueryHandler("Sensory-event && Action")
    matches = query.search(hs)

Key exports
-----------
- :class:`HedString` — a parsed HED annotation string (root of the parse tree).
- :class:`HedTag` — a single HED tag with schema linkage and canonical form.
- :class:`HedGroup` — a parenthesised group of tags and nested groups.
- :class:`TabularInput` — a BIDS-style TSV events file with optional sidecar.
- :class:`Sidecar` — a BIDS JSON sidecar mapping column values to HED strings.
- :class:`SpreadsheetInput` — an Excel / TSV spreadsheet with HED columns.
- :class:`TimeseriesInput` — a continuous time-series file with HED annotations.
- :class:`DefinitionDict` — a collection of resolved HED Def/Def-expand definitions.
- :class:`QueryHandler` — compile and execute queries against HED strings.
- :func:`get_query_handlers` / :func:`search_hed_objs` — convenience helpers for
  batch querying.
- :func:`convert_to_form`, :func:`shrink_defs`, :func:`expand_defs`,
  :func:`process_def_expands` — DataFrame-level HED transformation utilities.
"""

from .base_input import BaseInput
from .column_metadata import ColumnMetadata, ColumnType
from .definition_dict import DefinitionDict
from .model_constants import DefTagNames, TopTagReturnType
from .query_handler import QueryHandler
from .query_service import get_query_handlers, search_hed_objs
from .hed_group import HedGroup
from .spreadsheet_input import SpreadsheetInput
from .hed_string import HedString
from .hed_tag import HedTag
from .sidecar import Sidecar
from .tabular_input import TabularInput
from .timeseries_input import TimeseriesInput
from .df_util import convert_to_form, shrink_defs, expand_defs, process_def_expands
