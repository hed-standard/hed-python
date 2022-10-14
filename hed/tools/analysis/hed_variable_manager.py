import pandas as pd
import json
from hed.tools.analysis.hed_type_variable import HedTypeVariable
from hed.tools.analysis.hed_context_manager import HedContextManager


class HedVariableManager:

    def __init__(self, hed_strings, hed_schema, definitions):
        """ Create a variable manager for one tabular file for all type variables.

        Parameters:
            hed_strings (list): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use for processing.
            definitions (dict): A dictionary of DefinitionEntry objects.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.
        """

        self.hed_schema = hed_schema
        self.definitions = definitions
        self.context_manager = HedContextManager(hed_strings)
        self._variable_type_map = {}   # a map of type variable into HedTypeVariable objects

    @property
    def type_variables(self):
        return list(self._variable_type_map.keys())

    def add_type_variable(self, type_name):
        if type_name.lower() in self._variable_type_map:
            return
        self._variable_type_map[type_name.lower()] = HedTypeVariable(self.context_manager, self.hed_schema,
                                                                     self.definitions,
                                                                     variable_type=type_name)

    def get_factor_vectors(self, type_name, type_variables=None, factor_encoding="one-hot"):
        this_var = self.get_type_variable(type_name)
        if this_var is None:
            return None
        variables = this_var.get_variable_names()
        if variables is None:
            variables = type_variables
        df_list = [0]*len(variables)
        for index, variable in enumerate(variables):
            var_sum = this_var._variable_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        return pd.concat(df_list, axis=1)

    def get_type_variable(self, type_name):
        return self._variable_type_map.get(type_name.lower(), None)

    def get_type_variable_factor(self, var_type, var_name):
        """ Return the HedTypeFactors associated with var_name or None. """
        this_map = self._variable_type_map.get(var_type, None)
        if this_map:
            return this_map._variable_map.get(var_name, None)
        return None

    def get_type_variable_def_names(self, type_var):
        this_map = self._variable_type_map.get(type_var, None)
        if not this_map:
            return []
        return this_map.get_variable_def_names()

    def summarize_all(self, as_json=False):
        summary = {}
        for type_name, type_var in self._variable_type_map.items():
            summary[type_name] = type_var.summarize()
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def __str__(self):
        return f"Type_variables: {str(list(self._variable_type_map.keys()))}"


# if __name__ == '__main__':
#     import os
#     from hed import Sidecar, TabularInput
#     from hed.tools.analysis.analysis_util import get_assembled_strings
#     schema = load_schema_version(xml_version="8.1.0")
#
#     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#                                                    '../../../tests/data/bids_tests/eeg_ds003654s_hed'))
#     events_path = os.path.realpath(os.path.join(bids_root_path,
#                                                 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
#     sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
#     sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
#     input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
#     assembled_strings = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
#     definitions = input_data.get_definitions()
#     var_manager = HedVariableManager(assembled_strings, schema, definitions)
#     var_manager.add_type_variable("condition-variable")
#     var_cond = var_manager.get_type_variable("condition-variable")
#     var_summary = var_cond.summarize()
#     summary_total = var_manager.summarize_all()
