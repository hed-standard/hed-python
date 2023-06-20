""" Summarize the definitions in the dataset. """

from hed import TabularInput
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary
from hed.models.def_expand_gather import DefExpandGatherer


class SummarizeDefinitionsOp(BaseOp):
    """ Summarize the definitions in the dataset.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.   
        - **summary_filename** (*str*): Base filename of the summary.   

    The purpose is to produce a summary of the values in a tabular file.

    """

    PARAMS = {
        "operation": "summarize_definitions",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str
        },
        "optional_parameters": {
            "append_timecode": bool
        }
    }

    SUMMARY_TYPE = 'definitions'

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
        self.append_timecode = parameters.get('append_timecode', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create summaries of definitions

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: a copy of df

        Side-effect:
            Updates the relevant summary.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.setdefault(self.summary_name,
                                                      DefinitionSummary(self, dispatcher.hed_schema))
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name, 'sidecar': sidecar,
                                'schema': dispatcher.hed_schema})
        return df_new


class DefinitionSummary(BaseSummary):
    def __init__(self, sum_op, hed_schema, known_defs=None):
        super().__init__(sum_op)
        self.def_gatherer = DefExpandGatherer(hed_schema, known_defs=known_defs)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a "schema" and a "Sidecar".

        """
        data_input = TabularInput(new_info['df'], sidecar=new_info['sidecar'], name=new_info['name'])
        series, def_dict = data_input.series_a, data_input.get_def_dict(new_info['schema'])
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
                description, value = DefinitionSummary._remove_description(value)
                items[key] = {"description": description, "contents": str(value)}
            elif isinstance(value, list):
                items[key] = [str(x) for x in value]
            else:
                items[key] = str(value)
        summary_dict[title] = items
        return summary_dict

    def get_details_dict(self, def_gatherer):
        """ Return the summary-specific information in a dictionary.

        Parameters:
            def_gatherer (DefExpandGatherer):  Contains the resolved dictionaries.

        Returns:
            dict: dictionary with the summary results.

        """
        known_defs_summary = self._build_summary_dict(def_gatherer.def_dict, "Known Definitions", None,
                                                      display_description=True)
        ambiguous_defs_summary = self._build_summary_dict(def_gatherer.ambiguous_defs, "Ambiguous Definitions",
                                                          def_gatherer.get_ambiguous_group)
        errors_summary = self._build_summary_dict(def_gatherer.errors, "Errors", None)

        known_defs_summary.update(ambiguous_defs_summary)
        known_defs_summary.update(errors_summary)
        return known_defs_summary

    def merge_all_info(self):
        """ Create an Object containing the definition summary.

        Returns:
            Object - the overall summary object for definitions.

        """
        return self.def_gatherer

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
    def _nested_dict_to_string(data, indent, level=1):
        result = []
        for key, value in data.items():
            if isinstance(value, dict):
                result.append(f"{indent * level}{key}: {len(value)} items")
                result.append(DefinitionSummary._nested_dict_to_string(value, indent, level + 1))
            elif isinstance(value, list):
                result.append(f"{indent * level}{key}:")
                for item in value:
                    result.append(f"{indent * (level + 1)}{item}")
            else:
                result.append(f"{indent * level}{key}: {value}")
        return "\n".join(result)

    @staticmethod
    def _get_dataset_string(summary_dict, indent=BaseSummary.DISPLAY_INDENT):
        return DefinitionSummary._nested_dict_to_string(summary_dict, indent)

    @staticmethod
    def _remove_description(def_entry):
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
