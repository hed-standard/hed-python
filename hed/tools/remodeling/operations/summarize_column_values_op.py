""" Summarize the values in the columns of a tabular file. """

import operator
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

    Optional remodeling parameters:   
         - **max_categorical** (*int*): Maximum number of unique values to include in summary for a categorical column.   

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
            "values_per_line": int,
            "max_categorical": int
        }
    }

    SUMMARY_TYPE = 'column_values'
    VALUES_PER_LINE = 5
    MAX_CATEGORICAL = 50

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
        self.max_categorical = parameters.get('max_categorical', float('inf'))
        self.values_per_line = parameters.get('values_per_line', self.VALUES_PER_LINE)

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
        self.max_categorical = sum_op.max_categorical
        self.values_per_line = sum_op.values_per_line

    def update_context(self, new_context):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_context (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary information is kept in separate TabularSummary objects for each file.  
            - The summary needs a "name" str and a "df" .  

        """
        name = new_context['name']
        if name not in self.summary_dict:
            self.summary_dict[name] = \
                TabularSummary(value_cols=self.value_columns, skip_cols=self.skip_columns, name=name)
        self.summary_dict[name].update(new_context['df'])

    def get_details_dict(self, summary):
        """ Return a dictionary with the summary contained in a TabularSummary

        Parameters:
            summary (TabularSummary): Dictionary of merged summary information.

        Returns:
            dict: Dictionary with the information suitable for extracting printout.

        """
        return summary.get_summary(as_json=False)

    def merge_all_info(self):
        """ Create a TabularSummary containing the overall dataset summary.

        Returns:
            TabularSummary - the summary object for column values.

        """
        all_sum = TabularSummary(value_cols=self.value_columns, skip_cols=self.skip_columns, name='Dataset')
        for key, counts in self.summary_dict.items():
            all_sum.update_summary(counts)
        return all_sum

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str - The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_dataset_string to get the overall summary string and
            _get_individual_string to get an individual summary string.

        """

        if name == "Dataset":
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(result, indent=indent)

    def _get_categorical_string(self, cat_dict, offset="", indent="   "):
        """ Return  a string with the summary for a particular categorical dictionary.

         Parameters:
             cat_dict (dict): Dictionary of summary information for a particular tabular file.
             offset (str): String of blanks used as offset for every item
             indent (str):  String of blanks used as the additional amount to indent an item's for readability.

         Returns:
             str: Formatted string suitable for saving in a file or printing.

         """
        sum_list = [f"{offset}{indent}Categorical column values[Events, Files]:"]
        sorted_tuples = sorted(cat_dict.items(), key=lambda x: x[0])
        for dict_entry in sorted_tuples:
            sum_list = sum_list + self._get_categorical_col(dict_entry, offset="", indent="   ")
        return "\n".join(sum_list)

    def _get_dataset_string(self, result, indent=BaseContext.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all of the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Total events={result.get('Total events', 0)} "
                    f"Total files={result.get('Total files', 0)}"]
        cat_cols = result.get("Categorical columns", {})
        if cat_cols:
            sum_list.append(self._get_categorical_string(cat_cols, offset="", indent=indent))
        val_cols = result.get("Value columns", {})
        if val_cols:
            sum_list.append(ColumnValueSummaryContext._get_value_string(val_cols, offset="", indent=indent))
        return "\n".join(sum_list)

    def _get_individual_string(self, result, indent=BaseContext.DISPLAY_INDENT):

        """ Return  a string with the summary for an individual tabular file.

        Parameters:
            result (dict): Dictionary of summary information for a particular tabular file.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Total events={result.get('Total events', 0)}"]
        cat_cols = result.get("Categorical columns", {})
        if cat_cols:
            sum_list.append(self._get_categorical_string(cat_cols, offset=indent, indent=indent))
        val_cols = result.get("Value columns", {})
        if val_cols:
            sum_list.append(ColumnValueSummaryContext._get_value_string(val_cols, offset=indent, indent=indent))
        return "\n".join(sum_list)

    def _get_categorical_col(self, dict_entry, offset="", indent="   "):
        """ Return  a string with the summary for a particular categorical column.

         Parameters:
             dict_entry(tuple): (Name of the column, summary dict for that column)
             offset(str): String of blanks used as offset for all items
             indent (str):  String of blanks used as the additional amount to indent for this item's readability.

         Returns:
             list: Formatted strings, each corresponding to a line in the output.
         """

        sorted_tuples = sorted(dict_entry[1], key=lambda x: x[1], reverse=True)
        num_disp = min(self.max_categorical, len(sorted_tuples))
        col_list = [f"{offset}{indent * 2}{dict_entry[0]}: {len(sorted_tuples)} unique values "
                    f"(displaying top {num_disp} values)"]
        # Create and partition the list of individual entries
        value_list = [f"{item[0]}{str(item[1])}" for item in sorted_tuples]
        part_list = ColumnValueSummaryContext.partition_list(value_list, self.values_per_line)
        return col_list + [f"{offset}{indent * 3}{item}" for item in part_list]

    @staticmethod
    def partition_list(lst, n):
        """ Partition a list into lists of n items.

        Parameters:
            lst (list): List to be partitioned
            n (int):  Number of items in each sublist

        Returns:
            list:  list of lists of n elements, the last might have fewer.

        """
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    @staticmethod
    def _get_value_string(val_dict, offset="", indent=""):
        sum_list = [f"{offset}{indent}Value columns[Events, Files]:"]
        for col_name, val_counts in val_dict.items():
            sum_list.append(f"{offset}{indent*2}{col_name}{str(val_counts)}")
        return "\n".join(sum_list)
