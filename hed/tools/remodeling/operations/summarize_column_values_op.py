from hed.tools import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeColumnValuesOp(BaseOp):
    """ Summarize the values that are in the columns.

    Notes: The required parameters are:
        - summary_name (str)   The name of the summary.
        - summary_filename (str)   Base filename of the summary.
        - skip_columns (list)  Names of columns to skip in the summary.
        - value_columns (list) Names of columns to treat as value columns rather than categorical columns

    The purpose of this op is to produce a summary of the values in a tabular file.

    """

    PARAMS = {
        "operation": "summarize_column_values",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "skip_columns": list,
            "value_columns": list,
            "task_names": list,
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = 'column_values'

    def __init__(self, parameters):
        super().__init__(self.PARAMS["operation"], self.PARAMS["required_parameters"],
                         self.PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.skip_columns = parameters['skip_columns']
        self.value_columns = parameters['value_columns']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for context
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = ColumnValueSummary(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': df})
        return df


class ColumnValueSummary(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.summary = TabularSummary(value_cols=sum_op.value_columns, skip_cols=sum_op.skip_columns,
                                      name=sum_op.summary_name)

    def update_context(self, new_context):
        self.summary.update(new_context['df'])

    def get_summary_details(self, verbose=True):
        return self.summary.get_summary(as_json=False)
