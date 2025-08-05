""" Summarize the type_defs in the dataset. """

import pandas as pd
from hed.models.tabular_input import TabularInput
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary
from hed.models.def_expand_gather import DefExpandGatherer


class SummarizeDefinitionsOp(BaseOp):
    """ Summarize the definitions used in the dataset based on Def and Def-expand.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.

    Optional remodeling parameters:
         - **append_timecode** (*bool*): If False (default), the timecode is not appended to the summary filename.

    The purpose is to produce a summary of the definitions used in a dataset.

    """
    NAME = "summarize_definitions"

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

    SUMMARY_TYPE = 'type_defs'

    def __init__(self, parameters):
        """ Constructor for the summary of definitions used in the dataset.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.append_timecode = parameters.get('append_timecode', False)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Create summaries of definitions.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: a copy of df

        Side effect:
            Updates the relevant summary.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.setdefault(self.summary_name,
                                                      DefinitionSummary(self, dispatcher.hed_schema))
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name, 'sidecar': sidecar,
                                'schema': dispatcher.hed_schema})
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []


class DefinitionSummary(BaseSummary):
    """ Manager for summaries of the definitions used in a dataset."""

    def __init__(self, sum_op, hed_schema, known_defs=None):
        """ Constructor for the summary of definitions.

        Parameters:
            sum_op (SummarizeDefinitionsOp): Summary operation class for gathering definitions.
            hed_schema (HedSchema or HedSchemaGroup):  Schema used for the dataset.
            known_defs (str or list or DefinitionDict): Definitions already known to be used.


        """
        super().__init__(sum_op)
        self.def_gatherer = DefExpandGatherer(hed_schema, known_defs=known_defs)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a "schema" and a "Sidecar".

        """
        data_input = TabularInput(
            new_info['df'], sidecar=new_info['sidecar'], name=new_info['name'])
        series, def_dict = data_input.series_a, data_input.get_def_dict(
            new_info['schema'])
        self.def_gatherer.process_def_expands(series, def_dict)

    @staticmethod
    def _build_summary_dict(items_dict, title, process_func, display_description=False):
        summary_dict = {}
        items = {}
        for key, value in items_dict.items():
            if process_func:
                value = process_func(value)
            if "#" in str(value):
                key = key + "/#"
            if display_description:
                description, value = DefinitionSummary._remove_description(
                    value)
                items[key] = {"description": description,
                              "contents": str(value)}
            elif isinstance(value, list):
                items[key] = [str(x) for x in value]
            else:
                items[key] = str(value)
        summary_dict[title] = items
        return summary_dict

    def get_details_dict(self, def_summary) -> dict:
        """ Return the summary-specific information in a dictionary.

        Parameters:
            def_summary (DefExpandGatherer):  Contains the resolved dictionaries.

        Returns:
            dict: dictionary with the summary results.

        """
        known_defs_summary = self._build_summary_dict(def_summary.def_dict, "Known Definitions", None,
                                                      display_description=True)
        # ambiguous_defs_summary = self._build_summary_dict(def_gatherer.ambiguous_defs, "Ambiguous Definitions",
        #                                                   def_gatherer.get_ambiguous_group)
        # ambiguous_defs_summary = {}
        # TODO: Summary of ambiguous definitions is not implemented
        errors_summary = self._build_summary_dict(
            def_summary.errors, "Errors", None)

        known_defs_summary.update(errors_summary)
        return {"Name": "", "Total events": 0, "Total files": 0, "Files": [], "Specifics": known_defs_summary}
        # return known_defs_summary

    def merge_all_info(self) -> object:
        """ Create an Object containing the definition summary.

        Returns:
            Object: The overall summary object for type_defs.

        """
        return self.def_gatherer

    def _get_result_string(self, name, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_dataset_string to get the overall summary string and
            _get_individual_string to get an individual summary string.

        """
        if name == "Dataset":
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(result, indent=indent)

    @staticmethod
    def _nested_dict_to_string(data, indent, level=1):
        """ Return string summary of definitions used by recursively traversing the summary info.

        Parameters:
            data (dict):  Dictionary containing information.
            indent (str):  Spaces to indent the nested results.
            level (int):  (Default 1): Level indicator for recursive calls.

        """
        result = []
        for key, value in data.items():
            if isinstance(value, dict):
                result.append(f"{indent * level}{key}: {len(value)} items")
                result.append(DefinitionSummary._nested_dict_to_string(
                    value, indent, level + 1))
            elif isinstance(value, list):
                result.append(f"{indent * level}{key}:")
                for item in value:
                    result.append(f"{indent * (level + 1)}{item}")
            else:
                result.append(f"{indent * level}{key}: {value}")
        return "\n".join(result)

    @staticmethod
    def _get_dataset_string(summary_dict, indent=BaseSummary.DISPLAY_INDENT):
        """ Return the string representing the summary of the definitions across the dataset.

        Parameters:
            summary_dict (dict): Contains the merged summary information.
            indent (str): Spaces to indent successively levels.

        Returns:
            str:  String summary of the definitions used in the dataset.

        """
        return DefinitionSummary._nested_dict_to_string(summary_dict, indent)

    @staticmethod
    def _remove_description(def_entry):
        """ Remove description from a definition entry.

        Parameters:
            def_entry (DefinitionEntry): Definition entry from which to remove its definition.

        Returns:
            tuple[str, DefinitionEntry]:
            - Description string.
            - DefinitionEntry after description has been removed.


        """
        def_group = def_entry.contents.copy()
        description = ""
        desc_tag = def_group.find_tags({"description"}, include_groups=False)
        if desc_tag:
            def_group.remove(desc_tag)
            desc_tag = desc_tag[0]
            description = desc_tag.extension

        return description, def_group

    @staticmethod
    def _get_individual_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the summary for an individual tabular file.

        Parameters:
            result (dict): Dictionary of summary information for a particular tabular file.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        return ""
