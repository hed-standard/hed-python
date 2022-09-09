import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.models.expression_parser import TagExpressionParser
from hed.tools.analysis.analysis_util import get_assembled_strings

PARAMS = {
    "command": "factor_hed_tags",
    "required_parameters": {
        "filters": list,
        "queries": list,
        "query_names": list,
        "remove_types": list,
    },
    "optional_parameters": {}
}

ALLOWED_FILTERS = ['expand_defs', 'collapse_defs', 'expand_onsets', 'remove_onsets']


class FilterHedOp(BaseOp):
    """ Create factors based on tag queries.

        Notes: The required parameters are:
             - filters (list)          List of filters to apply prior to queries.
             - queries (list)          Queries to be applied successively as filters.
             - query_names (list)      List of names to use as columns for the queries.
             - remove_types (list)     Structural HED tags to be removed (usually *Condition-variable* and *Task*).

    """

    def __init__(self, parameters):
        super().__init__(PARAMS["command"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.filters = parameters['filters']
        self.queries = parameters['queries']
        self.query_names = parameters['query_names']
        self.remove_types = parameters['remove_types']
        if self.query_names and len(self.queries) != len(self.query_names):
            raise ValueError("QueryNamesLenBad",
                             f"The query_names length {len(self.query_names)} must be empty or equal" +
                             f"to the queries length {len(self.queries)} .")
        elif not self.query_names:
            self.query_names = [f"query_{index}" for index in range(len(self.queries))]
        self.expression_parsers = []
        for index, query in enumerate(self.queries):
            try:
                next_query = TagExpressionParser(query)
            except Exception:
                raise ValueError("BadQuery", f"Query [{index}]: {query} cannot be parsed")
            self.expression_parsers.append(next_query)

    def do_op(self, dispatcher, df, name, sidecar=None, verbose=False):
        """ Factor the column using HED tag queries

        Args:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.
            verbose (bool) If True output informative messages during operation.

        Returns:
            Dataframe - a new dataframe after processing.

        """

        input_data = TabularInput(df, hed_schema=dispatcher.hed_schema, sidecar=sidecar)
        hed_strings = get_assembled_strings(input_data, hed_schema=dispatcher.hed_schema, expand_defs=False)
        df_factors = pd.DataFrame(0, index=range(len(hed_strings)), columns=self.query_names)
        for parse_ind, parser in enumerate(self.expression_parsers):
            df_factors[self.query_names[parse_ind]] = self.get_query_factor(hed_strings, parser)

        return df_factors

    @staticmethod
    def get_query_factor(hed_strings, parser):
        query_results = [0]*len(hed_strings)
        for index, next_item in enumerate(hed_strings):
            match = parser.search_hed_string(next_item)
            if match:
                query_results[index] = 1
        return query_results
