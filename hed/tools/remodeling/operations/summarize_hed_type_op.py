from hed.models.tabular_input import TabularInput
from hed.tools.analysis.analysis_util import get_assembled_strings
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_type_counts import HedTypeCounts
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeHedTypeOp(BaseOp):
    """ Summarize the occurrences of a type tag in the dataset.

    Notes: The required parameters are:
        - summary_name (str)   The name of the summary.
        - summary_filename (str)   Base filename of the summary.
        - type_tag (str)  Type tag to get_summary (e.g. 'condition-variable' or 'task')

    The purpose of this op is to produce a summary of the occurrences of specified tag. This summary
    is often used with 'condition-variable' to produce a summary of the experimental design.

    """

    PARAMS = {
        "operation": "summarize_hed_type",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "type_tag": str,
            "expand_context": bool
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = 'hed_type_summary'

    def __init__(self, parameters):
        super().__init__(self.PARAMS["operation"], self.PARAMS["required_parameters"],
                         self.PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.type_tag = parameters['type_tag'].lower()

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for context
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context.

        """
        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = HedTypeSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_prep_events(df), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df


class HedTypeSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.type_tag = sum_op.type_tag

    def _get_result_string(self, name, result):
        sum_list = [f"\n{result['name']}: {result['type_tag']} for {len(result['files'])}"]
        details = result.get('details', {})
        for key, item in details.items():
            sum_list.append(f"\t{key}:")
            sum_list.append(f"\t\tFiles: {str(item['files'])}")
            sum_list.append(f"\t\tLevels: {item['levels']}  Direct references: {item['direct_references']}")
            str1 = f"\t\tEvents: {item['events']} out of {item['total_events']} total events " + \
                   f"in {len(item['files'])} files"

            if item['events_with_multiple_refs']:
                str1 = str1 + f" (Events with multiple refs: {item['events_with_multiple_refs']})"
            sum_list.append(str1)
            if item['level_counts']:
                sum_list = sum_list + self._level_details(item['level_counts'])
        return "\n".join(sum_list)

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

    @staticmethod
    def _level_details(level_counts):
        level_list = [f"\t\tLevels:"]
        for key, details in level_counts.items():
            level_list.append(f"\t\t\t{key} [Events:{details['events']}, Files:{details['files']}]")
            if details['description']:
                level_list.append(f"\t\t\t\tDescription: {details['description']}")
            if details['tags']:
                level_list.append(f"\t\t\t\tTags: {str(details['tags'])}")
        return level_list
