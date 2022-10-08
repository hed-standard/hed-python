from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


PARAMS = {
    "operation": "summarize_column_names",
    "required_parameters": {
        "summary_name": str,
        "summary_filename": str
    },
    "optional_parameters": {
    }
}


class SummarizeColumnNamesOp(BaseOp):
    """ Summarize the column names in a dataset.

    Notes: The required parameters are:
        - summary_name (str)       The name of the summary.
        - summary_filename (str)   Base filename of the summary.

    The purpose of this is to check that all of the dataframes have the same columns in same order.

    """

    def __init__(self, parameters):
        super().__init__(PARAMS["operation"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.summary_type = 'column_names'
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Returns:
            DataFrame - a new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = ColumnNameSummary(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({"name": name, "column_names": list(df.columns)})
        return df


class ColumnNameSummary(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.summary_type, sum_op.summary_name, sum_op.summary_filename)
        self.file_dict = {}
        self.unique_headers = []

    def update_context(self, new_context):
        columns = new_context["column_names"]
        name = new_context["name"]
        position = self._update_headers(columns)
        if name not in self.file_dict:
            self.file_dict[name] = position
        elif name in self.file_dict and position != self.file_dict[name]:
            raise ValueError("FileHasChangedColumnNames",
                             f"{name} in the summary has conflicting column names " +
                             f"Current: {str(columns)} Previous: {str(self.unique_headers[self.file_dict[name]])}")

    def _update_headers(self, column_names):
        for index, item in enumerate(self.unique_headers):
            if item == column_names:
                return index
        self.unique_headers.append(column_names)
        return len(self.unique_headers) - 1

    def get_summary_details(self, verbose=True):
        patterns = [list() for element in self.unique_headers]
        for key, value in self.file_dict.items():
            patterns[value].append(key)
        column_headers = {}
        for index, pattern in enumerate(patterns):
            column_headers[index] = {'column_names': self.unique_headers[index], 'file_list': patterns[index]}
        summary = {'unique_patterns': len(self.unique_headers),
                   'files': len(self.file_dict), 'patterns': column_headers}
        return summary
