""" Summarize the values in the columns of a tabular file. """

from hed.tools import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


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
            "append_timecode": bool,
            "max_categorical": int,
            "values_per_line": int
        }
    }

    SUMMARY_TYPE = 'column_values'
    VALUES_PER_LINE = 5
    MAX_CATEGORICAL = 50

    def __init__(self, parameters):
        """ Constructor for the summarize column values operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        :raises KeyError:
            - If a required parameter is missing.
            - If an unexpected parameter is provided.

        :raises TypeError:
            - If a parameter has the wrong type.

        """

        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.skip_columns = parameters['skip_columns']
        self.value_columns = parameters['value_columns']
        self.append_timecode = parameters.get('append_timecode', False)
        self.max_categorical = parameters.get('max_categorical', float('inf'))
        self.values_per_line = parameters.get('values_per_line', self.VALUES_PER_LINE)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create a summary of the column values in df.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            DataFrame: A copy of df.

        Side-effect:
            Updates the relevant summary.

        """
       
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = ColumnValueSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name})
        return df_new


class ColumnValueSummary(BaseSummary):

    def __init__(self, sum_op):
        super().__init__(sum_op)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary information is kept in separate TabularSummary objects for each file.  
            - The summary needs a "name" str and a "df" .  

        """
        name = new_info['name']
        if name not in self.summary_dict:
            self.summary_dict[name] = \
                TabularSummary(value_cols=self.op.value_columns, skip_cols=self.op.skip_columns, name=name)
        self.summary_dict[name].update(new_info['df'])

    def get_details_dict(self, summary):
        """ Return a dictionary with the summary contained in a TabularSummary

        Parameters:
            summary (TabularSummary): Dictionary of merged summary information.

        Returns:
            dict: Dictionary with the information suitable for extracting printout.

        """
        this_summary = summary.get_summary(as_json=False)
        unique_counts = [(key, len(count_dict)) for key, count_dict in this_summary['Categorical columns'].items()]
        this_summary['Categorical counts'] = dict(unique_counts)
        for key, dict_entry in this_summary['Categorical columns'].items():
            num_disp, sorted_tuples = ColumnValueSummary.sort_dict(dict_entry, reverse=True)
            this_summary['Categorical columns'][key] = dict(sorted_tuples[:min(num_disp, self.op.max_categorical)])
        return this_summary

    def merge_all_info(self):
        """ Create a TabularSummary containing the overall dataset summary.

        Returns:
            TabularSummary - the summary object for column values.

        """
        all_sum = TabularSummary(value_cols=self.op.value_columns, skip_cols=self.op.skip_columns, name='Dataset')
        for key, counts in self.summary_dict.items():
            all_sum.update_summary(counts)
        return all_sum

    def _get_result_string(self, name, result, indent=BaseSummary.DISPLAY_INDENT):
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

    def _get_categorical_string(self, result, offset="", indent="   "):
        """ Return  a string with the summary for a particular categorical dictionary.

         Parameters:
             result (dict): Dictionary of summary information for a particular tabular file.
             offset (str): String of blanks used as offset for every item
             indent (str):  String of blanks used as the additional amount to indent an item's for readability.

         Returns:
             str: Formatted string suitable for saving in a file or printing.

         """
        cat_dict = result.get('Categorical columns', {})
        if not cat_dict:
            return ""
        count_dict = result['Categorical counts']
        sum_list = [f"{offset}{indent}Categorical column values[Events, Files]:"]
        sorted_tuples = sorted(cat_dict.items(), key=lambda x: x[0])
        for entry in sorted_tuples:
            sum_list = sum_list + self._get_categorical_col(entry, count_dict, offset="", indent="   ")
        return "\n".join(sum_list)

    def _get_dataset_string(self, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all of the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Total events={result.get('Total events', 0)} "
                    f"Total files={result.get('Total files', 0)}"]
        cat_string = self._get_categorical_string(result, offset="", indent=indent)
        if cat_string:
            sum_list.append(cat_string)
        val_cols = result.get("Value columns", {})
        if val_cols:
            sum_list.append(ColumnValueSummary._get_value_string(val_cols, offset="", indent=indent))
        return "\n".join(sum_list)

    def _get_individual_string(self, result, indent=BaseSummary.DISPLAY_INDENT):

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
            sum_list.append(ColumnValueSummary._get_value_string(val_cols, offset=indent, indent=indent))
        return "\n".join(sum_list)

    def _get_categorical_col(self, entry, count_dict, offset="", indent="   "):
        """ Return  a string with the summary for a particular categorical column.

         Parameters:
             entry(tuple): (Name of the column, summary dict for that column)
             count_dict (dict): Count of the total number of unique values indexed by the name
             offset(str): String of blanks used as offset for all items
             indent (str):  String of blanks used as the additional amount to indent for this item's readability.

         Returns:
             list: Formatted strings, each corresponding to a line in the output.
         """
        num_unique = count_dict[entry[0]]
        num_disp = min(self.op.max_categorical, num_unique)
        col_list = [f"{offset}{indent * 2}{entry[0]}: {num_unique} unique values "
                    f"(displaying top {num_disp} values)"]
        # Create and partition the list of individual entries
        value_list = [f"{item[0]}{str(item[1])}" for item in entry[1].items()]
        value_list = value_list[:num_disp]
        part_list = ColumnValueSummary.partition_list(value_list, self.op.values_per_line)
        return col_list + [f"{offset}{indent * 3}{ColumnValueSummary.get_list_str(item)}" for item in part_list]

    @staticmethod
    def get_list_str(lst):
        return f"{' '.join(str(item) for item in lst)}"

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

    @staticmethod
    def sort_dict(count_dict, reverse=False):
        sorted_tuples = sorted(count_dict.items(), key=lambda x: x[1][0], reverse=reverse)
        return len(sorted_tuples), sorted_tuples
