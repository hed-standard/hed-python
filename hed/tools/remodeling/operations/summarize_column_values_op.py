""" Summarize the values in the columns of a tabular file. """

from hed.tools import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeColumnValuesOp(BaseOp):
    """ Summarize the values in the columns of a tabular file.

    Required remodeling parameters:   
        - **summary_name** (*str*): The name of the summary.   
        - **summary_filename** (*str*): Base filename of the summary.   
        - **skip_columns** (*list*):  Names of columns to skip in the summary.   
        - **value_columns** (*list*): Names of columns to treat as value columns rather than categorical columns.   

    The purpose is to produce a summary of the values in a tabular file.

    """

    PARAMS = {
        "operation": "summarize_column_values",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "skip_columns": list,
            "value_columns": list
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = 'column_values'

    def __init__(self, parameters):
        """ Constructor for the summarize column values operation.

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
        self.skip_columns = parameters['skip_columns']
        self.value_columns = parameters['value_columns']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context.

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = ColumnValueSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name})
        return df


class ColumnValueSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.value_columns = sum_op.value_columns
        self.skip_columns = sum_op.skip_columns

    def update_context(self, new_context):
        name = new_context['name']
        if name not in self.summary_dict:
            self.summary_dict[name] = \
                TabularSummary(value_cols=self.value_columns, skip_cols=self.skip_columns, name=name)
        self.summary_dict[name].update(new_context['df'])

    def _get_summary_details(self, summary):
        return summary.get_summary(as_json=False)

    def _merge_all(self):
        all_sum = TabularSummary(value_cols=self.value_columns, skip_cols=self.skip_columns, name='Dataset')
        for key, counts in self.summary_dict.items():
            all_sum.update_summary(counts)
        return all_sum

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        if name == "Dataset":
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(name, result, indent=indent)

    @staticmethod
    def _get_dataset_string(result, indent=BaseContext.DISPLAY_INDENT):
        sum_list = [f"Dataset: Total events={result.get('Total events', 0)} "
                    f"Total files={result.get('Total files', 0)}"]
        cat_cols = result.get("Categorical columns", {})
        if cat_cols:
            sum_list.append(ColumnValueSummaryContext._get_categorical_string(cat_cols, offset="", indent=indent))
        val_cols = result.get("Value columns", {})
        if val_cols:
            sum_list.append(ColumnValueSummaryContext._get_value_string(val_cols, offset="", indent=indent))
        return "\n".join(sum_list)

    @staticmethod
    def _get_individual_string(name, result, indent=BaseContext.DISPLAY_INDENT):
        sum_list = [f"Total events={result.get('Total events', 0)}"]
        cat_cols = result.get("Categorical columns", {})
        if cat_cols:
            sum_list.append(ColumnValueSummaryContext._get_categorical_string(cat_cols, offset=indent, indent=indent))
        val_cols = result.get("Value columns", {})
        if val_cols:
            sum_list.append(ColumnValueSummaryContext._get_value_string(val_cols, offset=indent, indent=indent))
        return "\n".join(sum_list)

    @staticmethod
    def _get_categorical_string(cat_dict, offset="", indent="   "):
        sum_list = [f"{offset}{indent}Categorical column values[Events, Files]:"]
        for col_name, col_dict in cat_dict.items():
            sum_list.append(f"{offset}{indent*2}{col_name}:")
            col_list = []
            for col_value, val_counts in col_dict.items():
                col_list.append(f"{col_value}{str(val_counts)}")
            sum_list.append(f"{offset}{indent*3}{' '.join(col_list)}")
        return "\n".join(sum_list)

    @staticmethod
    def _get_value_string(val_dict, offset="", indent=""):
        sum_list = [f"{offset}{indent}Value columns[Events, Files]:"]
        for col_name, val_counts in val_dict.items():
            sum_list.append(f"{offset}{indent*2}{col_name}{str(val_counts)}")
        return "\n".join(sum_list)
