""" Summarize the HED tags in collection of tabular files.  """

from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_tag_counts import HedTagCounts
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeHedTagsOp(BaseOp):
    """ Summarize the HED tags in collection of tabular files.

    Notes:
        The required parameters are:
        - summary_name (str)   The name of the summary.
        - summary_filename (str)   Base filename of the summary.
        - type_tags (list)  Type tag to get_summary separately (e.g. 'condition-variable' or 'task').
        - include_context (bool):  If True, expand Onset and Offset tags.

        Optional parameters are:
        - breakout_list (list):  A list of tags to be separated.


    The purpose of this op is to produce a summary of the occurrences of specified tag. This summary
    is often used with 'condition-variable' to produce a summary of the experimental design.


    """

    PARAMS = {
        "operation": "summarize_hed_tags",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "tags": dict,
            "expand_context": bool
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = "hed_tag_summary"

    def __init__(self, parameters):
        """ Constructor for the summarize hed tags operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        Raises:

            - KeyError:
                - If a required parameter is missing.
                - If an unexpected parameter is provided.

            - TypeError:
                - If a parameter has the wrong type.

        """
        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.tags = parameters['tags']
        self.expand_context = parameters['expand_context']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher) - dispatcher object for managing the operations.
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context

        """
        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = HedTagSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df


class HedTagSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.tags = sum_op.tags
        self.expand_context = sum_op.expand_context

    def update_context(self, new_context):
        counts = HedTagCounts(new_context['name'])
        input_data = TabularInput(new_context['df'], hed_schema=new_context['schema'], sidecar=new_context['sidecar'])
        definitions = input_data.get_definitions().gathered_defs
        for objs in input_data.iter_dataframe(hed_ops=[new_context['schema']], return_string_only=False,
                                              expand_defs=False, remove_definitions=True):
            counts.update_event_counts(objs['HED'])

        self.summary_dict[new_context["name"]] = counts

    def _get_summary_details(self, merge_counts):
        template, unmatched = merge_counts.organize_tags(self.tags)
        details = {}
        for key, key_list in self.tags.items():
            details[key] = self._get_details(key_list, template, verbose=True)
        leftovers = [value.get_info(verbose=True) for value in unmatched]
        return {"Main tags": details, "Other tags": leftovers}

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        sum_list = [f"\n{name}\n{indent}Main tags[events,files]:"]
        for category, tags in result['Main tags'].items():
            sum_list.append(f"{indent}{indent}{category}:")
            if tags:
                sum_list.append(f"{indent}{indent}{indent}{' '.join(self._tag_details(tags))}")
        if result['Other tags']:
            sum_list.append(f"\tOther tags[events,files]:")
            sum_list.append(f"{indent}{indent}{' '.join(self._tag_details(result['Other tags']))}")
        return "\n".join(sum_list)

    @staticmethod
    def _tag_details(tags):
        tag_list = []
        for tag in tags:
            tag_list.append(f"{tag['tag']}[{tag['events']},{len(tag['files'])}]")
        return tag_list

    @staticmethod
    def _get_details(key_list, template, verbose=False):
        key_details = []
        for item in key_list:
            for tag_cnt in template[item.lower()]:
                key_details.append(tag_cnt.get_info(verbose=verbose))
        return key_details

    def _merge_all(self):
        all_counts = HedTagCounts()
        for key, counts in self.summary_dict.items():
            HedTagCounts.merge_tag_dicts(all_counts.tag_dict, counts.tag_dict)
        return all_counts
