
import pandas as pd


class VariableSummary:
    """ Holds index of positions for variables, defined and otherwise. """

    def __init__(self, name, number_elements, variable_type="condition-variable"):
        """ Constructor for VariableSummary.

        Args:
            name (str): Name of the variable summarized by this class.
            number_elements (int): Number of elements in the data column
            variable_type (str):  Lowercase string corresponding to a HED tag which has a takes value child.

        """

        self.name = name
        self.number_elements = number_elements
        self.variable_type = variable_type.lower()
        self.levels = {}
        self.direct_indices = {}

    def __str__(self):
        return f"{self.name}[{self.variable_type}]: {self.number_elements} elements " + \
               f"{str(self.levels)} levels {len(self.direct_indices)} references"

    def get_variable_factors(self):
        df = pd.DataFrame(0, index=range(self.number_elements), columns=[self.name])
        df.loc[self.direct_indices, [self.name]] = 1
        if not self.levels:
            return df

        levels = list(self.levels.keys())
        levels_list = [f"{self.name}.{level}" for level in levels]
        df_levels = pd.DataFrame(0, index=range(self.number_elements), columns=[levels_list])
        for index, level in enumerate(levels):
            index_keys = list(self.levels[level].keys())
            df_levels.loc[index_keys, [levels_list[index]]] = 1
        x = pd.concat([df, df_levels], axis=1)
        return x

    def get_summary(self, full=True):
        count_list = [0] * self.number_elements
        for index in list(self.direct_indices.keys()):
            count_list[index] = count_list[index] + 1
        for level, cond in self.levels.items():
            for index, item in cond.items():
                count_list[index] = count_list[index] + 1
        number_events, number_multiple, max_multiple = self.count_events(count_list)
        summary = {'name': self.name, 'variable_type': self.variable_type, 'levels': len(self.levels.keys()),
                   'direct_references': len(self.direct_indices.keys()),
                   'total events': self.number_elements, 'number events': number_events,
                   'number_multiple': number_multiple, 'multiple maximum': max_multiple}
        if full:
            summary['level counts'] = self._get_level_counts()
        return summary

    def _get_level_counts(self):
        count_dict = {}
        for level, cond in self.levels.items():
            x = len(cond.values())
            count_dict[level] = len(cond.values())
        return count_dict

    @staticmethod
    def count_events(count_list):
        number_events = 0
        number_multiple = 0
        max_multiple = count_list[0]
        for index, count in enumerate(count_list):
            if count_list[index] > 0:
                number_events = number_events + 1
            if count_list[index] > 1:
                number_multiple = number_multiple + 1
            if count_list[index] > max_multiple:
                max_multiple = count_list[index]
        return number_events, number_multiple, max_multiple


if __name__ == '__main__':
    import os
    import json
    from hed.tools.analysis.variable_manager import VariableManager
    from hed.schema import load_schema_version
    from hed.models import HedString, DefinitionEntry, TabularInput, Sidecar
    from hed.tools.analysis.analysis_util import get_assembled_strings
    schema = load_schema_version(xml_version="8.1.0")
    # test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
    #                            f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=schema),
    #                  HedString('(Def/Cond1, Offset)', hed_schema=schema),
    #                  HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast', hed_schema=schema),
    #                  HedString('', hed_schema=schema),
    #                  HedString('(Def/Cond2, Onset)', hed_schema=schema),
    #                  HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
    #                  HedString('Arm, Leg, Condition-variable/Fast, Def/Cond6/7.2', hed_schema=schema)]
    #
    # test_strings2 = [HedString(f"Def/Cond2, Def/Cond6/4, Def/Cond6/7.8, Def/Cond6/Alpha", hed_schema=schema),
    #                  HedString("Yellow", hed_schema=schema),
    #                  HedString("Def/Cond2", hed_schema=schema),
    #                  HedString("Def/Cond2, Def/Cond6/5.2", hed_schema=schema)]
    # test_strings3 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
    #                            hed_schema=schema),
    #                  HedString("Yellow", hed_schema=schema),
    #                  HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=schema),
    #                  HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=schema),
    #                  HedString("Def/Cond2, Def/Cond6/4", hed_schema=schema)]
    # def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
    # def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
    # def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
    #                  hed_schema=schema)
    # def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
    # def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=schema)
    # def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=schema)
    # defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
    #         'Cond2': DefinitionEntry('Cond2', def2, False, None),
    #         'Cond3': DefinitionEntry('Cond3', def3, True, None),
    #         'Cond4': DefinitionEntry('Cond4', def4, False, None),
    #         'Cond5': DefinitionEntry('Cond5', def5, False, None),
    #         'Cond6': DefinitionEntry('Cond6', def6, True, None)
    #         }
    #
    # conditions = VariableManager(test_strings3, schema, defs)
    # for man_var in conditions.variables:
    #     var_sum = conditions.get_variable(man_var)
    #     s = var_sum.get_summary()
    #     print(json.dumps(s))
    #     s = var_sum.get_summary(full=False)
    #     print(json.dumps(s))

    bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   '../../../tests/data/bids/eeg_ds003654s_hed'))
    events_path = os.path.realpath(os.path.join(bids_root_path,
                                                'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    hed_strings = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
    definitions = input_data.get_definitions(as_strings=False)
    var_manager = VariableManager(hed_strings, schema, definitions)

    for man_var in var_manager.variables:
        var_sum = var_manager.get_variable(man_var)
        s = var_sum.get_summary()
        print(json.dumps(s))
        # s = var_sum.get_summary(full=False)
        # print(json.dumps(s))
