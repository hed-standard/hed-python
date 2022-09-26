import json


class HedVariableCounts:
    """ Keeps a summary of one value of one type of variable.

    Parameters:
        variable_value (str)  The value of the variable to be counted
        variable_type (str)   The type of variable.

    Examples:
        HedVariableCounts('SymmetricCond', 'condition-variable') keeps counts of Condition-variable/Symmetric

    """

    def __init__(self, variable_value, variable_type):
        self.variable_value = variable_value
        self.variable_type = variable_type.lower()
        self.direct_references = 0
        self.total_events = 0
        self.events = 0
        self.multiple_events = 0
        self.multiple_event_maximum = 0
        self.level_counts = {}

    def update(self, variable_info):
        """ Update the counts from a HedTypeVariable.

        Parameters:
            variable_info (HedTypeFactor) information about the contents for a particular data file.

        """
        var_sum = variable_info.get_summary(full=True)
        self.direct_references += var_sum['direct_references']
        self.total_events += var_sum['total_events']
        self.events += var_sum['events']
        self.multiple_events += var_sum['multiple_events']
        self.multiple_event_maximum = max(self.multiple_event_maximum, var_sum['multiple_event_maximum'])
        self._update_levels(var_sum.get('level_counts', {}))

    def _update_levels(self, level_dict):
        for key, item in level_dict.items():
            if key not in self.level_counts:
                self.level_counts[key] = {'files': 0, 'events': 0}
            self.level_counts[key]['files'] = self.level_counts[key]['files'] + 1
            self.level_counts[key]['events'] = self.level_counts[key]['events'] + item

    def get_summary(self, as_json=False):
        summary = {'variable_value': self.variable_value,
                   'variable_type': self.variable_type,
                   'levels': len(self.level_counts.keys()),
                   'direct_references': self.direct_references,
                   'total_events': self.total_events,
                   'events': self.events,
                   'multiple_events': self.multiple_events,
                   'multiple_event_maximum': self.multiple_event_maximum}
        if self.level_counts:
            summary['level_counts'] = self.level_counts
        if as_json:
            return json.dumps(summary, indent=4)
        return summary


class HedVariableSummary:
    """ Holds a consolidated summary for one type variable. """

    def __init__(self, variable_type, name=''):
        """ Constructor for HedVariableSummary for a particular type of variable.

        Args:
            variable_type (str)    Tag representing the type in this summary

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

        Args:
            variable (HedTypeVariable):  Contains the information about
        """

        for type_var in variable.type_variables:
            if type_var not in self.summary:
                self.summary[type_var] = HedVariableCounts(type_var, self.variable_type)
            var_counts = self.summary[type_var]
            var_counts.update(variable.get_variable(type_var))


if __name__ == '__main__':
    import os
    from hed.tools.analysis.hed_variable_manager import HedVariableManager
    from hed.schema import load_schema_version
    from hed.models import TabularInput, Sidecar
    from hed.tools.analysis.analysis_util import get_assembled_strings
    schema = load_schema_version(xml_version="8.1.0")
    bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   '../../../tests/data/bids/eeg_ds003654s_hed'))
    events_path = os.path.realpath(os.path.join(bids_root_path,
                                                'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    hed_strings = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
    def_mapper = input_data.get_definitions()
    var_manager = HedVariableManager(hed_strings, schema, def_mapper)
    var_manager.add_type_variable("condition-variable")
    var_summary = HedVariableSummary("condition-variable")
    for man_var in var_manager.type_variables:
        var_map = var_manager.get_type_variable(man_var)
        var_summary.update_summary(var_map)

    final_summary = var_summary.get_summary(as_json=False)
    print(f"Variable summary\n{final_summary}")
    print(f"\n\n{str(var_summary)}")
