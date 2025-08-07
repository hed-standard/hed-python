""" Summarize the values in the columns of a columnar file. """

import pandas as pd
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeColumnValuesOp(BaseOp):
    """ Summarize the values in the columns of a columnar file.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.

    Optional remodeling parameters:
        - **append_timecode** (*bool*): (**Optional**: Default False) If True append timecodes to the summary filename.
        - **max_categorical** (*int*): Maximum number of unique values to include in summary for a categorical column.
        - **skip_columns** (*list*):  Names of columns to skip in the summary.
        - **value_columns** (*list*): Names of columns to treat as value columns rather than categorical columns.
        - **values_per_line** (*int*): The number of values output per line in the summary.

    The purpose is to produce a summary of the values in a tabular file.

    """
    NAME = "summarize_column_values"

    PARAMS = {
        "type": "object",
        "properties": {
            "summary_name": {
                "type": "string",
                "description": "Name to use for the summary in titles."
            },
            "summary_filename": {
                "type": "string",
                "description": "Name to use for the summary file name base."
            },
            "append_timecode": {
                "type": "boolean",
                "description": "If true, the timecode is appended to the base filename so each run has a unique name."
            },
            "max_categorical": {
                "type": "integer",
                "description": "Maximum number of unique column values to show in text description."
            },
            "skip_columns": {
                "type": "array",
                "description": "List of columns to skip when creating the summary.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "value_columns": {
                "type": "array",
                "description": "Columns to be annotated with a single HED annotation and placeholder.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "values_per_line": {
                "type": "integer",
                "description": "Number of items per line to display in the text file."
            }
        },
        "required": [
            "summary_name",
            "summary_filename"
        ],
        "additionalProperties": False
    }

    SUMMARY_TYPE = 'column_values'
    VALUES_PER_LINE = 5
    MAX_CATEGORICAL = 50

    def __init__(self, parameters):
        """ Constructor for the summarize column values operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """

        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.append_timecode = parameters.get('append_timecode', False)
        self.max_categorical = parameters.get('max_categorical', float('inf'))
        self.skip_columns = parameters.get('skip_columns', [])
        self.value_columns = parameters.get('value_columns', [])
        self.values_per_line = parameters.get('values_per_line', self.VALUES_PER_LINE)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Create a summary of the column values in df.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            DataFrame: A copy of df.

        Side effect:
            Updates the relevant summary.

        """

        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = ColumnValueSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary(
            {'df': dispatcher.post_proc_data(df_new), 'name': name})
        return df_new

    @staticmethod
    def validate_input_data(parameters) -> list:
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []


class ColumnValueSummary(BaseSummary):
    """ Manager for summaries of column contents for columnar files. """

    def __init__(self, sum_op):
        """ Constructor for column value summary manager.

        Parameters:
            sum_op (SummarizeColumnValuesOp): Operation associated with this summary.

        """
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
                TabularSummary(value_cols=self.op.value_columns,
                               skip_cols=self.op.skip_columns, name=name)
        self.summary_dict[name].update(new_info['df'])

    def get_details_dict(self, tabular_summary) -> dict:
        """ Return a dictionary with the summary contained in a TabularSummary.

        Parameters:
            tabular_summary (TabularSummary): The tabular summary object.

        Returns:
            dict: Dictionary with the information suitable for extracting printout.

        """
        this_summary = tabular_summary.get_summary(as_json=False)
        unique_counts = [(key, len(count_dict)) for key,
                         count_dict in this_summary['Categorical columns'].items()]
        this_summary['Categorical counts'] = dict(unique_counts)
        for key, dict_entry in this_summary['Categorical columns'].items():
            num_disp, sorted_tuples = ColumnValueSummary.sort_dict(
                dict_entry, reverse=True)
            this_summary['Categorical columns'][key] = dict(
                sorted_tuples[:min(num_disp, self.op.max_categorical)])
        return {"Name": this_summary['Name'], "Total events": this_summary["Total events"],
                "Total files": this_summary['Total files'],
                "Files": list(this_summary['Files'].keys()),
                "Specifics": {"Value columns": list(this_summary['Value columns']),
                              "Skip columns": this_summary['Skip columns'],
                              "Value column summaries": this_summary['Value columns'],
                              "Categorical column summaries": this_summary['Categorical columns'],
                              "Categorical counts": this_summary['Categorical counts']}}

    def merge_all_info(self) -> 'TabularSummary':
        """ Create a TabularSummary containing the overall dataset summary.

        Returns:
            TabularSummary - the summary object for column values.

        """
        all_sum = TabularSummary(
            value_cols=self.op.value_columns, skip_cols=self.op.skip_columns, name='Dataset')
        for counts in self.summary_dict.values():
            all_sum.update_summary(counts)
        return all_sum

    def _get_result_string(self, name, summary, individual=False) -> str:
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            summary (dict): The dictionary of the summary results indexed by name.
            individual (bool): Whether this is for an individual file summary.

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_dataset_string to get the overall summary string and
            _get_individual_string to get an individual summary string.

        """

        if name == "Dataset":
            sum_list = [f"Dataset: Total events={summary.get('Total events', 0)} "
                        f"Total files={summary.get('Total files', 0)}"]
        else:
            sum_list = [f"Total events={summary.get('Total events', 0)}"]
        sum_list = sum_list + self._get_detail_list(summary, indent=BaseSummary.DISPLAY_INDENT)
        return "\n".join(sum_list)

    def _get_individual_string(self, result, indent=BaseSummary.DISPLAY_INDENT) -> str:
        """ Return a formatted string with the summary for an individual file.

        Parameters:
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_categorical_string to get the categorical part of the summary,
            and _get_value_string to get the value column part of the summary.

        """

        return "\n".join([
            f"Summary for {result['Name']}",
            f"  Total events: {result.get('Total events', 0)}",
            f"  Total files: {result.get('Total files', 0)}",
            f"  Value columns: {result['Specifics']['Value columns']}",
            f"  Skip columns: {result['Specifics']['Skip columns']}",
            self._get_categorical_string(result),
            self._get_value_string(result['Specifics']['Value column summaries'])
        ])


    def _format_categorical_lists(self, specifics) -> list:
        """ Format the categorical column summaries for display.

        Parameters:
            specifics (dict): The specifics dictionary from the summary.

        Returns:
            list: A list of formatted strings for the categorical column summaries.

        """
        cat_dict = specifics.get('Categorical column summaries', {})
        if not cat_dict:
            return []
        count_dict = specifics['Categorical counts']
        formatted_list = [
            f"Categorical column values[Events, Files]:"]
        sorted_tuples = sorted(cat_dict.items(), key=lambda x: x[0])
        for entry in sorted_tuples:
            formatted_list = formatted_list + self._get_categorical_col( entry, count_dict, offset="", indent="   ")
        return formatted_list

    def _get_categorical_string(self, summary, offset="", indent="   "):
        """ Return  a string with the summary for a particular categorical dictionary.

         Parameters:
             summary (dict): Dictionary of summary information for a particular tabular file.
             offset (str): String of blanks used as offset for every item
             indent (str):  String of blanks used as the additional amount to indent an item's for readability.

         Returns:
             str: Formatted string suitable for saving in a file or printing.

         """
        specifics = summary.get('Specifics', {})
        cat_dict = specifics.get('Categorical column summaries', {})
        if not cat_dict:
            return ""
        count_dict = specifics.get('Categorical counts', {})
        sum_list = [
            f"{offset}{indent}Categorical column values[Events, Files]:"]
        sorted_tuples = sorted(cat_dict.items(), key=lambda x: x[0])
        for entry in sorted_tuples:
            sum_list = sum_list + self._get_categorical_col(entry, count_dict, offset="", indent="   ")
        return "\n".join(sum_list)

    def _get_detail_list(self, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a list of strings with the details

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            list: list of formatted strings suitable for saving in a file or printing.

        """
        sum_list = []
        specifics = result["Specifics"]
        cat_string = self._get_categorical_string(
            specifics, offset="", indent=indent)
        if cat_string:
            sum_list.append(cat_string)
        val_dict = specifics.get("Value column summaries", {})
        if val_dict:
            sum_list.append(ColumnValueSummary._get_value_string(
                val_dict, offset="", indent=indent))
        return sum_list

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
        part_list = ColumnValueSummary.partition_list(
            value_list, self.op.values_per_line)
        return col_list + [f"{offset}{indent * 3}{ColumnValueSummary.get_list_str(item)}" for item in part_list]

    @staticmethod
    def get_list_str(lst) -> str:
        """ Return a str version of a list with items separated by a blank.

        Returns:
            str:  String version of list.

        """
        return f"{' '.join(str(item) for item in lst)}"

    @staticmethod
    def partition_list(lst, n) -> list:
        """ Partition a list into lists of n items.

        Parameters:
            lst (list): List to be partitioned.
            n (int):  Number of items in each sublist.

        Returns:
            list:  list of lists of n elements, the last might have fewer.

        """
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    @staticmethod
    def _get_value_string(val_dict, offset="", indent="") -> str:
        sum_list = [f"{offset}{indent}Value columns[Events, Files]:"]
        for col_name, val_counts in val_dict.items():
            sum_list.append(f"{offset}{indent*2}{col_name}{str(val_counts)}")
        return "\n".join(sum_list)

    @staticmethod
    def sort_dict(count_dict, reverse=False):
        sorted_tuples = sorted(
            count_dict.items(), key=lambda x: x[1][0], reverse=reverse)
        return len(sorted_tuples), sorted_tuples
