"""  Summarize the column names in a collection of tabular files. """

import pandas as pd
from hed.tools.analysis.column_name_summary import ColumnNameSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeColumnNamesOp(BaseOp):
    """  Summarize the column names in a collection of tabular files.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.

    Optional remodeling parameters:
        - **append_timecode** (*bool*): If False (default), the timecode is not appended to the summary filename.

    The purpose is to check that all the tabular files have the same columns in same order.

    """
    NAME = "summarize_column_names"

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
            }
        },
        "required": [
            "summary_name",
            "summary_filename"
        ],
        "additionalProperties": False
    }

    SUMMARY_TYPE = "column_names"

    def __init__(self, parameters):
        """ Constructor for summarize column names operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.append_timecode = parameters.get('append_timecode', False)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Create a column name summary for df.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Not needed for this operation.

        Returns:
            DataFrame: A copy of df.

        Side effect:
            Updates the relevant summary.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = ColumnNamesSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary(
            {"name": name, "column_names": list(df_new.columns)})
        return df_new

    @staticmethod
    def validate_input_data(parameters) -> list:
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []

class ColumnNamesSummary(BaseSummary):
    """ Manager for summaries of column names for a dataset. """
    def __init__(self, sum_op):
        """ Constructor for column name summary manager.

        Parameters:
            sum_op (SummarizeColumnNamesOp): Operation associated with this summary.

        """
        super().__init__(sum_op)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary information is kept in separate ColumnNameSummary objects for each file.
            - The summary needs a "name" str and a "column_names" list.
            - The summary uses ColumnNameSummary as the summary object.
        """
        name = new_info['name']
        if name not in self.summary_dict:
            self.summary_dict[name] = ColumnNameSummary(name=name)
        self.summary_dict[name].update(name, new_info["column_names"])

    def get_details_dict(self, column_summary) -> dict:
        """ Return the summary dictionary extracted from a ColumnNameSummary.

        Parameters:
            column_summary (ColumnNameSummary):  A column name summary for the data file.

        Returns:
            dict - a dictionary with the summary information for column names.

        """
        summary = column_summary.get_summary()
        return {"Name": summary['Summary name'], "Total events": "n/a",
                "Total files": summary['Number files'],
                "Files": [name for name in column_summary.file_dict.keys()],
                "Specifics": {"Columns": summary['Columns']}}

    def merge_all_info(self) -> 'ColumnNameSummary':
        """ Create a ColumnNameSummary containing the overall dataset summary.

        Returns:
            ColumnNameSummary - the overall summary object for column names.

        """
        all_sum = ColumnNameSummary(name='Dataset')
        for key, counts in self.summary_dict.items():
            for name, pos in counts.file_dict.items():
                all_sum.update(name, counts.unique_headers[pos])
        return all_sum

    def _get_result_string(self, name, summary, individual=False) -> str:
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            summary (dict): The dictionary of the summary results indexed by name.
            individual (bool): True if individual summary, False otherwise.

        Returns:
            str - The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_dataset_string to get the overall summary string.

        """
        if name == "Dataset":
            return self._get_dataset_string(summary, BaseSummary.DISPLAY_INDENT)
        columns = summary.get("Specifics", {}).get("Columns", [])
        if columns:
            return f"{BaseSummary.DISPLAY_INDENT}{str(columns[0])}"
        else:
            return ""

    @staticmethod
    def _get_dataset_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Number of files={result.get('Total files', 0)}"]
        specifics = result.get("Specifics", {})
        columns = specifics.get("Columns", {})
        for element in columns:
            sum_list.append(f"{indent}Columns: {str(element['Column names'])}")
            for file in element.get("Files", []):
                sum_list.append(f"{indent}{indent}{file}")
        return "\n".join(sum_list)
