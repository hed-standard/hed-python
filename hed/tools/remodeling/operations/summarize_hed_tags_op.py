# from hed.models.tabular_input import TabularInput
# from hed.tools.analysis.analysis_util import get_assembled_strings
# from hed.tools.analysis.hed_tag_summary import HedTagSummary
# from hed.tools.analysis.hed_variable_manager import HedVariableManager
# from hed.tools.analysis.hed_variable_summary import HedVariableSummary
# from hed.tools.remodeling.operations.base_op import BaseOp
# from hed.tools.remodeling.operations.base_context import BaseContext

# TODO: Not implemented yet.


# PARAMS = {
#     "operation": "summarize_hed_tags",
#     "required_parameters": {
#         "summary_name": str,
#         "summary_filename": str,
#         "excluded_type_tags": list,
#     },
#     "optional_parameters": {
#         "breakout_list": list
#     }
# }


# class SummarizeHedTagsOp(BaseOp):
#     """ Summarize the occurrences of HED tags in the dataset.
#
#     Notes:
#         The required parameters are:
#         - summary_name (str)   The name of the summary.
#         - summary_filename (str)   Base filename of the summary.
#         - type_tags (list)  Type tag to summarize separately (e.g. 'condition-variable' or 'task')
#         - include_context (bool):  If True, expand Onset and Offset tags.
#
#         Optional parameters are:
#         - breakout_list (list):  A list of tags to be separated.
#
#
#     The purpose of this op is to produce a summary of the occurrences of specified tag. This summary
#     is often used with 'condition-variable' to produce a summary of the experimental design.
#
#
#     """
#
#     def __init__(self, parameters):
#         print()
#         # super().__init__(PARAMS["operation"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
#         # self.check_parameters(parameters)
#         # self.summary_type = 'summarize_hed_tags'
#         # self.summary_name = parameters['summary_name']
#         # self.summary_filename = parameters['summary_filename']
#         # self.type_tags = parameters['type_tags']
#         # self.include_context = parameters['include_context']
#         # self.breakout_list = parameters.get('breakout_list', HedTagSummary.BREAKOUT_LIST)
#
#     def do_op(self, dispatcher, df, name, sidecar=None):
#         """ Create factor columns corresponding to values in a specified column.
#
#         Parameters:
#             dispatcher (Dispatcher) - dispatcher object for context
#             df (DataFrame) - The DataFrame to be remodeled.
#             name (str) - Unique identifier for the dataframe -- often the original file path.
#             sidecar (Sidecar or file-like)   Only needed for HED operations.
#
#         Returns:
#             DataFrame - a new DataFrame with the factor columns appended.
#
#         Side-effect:
#             Updates the context
#
#         """
#         # summary = dispatcher.context_dict.get(self.summary_name, None)
#         # if not summary:
#         #     summary = HedTagSummary(self)
#         #     dispatcher.context_dict[self.summary_name] = summary
#         #
#         # input_data = TabularInput(df, hed_schema=dispatcher.hed_schema, sidecar=sidecar)
#         # df_new = input_data.dataframe
#         # hed_strings = get_assembled_strings(input_data, hed_schema=dispatcher.hed_schema, expand_defs=False)
#         # definitions = input_data.get_definitions().gathered_defs
#         # var_manager = HedVariableManager(hed_strings, dispatcher.hed_schema, definitions)
#         # # var_manager.add_type_variable(self.type_tag)
#         # # var_map = var_manager.get_type_variable(self.type_tag)
#         # # summary.update_context({"update": var_map})
#         # return df_new
#
#
# # class HedTagSummary(BaseContext):
# #
# #     def __init__(self, sum_op):
# #         super().__init__(sum_op.summary_type, sum_op.summary_name, sum_op.summary_filename)
# #         self.summary = HedVariableSummary(variable_type=sum_op.type_tag)
# #
# #     def update_context(self, new_context):
# #         self.summary.update_summary(new_context["update"])
# #
# #     def get_summary_details(self, verbose=True):
# #         return self.summary.get_summary(as_json=False)
