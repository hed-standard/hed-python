""" Create tabular file factors from tag queries. """


import pandas as pd
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.models.expression_parser import TagExpressionParser
from hed.tools.analysis.analysis_util import get_assembled_strings


class FactorHedTagsOp(BaseOp):
    """ Create tabular file factors from tag queries.

    The required parameters are:
        - queries (list):       Queries to be applied successively as filters.
        - query_names (list):   List of names to use as columns for the queries (otherwise use query1,.._.
        - remove_types (list):  Structural HED tags to be removed (usually *Condition-variable* and *Task*).
        - expand_context bool): Expand the context if True.

    Raises:
        - ValueError:
            - If the list of query_names is not empty or the same length as queries.
            - If the query_names list contains duplicate names.
            - If a query is invalid and cannot be parsed.

    """

    PARAMS = {
        "operation": "factor_hed_tags",
        "required_parameters": {
            "queries": list,
            "query_names": list,
            "remove_types": list,
            "expand_context": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        """ Constructor for the factor HED tags operation.

        Parameters:
            op_spec (dict): Specification for required and optional parameters.
            parameters (dict):  Actual values of the parameters for the operation.

        Raises:
            - KeyError:
                - if a required parameter is missing.
                - If an unexpected parameter is provided.

            - TypeError:
                - If a parameter has the wrong type.

            - ValueError:
                - If the specification is missing a valid operation.
                - If the length of query names is not empty and not same length as queries.
                - If there are duplicate query names.

        """
        super().__init__(self.PARAMS, parameters)
        self.queries = parameters['queries']
        self.query_names = parameters['query_names']
        self.remove_types = parameters['remove_types']
        if not self.query_names:
            self.query_names = [f"query_{index}" for index in range(len(self.queries))]
        elif len(self.queries) != len(self.query_names):
            raise ValueError("QueryNamesLengthBad",
                             f"The query_names length {len(self.query_names)} must be empty or equal" +
                             f"to the queries length {len(self.queries)} .")
        elif len(set(self.query_names)) != len(self.query_names):
            raise ValueError("DuplicateQueryNames",  f"The query names {str(self.query_names)} list has duplicates")
        self.expression_parsers = []
        for index, query in enumerate(self.queries):
            try:
                next_query = TagExpressionParser(query)
            except Exception:
                raise ValueError("BadQuery", f"Query [{index}]: {query} cannot be parsed")
            self.expression_parsers.append(next_query)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Factor the column using HED tag queries.

        Parameters:
            dispatcher (Dispatcher) - dispatcher object for managing the operations.
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Raises:
            - ValueError:
                - If a name for a new query factor column is already a column.

        Returns:
            Dataframe: A new dataframe after processing.

        """

        input_data = TabularInput(df, hed_schema=dispatcher.hed_schema, sidecar=sidecar)
        column_names = list(df.columns)
        for name in self.query_names:
            if name in column_names:
                raise ValueError("QueryNameAlreadyColumn",
                                 f"Query [{name}]: is already a column name of the data frame")
        df = input_data.dataframe.copy()
        df_list = [df]
        hed_strings = get_assembled_strings(input_data, hed_schema=dispatcher.hed_schema, expand_defs=True)
        df_factors = pd.DataFrame(0, index=range(len(hed_strings)), columns=self.query_names)
        for parse_ind, parser in enumerate(self.expression_parsers):
            for index, next_item in enumerate(hed_strings):
                match = parser.search_hed_string(next_item)
                if match:
                    df_factors.at[index, self.query_names[parse_ind]] = 1
        if len(df_factors.columns) > 0:
            df_list.append(df_factors)
        df_new = pd.concat(df_list, axis=1)
        df_new.replace('n/a', np.NaN, inplace=True)
        return df_new

    #     hed_strings = get_assembled_strings(input_data, hed_schema=dispatcher.hed_schema, expand_defs=False)
    #
    #     definitions = input_data.get_definitions()
    #     var_manager = HedTypeManager(hed_strings, dispatcher.hed_schema, definitions)
    #     var_manager.add_type_variable(self.type_tag.lower())
    #
    #     df_factors = var_manager.get_factor_vectors(self.type_tag, [], factor_encoding="one-hot")
    #     if len(df_factors.columns) > 0:
    #         df_list.append(df_factors)
    #     df_new = pd.concat(df_list, axis=1)
    #     df_new.replace('n/a', np.NaN, inplace=True)
    #     return df_new
