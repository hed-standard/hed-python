""" Summarize the HED tags in collection of tabular files.  """

from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_tag_counts import HedTagCounts
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_tag_manager import HedTagManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeHedTagsOp(BaseOp):
    """ Summarize the HED tags in collection of tabular files.


    Required remodeling parameters:   
        - **summary_name** (*str*): The name of the summary.   
        - **summary_filename** (*str*): Base filename of the summary.   
        - **tags** (*dict*): Specifies how to organize the tag output. 

    Optional remodeling parameters:    
       - **expand_context** (*bool*): If True, include counts from expanded context (not supported).   

    The purpose of this op is to produce a summary of the occurrences of hed tags organized in a specified manner.
    The


    """

    PARAMS = {
        "operation": "summarize_hed_tags",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "tags": dict
        },
        "optional_parameters": {
            "append_timecode": bool,
            "include_context": bool,
            "replace_defs": bool,
            "remove_types": list
        }
    }

    SUMMARY_TYPE = "hed_tag_summary"

    def __init__(self, parameters):
        """ Constructor for the summarize_hed_tags operation.

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
        self.tags = parameters['tags']
        self.append_timecode = parameters.get('append_timecode', False)
        self.include_context = parameters.get('include_context', True)
        self.replace_defs = parameters.get("replace_defs", True)
        self.remove_types = parameters.get("remove_types", ["Condition-variable", "Task"])

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Summarize the HED tags present in the dataset.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            DataFrame: A copy of df.

        Side effect:
            Updates the context.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = HedTagSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        x = {'df': dispatcher.post_proc_data(df_new), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar}
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df_new


class HedTagSummary(BaseSummary):

    def __init__(self, sum_op):
        super().__init__(sum_op)
        self.sum_op = sum_op

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a "schema", a "df, and a "Sidecar".

        """
        counts = HedTagCounts(new_info['name'], total_events=len(new_info['df']))
        input_data = TabularInput(new_info['df'], sidecar=new_info['sidecar'], name=new_info['name'])
        tag_man = HedTagManager(EventManager(input_data, new_info['schema']), 
                                remove_types=self.sum_op.remove_types)
        hed_objs = tag_man.get_hed_objs(include_context=self.sum_op.include_context, 
                                        replace_defs=self.sum_op.replace_defs)
        for hed in hed_objs:
            counts.update_event_counts(hed, new_info['name'])
        self.summary_dict[new_info["name"]] = counts

    def get_details_dict(self, tag_counts):
        """ Return the summary-specific information in a dictionary.

        Parameters:
            tag_counts (HedTagCounts):  Contains the counts of tags in the dataset.

        Returns:
            dict: dictionary with the summary results.

        """
        template, unmatched = tag_counts.organize_tags(self.sum_op.tags)
        details = {}
        for key, key_list in self.sum_op.tags.items():
            details[key] = self._get_details(key_list, template, verbose=True)
        leftovers = [value.get_info(verbose=True) for value in unmatched]
        return {"Name": tag_counts.name, "Total events": tag_counts.total_events,
                "Total files": len(tag_counts.files.keys()),
                "Files": [name for name in tag_counts.files.keys()],
                "Specifics": {"Main tags": details, "Other tags": leftovers}}

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
        if name == 'Dataset':
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(result, indent=indent)

    def merge_all_info(self):
        """ Create a HedTagCounts containing the overall dataset HED tag  summary.

        Returns:
            HedTagCounts - the overall dataset summary object for HED tag counts.

        """

        all_counts = HedTagCounts('Dataset')
        for key, counts in self.summary_dict.items():
            all_counts.merge_tag_dicts(counts.tag_dict)
            for file_name in counts.files.keys():
                all_counts.files[file_name] = ""
            all_counts.total_events = all_counts.total_events + counts.total_events
        return all_counts

    @staticmethod
    def _get_dataset_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Total events={result.get('Total events', 0)} "
                    f"Total files={len(result.get('Files', 0))}"]
        sum_list = sum_list + HedTagSummary._get_tag_list(result, indent=indent)
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
        sum_list = [f"Total events={result.get('Total events', 0)}"]
        sum_list = sum_list + HedTagSummary._get_tag_list(result, indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _tag_details(tags):
        tag_list = []
        for tag in tags:
            tag_list.append(f"{tag['tag']}[{tag['events']},{len(tag['files'])}]")
        return tag_list

    @staticmethod
    def _get_tag_list(result, indent=BaseSummary.DISPLAY_INDENT):
        tag_info = result["Specifics"]
        sum_list = [f"\n{indent}Main tags[events,files]:"]
        for category, tags in tag_info['Main tags'].items():
            sum_list.append(f"{indent}{indent}{category}:")
            if tags:
                sum_list.append(f"{indent}{indent}{indent}{' '.join(HedTagSummary._tag_details(tags))}")
        if tag_info['Other tags']:
            sum_list.append(f"{indent}Other tags[events,files]:")
            sum_list.append(f"{indent}{indent}{' '.join(HedTagSummary._tag_details(tag_info['Other tags']))}")
        return sum_list

    @staticmethod
    def _get_details(key_list, template, verbose=False):
        key_details = []
        for item in key_list:
            for tag_cnt in template[item.lower()]:
                key_details.append(tag_cnt.get_info(verbose=verbose))
        return key_details
