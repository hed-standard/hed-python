""" Summarize a HED type tag in a collection of tabular files. """

from hed.models.tabular_input import TabularInput
from hed.models.sidecar import Sidecar
from hed.models.df_util import get_assembled
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_type_counts import HedTypeCounts
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeHedTypeOp(BaseOp):
    """ Summarize a HED type tag in a collection of tabular files.

    Required remodeling parameters:   
        - **summary_name** (*str*): The name of the summary.   
        - **summary_filename** (*str*): Base filename of the summary.   
        - **type_tag** (*str*):Type tag to get_summary (e.g. `condition-variable` or `task` tags).   

    The purpose of this op is to produce a summary of the occurrences of specified tag. This summary
    is often used with `condition-variable` to produce a summary of the experimental design.

    """

    PARAMS = {
        "operation": "summarize_hed_type",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "type_tag": str
        },
        "optional_parameters": {
            "append_timecode": bool
        }
    }

    SUMMARY_TYPE = 'hed_type_summary'

    def __init__(self, parameters):
        """ Constructor for the summarize hed type operation.

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
        self.type_tag = parameters['type_tag'].lower()
        self.append_timecode = parameters.get('append_timecode', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Summarize a specified HED type variable such as Condition-variable .

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be summarized.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually required unless event file has a HED column.

        Returns:
            DataFrame: A copy of df

        Side-effect:
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


class HedTypeSummary(BaseSummary):

    def __init__(self, sum_op):
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
        input_data = TabularInput(new_info['df'], sidecar=sidecar, name=new_info['name'])
        hed_strings, definitions = get_assembled(input_data, sidecar, new_info['schema'], 
                                                 extra_def_dicts=None, join_columns=True, expand_defs=False)
        context_manager = HedContextManager(hed_strings, new_info['schema'])
        type_values = HedTypeValues(context_manager, definitions, new_info['name'], type_tag=self.type_tag)

        counts = HedTypeCounts(new_info['name'], self.type_tag)
        counts.update_summary(type_values.get_summary(), type_values.total_events, new_info['name'])
        counts.add_descriptions(type_values.definitions)
        self.summary_dict[new_info["name"]] = counts

    def get_details_dict(self, counts):
        """ Return the summary-specific information in a dictionary.

        Parameters:
            counts (HedTypeCounts):  Contains the counts of the events in which the type occurs.

        Returns:
            dict: dictionary with the summary results.

        """
        return counts.get_summary()

    def merge_all_info(self):
        """ Create a HedTypeCounts containing the overall dataset HED type summary.

        Returns:
            HedTypeCounts - the overall dataset summary object for HED type summary.

        """
        all_counts = HedTypeCounts('Dataset', self.type_tag)
        for key, counts in self.summary_dict.items():
            all_counts.update(counts)
        return all_counts

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
        details = result.get('details', {})
        sum_list = [f"Dataset: Type={result['type_tag']} Type values={len(details)} "
                    f"Total events={result.get('total_events', 0)} Total files={len(result.get('files', []))}"]

        for key, item in details.items():
            str1 = f"{item['events']} event(s) out of {item['total_events']} total events in " + \
                   f"{len(item['files'])} file(s)"
            if item['level_counts']:
                str1 = f"{len(item['level_counts'])} levels in " + str1
            if item['direct_references']:
                str1 = str1 + f" Direct references:{item['direct_references']}"
            if item['events_with_multiple_refs']:
                str1 = str1 + f" Multiple references:{item['events_with_multiple_refs']})"
            sum_list.append(f"{indent}{key}: {str1}")
            if item['level_counts']:
                sum_list = sum_list + HedTypeSummary._level_details(item['level_counts'], indent=indent)
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
        details = result.get('details', {})
        sum_list = [f"Type={result['type_tag']} Type values={len(details)} "
                    f"Total events={result.get('total_events', 0)}"]

        for key, item in details.items():
            sum_list.append(f"{indent*2}{key}: {item['levels']} levels in {item['events']} events")
            str1 = ""
            if item['direct_references']:
                str1 = str1 + f" Direct references:{item['direct_references']}"
            if item['events_with_multiple_refs']:
                str1 = str1 + f" (Multiple references:{item['events_with_multiple_refs']})"
            if str1:
                sum_list.append(f"{indent*3}{str1}")
            if item['level_counts']:
                sum_list = sum_list + HedTypeSummary._level_details(item['level_counts'],
                                                                    offset=indent, indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _level_details(level_counts, offset="", indent=""):
        level_list = []
        for key, details in level_counts.items():
            str1 = f"[{details['events']} events, {details['files']} files]:"
            level_list.append(f"{offset}{indent*2}{key} {str1}")
            if details['tags']:
                level_list.append(f"{offset}{indent*3}Tags: {str(details['tags'])}")
            if details['description']:
                level_list.append(f"{offset}{indent*3}Description: {details['description']}")
        return level_list
