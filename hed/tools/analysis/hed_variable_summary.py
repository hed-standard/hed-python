import json

from hed.tools.analysis.hed_variable_counts import HedVariableCounts


class HedVariableSummary:
    """ Holds a consolidated summary for one type variable. """

    def __init__(self, variable_type, name=''):
        """ Constructor for HedVariableSummary for a particular type of variable.

        Parameters:
            variable_type (str):    Tag representing the type in this summary

        """

        self.variable_type = variable_type.lower()
        self.name = name
        self.summary = {}

    def __str__(self):
        return f"Summary {self.name} for HED {self.variable_type} [{len(self.summary)} values]:" + '\n' + \
            self.get_summary(as_json=True)

    def get_summary(self, as_json=True):
        sum_dict = {}
        for var_value, var_counts in self.summary.items():
            sum_dict[var_value] = var_counts.get_summary(as_json=False)
        if as_json:
            return json.dumps(sum_dict, indent=4)
        else:
            return sum_dict

    def update_summary(self, variable):
        """ Update this summary based on the type variable map.

        Parameters:
            variable (HedTypeVariable):  Contains the information about.

        """

        for type_var in variable.type_variables:
            if type_var not in self.summary:
                self.summary[type_var] = HedVariableCounts(type_var, self.variable_type)
            var_counts = self.summary[type_var]
            var_counts.update(variable.get_variable(type_var))


# if __name__ == '__main__':
#     import os
#     from hed.tools.analysis.hed_variable_manager import HedVariableManager
#     from hed.schema import load_schema_version
#     from hed.models import TabularInput, Sidecar
#     from hed.tools.analysis.analysis_util import get_assembled_strings
#     schema = load_schema_version(xml_version="8.1.0")
#     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#                                                    '../../../tests/data/bids_tests/eeg_ds003654s_hed'))
#     events_path = os.path.realpath(os.path.join(bids_root_path,
#                                                 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
#     sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
#     sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
#     input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
#     hed_strings = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
#     def_mapper = input_data.get_definitions()
#     var_manager = HedVariableManager(hed_strings, schema, def_mapper)
#     var_manager.add_type_variable("condition-variable")
#     var_summary = HedVariableSummary("condition-variable")
#     for man_var in var_manager.type_variables:
#         var_map = var_manager.get_type_variable(man_var)
#         var_summary.update_summary(var_map)
#
#     final_summary = var_summary.get_summary(as_json=False)
#     print(f"Variable summary\n{final_summary}")
#     print(f"\n\n{str(var_summary)}")
