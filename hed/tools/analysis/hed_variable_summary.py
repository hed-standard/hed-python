
class HedVariableCounts:

    def __init__(self, name, variable_type="condition-variable"):
        self.variable_name = name
        self.variable_type = variable_type.lower()
        self.direct_references = 0
        self.total_events = 0
        self.number_type_events = 0
        self.number_multiple_events = 0
        self.multiple_event_maximum = 0
        self.level_counts = {}

    def update(self, var_counts):
        var_sum = var_counts.get_summary(full=True)
        self.direct_references += var_sum['direct_references']
        self.total_events += var_sum['total_events']
        self.number_type_events += var_sum['number_type_events']
        self.number_multiple_events += var_sum['number_multiple_events']
        self.multiple_event_maximum = max(self.multiple_event_maximum, var_sum['multiple_event_maximum'])
        self._update_levels(var_sum['level_counts'])

    def _update_levels(self, level_dict):
        for key, item in level_dict.items():
            if key not in self.level_counts:
                self.level_counts[key] = {'files': 0, 'events': 0}
            self.level_counts[key]['files'] = self.level_counts[key]['files'] + 1
            self.level_counts[key]['events'] = self.level_counts[key]['events'] + item

    def get_summary(self, as_json=False):
        summary = {'name': self.variable_name, 'variable_type': self.variable_type,
                   'levels': len(self.level_counts.keys()),
                   'direct_references': self.direct_references,
                   'total_events': self.total_events,
                   'number_type_events': self.number_type_events,
                   'number_multiple_events': self.number_multiple_events,
                   'multiple_event_maximum': self.multiple_event_maximum,
                   'level_counts': self.level_counts}
        if as_json:
            return json.dumps(summary, indent=4)
        return summary


class HedVariableSummary:

    def __init__(self, variable_type="condition-variable"):
        """ Constructor for HedVariableSummary.

        Args:
            variable_type (str)    Tag representing the type in this summary

        """

        self.variable_type = variable_type.lower()
        self.summaries = {}

    def __str__(self):
        return f"{self.variable_type}[{self.variable_type}]: {len(self.summaries)} type_variables "

    def get_summaries(self, as_json=True):
        sum_dict = {}
        for var_name, var_counts in self.summaries.items():
            sum_dict[var_name] = var_counts.get_summary(as_json=False)
        if as_json:
            return json.dumps(sum_dict, indent=4)
        else:
            return sum_dict

    def update_summary(self, var_counts):
        if var_counts.variable_name not in self.summaries:
            self.summaries[var_counts.variable_name] = HedVariableCounts(var_counts.variable_name,
                                                                         var_counts.variable_type)
        summary = self.summaries[var_counts.variable_name]
        summary.update(var_counts)


if __name__ == '__main__':
    import os
    import json
    from hed.tools.analysis.hed_variable_manager import HedVariableManager
    from hed.schema import load_schema_version
    from hed.models import HedString, DefinitionEntry, TabularInput, Sidecar
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
    var_summary = HedVariableSummary(variable_type="condition-variable")

    for man_var in var_manager.type_variables:
        var_map = var_manager.get_variable(man_var)
        var_summary.update_summary(var_map)

    summary = var_summary.get_summaries(as_json=False)
    print(f"Variable summary\n{var_summary.get_summaries()}")
