""" Summarize a HED type tag in a collection of tabular files. """

from hed.models.tabular_input import TabularInput
from hed.tools.analysis.analysis_util import get_assembled_strings
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_type_counts import HedTypeCounts
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


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
        }
    }

    SUMMARY_TYPE = 'hed_type_summary'

    def __init__(self, parameters):
        """ Constructor for the summarize hed type operation.

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
        self.type_tag = parameters['type_tag'].lower()

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Summarize a specified HED type variable such as Condition-variable .

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be summarized.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually required unless event file has a HED column.

        Returns:
            DataFrame: Input DataFrame, unchanged.

        Side-effect:
            Updates the context.

        """
        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = HedTypeSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df


class HedTypeSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.type_tag = sum_op.type_tag

    def update_context(self, new_context):
        input_data = TabularInput(new_context['df'], hed_schema=new_context['schema'], sidecar=new_context['sidecar'])
        hed_strings = get_assembled_strings(input_data, hed_schema=new_context['schema'], expand_defs=False)
        definitions = input_data.get_definitions().gathered_defs
        context_manager = HedContextManager(hed_strings, new_context['schema'])
        type_values = HedTypeValues(context_manager, definitions, new_context['name'], type_tag=self.type_tag)

        counts = HedTypeCounts(new_context['name'], self.type_tag)
        counts.update_summary(type_values.get_summary(), type_values.total_events, new_context['name'])
        counts.add_descriptions(type_values.definitions)
        self.summary_dict[new_context["name"]] = counts

    def _get_summary_details(self, counts):
        return counts.get_summary()

    def _merge_all(self):
        """ Return merged information.

        Returns:
           object:  Consolidated summary of information.

        Notes:
            Abstract method be implemented by each individual context summary.

        """
        all_counts = HedTypeCounts('Dataset', self.type_tag)
        for key, counts in self.summary_dict.items():
            all_counts.update(counts)
        return all_counts

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        if name == "Dataset":
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(name, result, indent=indent)

    @staticmethod
    def _get_dataset_string(result, indent=BaseContext.DISPLAY_INDENT):
        details = result.get('details', {})
        sum_list = [f"Dataset: Type={result['type_tag']} Type values={len(details)} "
                    f"Total events={result.get('total_events', 0)} Total files={len(result.get('files', []))}"]

        for key, item in details.items():
            str1 = f"{item['events']} event(s) out of {item['total_events']} total events in {len(item['files'])} file(s)"
            if item['level_counts']:
                str1 = f"{len(item['level_counts'])} levels in " + str1
            if item['direct_references']:
                str1 = str1 + f" Direct references:{item['direct_references']}"
            if item['events_with_multiple_refs']:
                str1 = str1 + f" Multiple references:{item['events_with_multiple_refs']})"
            sum_list.append(f"{indent}{key}: {str1}")
            if item['level_counts']:
                sum_list = sum_list + HedTypeSummaryContext._level_details(item['level_counts'], indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _get_individual_string(name, result, indent=BaseContext.DISPLAY_INDENT):
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
                sum_list = sum_list + HedTypeSummaryContext._level_details(item['level_counts'],
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
