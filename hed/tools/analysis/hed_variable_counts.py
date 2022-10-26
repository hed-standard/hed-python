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
                self.level_counts[key] = {'files': 0, 'events': 0, 'description': ''}
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