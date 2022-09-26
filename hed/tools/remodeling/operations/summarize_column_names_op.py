from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


PARAMS = {
    "command": "summarize_column_headers",
    "required_parameters": {
        "summary_name": str,
        "summary_filename": str
    },
    "optional_parameters": {
    }
}


class SummarizeColumnNamesOp(BaseOp):
    """ Summarize the column headers in a dataset.

    Notes: The required parameters are:
        - summary_name (str)       The name of the summary.
        - summary_filename (str)   Base filename of the summary.

    The purpose of this is to check that all of the dataframes have the same columns in same order.

    """

    def __init__(self, parameters):
        super().__init__(PARAMS["command"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.summary_type = 'column_headers'
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
        position = summary.update_context(list(df.columns))
        if name not in summary.file_dict:
            summary.file_dict[name] = position
        elif name in summary.file_dict and position != summary.file_dict[name]:
            raise ValueError("FileHasChangedColumnNames",
                             f"{name} in the summary has conflicting column names " +
                             f"Current: {str(list(df.columns))} " +
                             f"Previous: {str(summary.unique_headers[summary.file_dict[name]])}")
        return df


class ColumnNameSummary(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.summary_type, sum_op.summary_name, sum_op.summary_filename)
        self.file_dict = {}
        self.unique_headers = []

    def update_context(self, column_names):
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
            column_headers[index] = {'column_header': self.unique_headers[index], 'file_list': patterns[index]}
        summary = {'number_unique_column_headers': len(self.unique_headers),
                   'number_files': len(self.file_dict), 'column_patterns': column_headers}
        return summary

    # def get_text_summary(self, title='', verbose=True):
    #     sum_str = super().get_text_summary(title=title, verbose=verbose)
    #     summary = self.get_summary(as_json=False)
    #
    #     sum_str = sum_str + '\n'.join([f"Number unique column headers: {summary['number_unique_column_headers']}",
    #                                    f"Column headers:"])
    #
    #     sum_details = [0]*len(summary['column_headers'])
    #     for index, header in summary['column_headers'].items():
    #         header_str = f"\t{str(header['column_header'])} has {len(header['file_list'])} files"
    #         file_str = ''
    #         if verbose:
    #             files = [f"\t\t{a_file}" for a_file in header['file_list']]
    #             file_str = '\n' + ('\n').join(files)
    #         sum_details[index] = header_str + file_str
    #     return '\n'.join(sum_str) + '\n' + '\n'.join(sum_details)
