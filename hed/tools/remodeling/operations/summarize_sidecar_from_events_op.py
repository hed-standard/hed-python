""" Create a JSON sidecar from column values in a collection of tabular files. """

import json
from hed.tools import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeSidecarFromEventsOp(BaseOp):
    """ Create a JSON sidecar from column values in a collection of tabular files.

    Required remodeling parameters:   
        - **summary_name** (*str*): The name of the summary.   
        - **summary_filename** (*str*): Base filename of the summary.   
        - **skip_columns** (*list*): Names of columns to skip in the summary.   
        - **value_columns** (*list*): Names of columns to treat as value columns rather than categorical columns.   

    The purpose is to produce a JSON sidecar template for annotating a dataset with HED tags.

    """

    PARAMS = {
        "operation": "summarize_sidecar_from_events",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "skip_columns": list,
            "value_columns": list,
        },
        "optional_parameters": {
            "append_timecode": bool
        }
    }

    SUMMARY_TYPE = "events_to_sidecar"

    def __init__(self, parameters):
        """ Constructor for summarize sidecar from events operation.

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

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Extract a sidecar from events file.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for managing the operations.
            df (DataFrame): The tabular file to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            DataFrame: A copy of df.

        Side-effect:
            Updates the associated summary if applicable.

        """

        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = EventsToSidecarSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name})
        return df_new


class EventsToSidecarSummary(BaseSummary):

    def __init__(self, sum_op):
        super().__init__(sum_op)
        self.value_cols = sum_op.value_columns
        self.skip_cols = sum_op.skip_columns

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str and a "df".

        """

        tab_sum = TabularSummary(value_cols=self.value_cols, skip_cols=self.skip_cols, name=new_info["name"])
        tab_sum.update(new_info['df'], new_info['name'])
        self.summary_dict[new_info["name"]] = tab_sum

    def get_details_dict(self, summary_info):
        """ Return the summary-specific information.

        Parameters:
            summary_info (TabularSummary):  Summary to return info from

        Notes:
            Abstract method be implemented by each individual context summary.

        """

        return {"files": summary_info.files, "total_files": summary_info.total_files,
                "total_events": summary_info.total_events, "skip_cols": summary_info.skip_cols,
                "sidecar": summary_info.extract_sidecar_template()}

    def merge_all_info(self):
        """ Merge summary information from all of the files

        Returns:
           TabularSummary:  Consolidated summary of information.

        """

        all_sum = TabularSummary(name='Dataset')
        for key, tab_sum in self.summary_dict.items():
            all_sum.update_summary(tab_sum)
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

    @staticmethod
    def _get_dataset_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all of the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Total events={result.get('total_events', 0)} "
                    f"Total files={result.get('total_files', 0)}",
                    f"Skip columns: {str(result.get('skip_cols', []))}",
                    f"Value columns: {str(result.get('value_cols', []))}",
                    f"Sidecar:\n{json.dumps(result['sidecar'], indent=indent)}"]
        return "\n".join(sum_list)

    @staticmethod
    def _get_individual_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the summary for an individual tabular file.

        Parameters:
            result (dict): Dictionary of summary information for a particular tabular file.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Total events={result.get('total_events', 0)}",
                    f"Skip columns: {str(result.get('skip_cols', []))}",
                    f"Value columns: {str(result.get('value_cols', []))}",
                    f"Sidecar:\n{json.dumps(result['sidecar'], indent=indent)}"]
        return "\n".join(sum_list)
