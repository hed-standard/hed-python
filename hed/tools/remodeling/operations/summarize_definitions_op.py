""" Summarize the values in the columns of a tabular file. """

from hed import DefinitionDict, TabularInput, Sidecar
from hed.models.df_util import process_def_expands
from hed.tools.analysis.analysis_util import assemble_hed
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext


class SummarizeDefinitionsOp(BaseOp):
    """ Summarize the values in the columns of a tabular file.

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
        }
    }

    SUMMARY_TYPE = 'definitions'

    def __init__(self, parameters):
        """ Constructor for the summarize column values operation.

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

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context.

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = DefinitionSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name, 'sidecar': sidecar,
                                'schema': dispatcher.hed_schema})
        return df


class DefinitionSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.defs = DefinitionDict()
        self.unresolved = {}
        self.errors = {}

    def update_context(self, new_context):
        name = new_context['name']
        data_input = TabularInput(new_context['df'], sidecar=new_context['sidecar'], name=new_context['name'])
        sidecar = Sidecar(new_context['sidecar'])
        df, _ = assemble_hed(data_input, sidecar, new_context['schema'],
                             columns_included=None, expand_defs=True)
        hed_strings = df['HED_assembled']
        self.defs, self.unresolved, errors = process_def_expands(hed_strings, new_context['schema'],
                                                                 known_defs=self.defs, ambiguous_defs=self.unresolved)
        self.errors.update(errors)

    def _get_summary_details(self, summary):
        return None

    def _merge_all(self):
        return None

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):
        if name == "Dataset":
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(name, result, indent=indent)

    @staticmethod
    def _get_dataset_string(result, indent=BaseContext.DISPLAY_INDENT):
        return ""

    @staticmethod
    def _get_individual_string(name, result, indent=BaseContext.DISPLAY_INDENT):
        return ""
