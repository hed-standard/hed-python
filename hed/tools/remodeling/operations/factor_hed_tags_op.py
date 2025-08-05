""" Append columns of factors based on column values to a columnar file. """


import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.models.sidecar import Sidecar
from hed.models import query_service
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_tag_manager import HedTagManager
from hed.tools.util.data_util import replace_na


class FactorHedTagsOp(BaseOp):
    """ Append columns of factors based on column values to a columnar file.

    Required remodeling parameters:
        - **queries** (*list*): Queries to be applied successively as filters.

    Optional remodeling parameters:
        - **expand_context** (*bool*): Expand the context if True.
        - **query_names** (*list*):  Column names for the query factors.
        - **remove_types** (*list*):  Structural HED tags to be removed (such as Condition-variable or Task).
        - **expand_context** (*bool*): If true, expand the context based on Onset, Offset, and Duration.

    Notes:
        - If query names are not provided, *query1*, *query2*, ... are used.
        - If query names are provided, the list must have same list as the number of queries.
        - When the context is expanded, the effect of events for temporal extent is accounted for.

    """
    NAME = "factor_hed_tags"

    PARAMS = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "description": "List of HED tag queries to compute one-hot factors for.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "query_names": {
                "type": "array",
                "description": "Optional column names for the queries.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "remove_types": {
                "type": "array",
                "descriptions": "List of type tags to remove from before querying (e.g., Condition-variable, Task).",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "expand_context": {
                "type": "boolean",
                "description": "If true, the assembled HED tags include the effects of temporal extent (e.g., Onset)."
            },
            "replace_defs": {
                "type": "boolean",
                "description": "If true, Def tags are replaced with definition contents."
            }
        },
        "required": [
            "queries"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the factor HED tags operation.

        Parameters:
            parameters (dict):  Actual values of the parameters for the operation.

        """
        super().__init__(parameters)
        self.queries = parameters['queries']
        self.remove_types = parameters.get('remove_types', [])
        self.expand_context = parameters.get('expand_context', True)
        self.replace_defs = parameters.get('replace_defs', True)
        self.query_handlers, self.query_names, issues = \
            query_service.get_query_handlers(self.queries, parameters.get('query_names', None))
        if issues:
            raise ValueError("FactorHedTagInvalidQueries", "\n".join(issues))

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Create factor columns based on HED tag queries.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            DataFrame: A new dataframe after processing.

        Raises:
            ValueError: If a name for a new query factor column is already a column.

        """

        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(sidecar)
        input_data = TabularInput(df.copy().fillna('n/a'), sidecar=sidecar, name=name)
        column_names = list(df.columns)
        for query_name in self.query_names:
            if query_name in column_names:
                raise ValueError("QueryNameAlreadyColumn",
                                 f"Query [{query_name}]: is already a column name of the data frame")
        df_list = [input_data.dataframe]
        tag_man = HedTagManager(EventManager(input_data, dispatcher.hed_schema), remove_types=self.remove_types)
        hed_objs = tag_man.get_hed_objs(include_context=self.expand_context, replace_defs=self.replace_defs)
        df_factors = query_service.search_hed_objs(hed_objs, self.query_handlers, query_names=self.query_names)
        if len(df_factors.columns) > 0:
            df_list.append(df_factors)
        df_new = pd.concat(df_list, axis=1)
        replace_na(df_new)
        return df_new

    @staticmethod
    def validate_input_data(parameters) -> list:
        """ Parse and valid the queries and return issues in parsing queries, if any.

        Parameters:
            parameters (dict):  Dictionary representing the actual operation values.

        Returns:
            list:  List of issues in parsing queries.

        """
        queries, names, issues = query_service.get_query_handlers(parameters.get("queries", []),
                                                                  parameters.get("query_names", None))
        return issues
