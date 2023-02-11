"""  Summarize the column names in a collection of tabular files. """

from hed.tools.analysis.column_name_summary import ColumnNameSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeColumnNamesOp(BaseOp):
    """  Summarize the column names in a collection of tabular files.

    Required remodeling parameters:   
        - **summary_name** (*str*)       The name of the summary.   
        - **summary_filename** (*str*)   Base filename of the summary.   

    The purpose is to check that all of the tabular files have the same columns in same order.

    """

    PARAMS = {
        "operation": "summarize_column_names",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = "column_names"

    def __init__(self, parameters):
        """ Constructor for summarize column names operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        Raises:
            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.   

            TypeError   
                - If a parameter has the wrong type.   

        """
        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):   Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context.

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = ColumnNameSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({"name": name, "column_names": list(df.columns)})
        return df


class ColumnNameSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)

    def update_context(self, new_context):
        name = new_context['name']
        if name not in self.summary_dict:
            self.summary_dict[name] = ColumnNameSummary(name=name)
        self.summary_dict[name].update(name, new_context["column_names"])

    def _get_summary_details(self, column_summary):
        return column_summary.get_summary()

    def _merge_all(self):
        all_sum = ColumnNameSummary(name='Dataset')
        for key, counts in self.summary_dict.items():
            for name, pos in counts.file_dict.items():
                all_sum.update(name, counts.unique_headers[pos])
        return all_sum

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        if name == "Dataset":
            return self._get_dataset_string(result, indent)
        columns = result["Columns"][0]
        return f"{indent}{str(columns['Column names'])}"

    @staticmethod
    def _get_dataset_string(result, indent=BaseContext.DISPLAY_INDENT):
        sum_list = [f"Dataset: Number of files={result.get('Number files', 0)}"]
        for element in result.get("Columns", []):
            sum_list.append(f"{indent}Columns: {str(element['Column names'])}")
            for file in element.get("Files", []):
                sum_list.append(f"{indent}{indent}{file}")
        return "\n".join(sum_list)
