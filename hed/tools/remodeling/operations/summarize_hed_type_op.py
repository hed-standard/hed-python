""" Summarize the HED type tags in collection of tabular files.  """

import pandas as pd
from hed.models.tabular_input import TabularInput
from hed.models.sidecar import Sidecar
from hed.tools.analysis.hed_type import HedType
from hed.tools.analysis.hed_type_counts import HedTypeCounts
from hed.tools.analysis.event_manager import EventManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeHedTypeOp(BaseOp):
    """ Summarize a HED type tag in a collection of tabular files.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.
        - **type_tag** (*str*):Type tag to get_summary (e.g. `condition-variable` or `task` tags).

    Optional remodeling parameters:
        - **append_timecode** (*bool*): If true, the timecode is appended to the base filename when summary is saved.

    The purpose of this op is to produce a summary of the occurrences of specified tag. This summary
    is often used with `condition-variable` to produce a summary of the experimental design.

    """

    NAME = "summarize_hed_type"

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
            "type_tag": {
                "type": "string",
                "description": "Type tag (such as Condition-variable or Task to design summaries for.."
            },
            "append_timecode": {
                "type": "boolean",
                "description": "If true, the timecode is appended to the base filename so each run has a unique name."
            }
        },
        "required": [
            "summary_name",
            "summary_filename",
            "type_tag"
        ],
        "additionalProperties": False
    }

    SUMMARY_TYPE = 'hed_type_summary'

    def __init__(self, parameters):
        """ Constructor for the summarize HED type operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.type_tag = parameters['type_tag'].casefold()
        self.append_timecode = parameters.get('append_timecode', False)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Summarize a specified HED type variable such as Condition-variable.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be summarized.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually required unless event file has a HED column.

        Returns:
            DataFrame: A copy of df

        Side effect:
            Updates the relevant summary.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = HedTypeSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []


class HedTypeSummary(BaseSummary):
    """ Manager of the HED type summaries. """

    def __init__(self, sum_op):
        """ Constructor for HED type summary manager.

        Parameters:
            sum_op (SummarizeHedTypeOp): Operation associated with this summary.

        """
        super().__init__(sum_op)
        self.type_tag = sum_op.type_tag

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a "schema", a "df, and a "Sidecar".

        """

        sidecar = new_info['sidecar']
        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(sidecar)
        input_data = TabularInput(
            new_info['df'], sidecar=sidecar, name=new_info['name'])
        type_values = HedType(EventManager(input_data, new_info['schema']), new_info['name'], type_tag=self.type_tag)
        counts = HedTypeCounts(new_info['name'], self.type_tag)
        counts.update_summary(type_values.get_summary(),
                              type_values.total_events, new_info['name'])
        counts.add_descriptions(type_values.type_defs)
        self.summary_dict[new_info["name"]] = counts

    def get_details_dict(self, hed_type_counts) -> dict:
        """ Return the summary-specific information in a dictionary.

        Parameters:
            hed_type_counts (HedTypeCounts):  Contains the counts of the events in which the type occurs.

        Returns:
            dict: dictionary with the summary results.

        """
        summary = hed_type_counts.get_summary()
        files = summary.get('files', [])
        return {"Name": summary.get("name", ""), "Total events": summary.get("total_events", 0),
                "Total files": len(files), "Files": files,
                "Specifics": {"Type tag": summary.get('type_tag', 'condition-variable'),
                              "Type info": summary.get('details', {})}}

    def merge_all_info(self) -> 'HedTypeCounts':
        """ Create a HedTypeCounts containing the overall dataset HED type summary.

        Returns:
            HedTypeCounts - the overall dataset summary object for HED type summary.

        """
        all_counts = HedTypeCounts('Dataset', self.type_tag)
        for key, counts in self.summary_dict.items():
            all_counts.update(counts)
        return all_counts

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
            return self._get_dataset_string(summary, indent=BaseSummary.DISPLAY_INDENT)
        return self._get_individual_string(summary, indent=BaseSummary.DISPLAY_INDENT)

    @staticmethod
    def _get_dataset_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        specifics = result.get('Specifics', {})
        type_info = specifics.get('Type info', {})
        sum_list = [f"Dataset: Type={specifics.get('Type tag', 'condition-variable')} Type values={len(type_info)} "
                    f"Total events={result.get('Total events', 0)} Total files={len(result.get('Files', []))}"]

        for key, item in type_info.items():
            str1 = f"{item['events']} event(s) out of {item['total_events']} total events in " + \
                   f"{len(item['files'])} file(s)"
            if item['level_counts']:
                str1 = f"{len(item['level_counts'])} levels in " + str1
            if item['direct_references']:
                str1 = str1 + f" Direct references:{item['direct_references']}"
            if item['events_with_multiple_refs']:
                str1 = str1 + \
                    f" Multiple references:{item['events_with_multiple_refs']})"
            sum_list.append(f"{indent}{key}: {str1}")
            if item['level_counts']:
                sum_list = sum_list + \
                    HedTypeSummary._level_details(
                        item['level_counts'], indent=indent)
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
        specifics = result.get('Specifics', {})
        type_info = specifics.get('Type info', {})
        sum_list = [f"Type={specifics.get('Type tag', 'condition-variable')} Type values={len(type_info)} "
                    f"Total events={result.get('Total events', 0)}"]

        for key, item in type_info.items():
            sum_list.append(
                f"{indent*2}{key}: {item['levels']} levels in {item['events']} events")
            str1 = ""
            if item['direct_references']:
                str1 = str1 + f" Direct references:{item['direct_references']}"
            if item['events_with_multiple_refs']:
                str1 = str1 + \
                    f" (Multiple references:{item['events_with_multiple_refs']})"
            if str1:
                sum_list.append(f"{indent*3}{str1}")
            if item['level_counts']:
                sum_list = sum_list + HedTypeSummary._level_details(item['level_counts'],
                                                                    offset=indent, indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _level_details(level_counts, offset="", indent=""):
        """ Return a list of tag type summary counts at different levels.

        Parameters:
            level_counts (dict): Dictionary of tags with counts.
            offset (str): Spaces to offset the entire entry.
            indent (str): Additional spaces to indent each level.

        """
        level_list = []
        for key, details in level_counts.items():
            str1 = f"[{details['events']} events, {details['files']} files]:"
            level_list.append(f"{offset}{indent*2}{key} {str1}")
            if details['tags']:
                level_list.append(
                    f"{offset}{indent*3}Tags: {str(details['tags'])}")
            if details['description']:
                level_list.append(
                    f"{offset}{indent*3}Description: {details['description']}")
        return level_list
