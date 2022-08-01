import pandas as pd
import json
from hed.schema import load_schema_version
from hed.models import HedTag, HedGroup
from hed.tools.analysis.onset_manager import OnsetManager
from hed.tools.analysis.definition_manager import DefinitionManager


class VariableFactors:
    """ Holds index of positions for variables, defined and otherwise. """
    ALLOWED_ENCODINGS = ("categorical", "one-hot")

    def __init__(self, name, number_elements, variable_type="condition-variable"):
        """ Constructor for VariableFactors.

        Args:
            name (str): Name of the variable summarized by this class.
            number_elements (int): Number of elements in the data column
            variable_type (str):  Lowercase string corresponding to a HED tag which has a takes value child.

        """

        self.variable_name = name
        self.number_elements = number_elements
        self.variable_type = variable_type.lower()
        self.levels = {}
        self.direct_indices = {}

    def __str__(self):
        return f"{self.variable_name}[{self.variable_type}]: {self.number_elements} elements " + \
               f"{str(self.levels)} levels {len(self.direct_indices)} references"

    def get_factors(self, factor_encoding="one-hot"):
        df = pd.DataFrame(0, index=range(self.number_elements), columns=[self.variable_name])
        df.loc[list(self.direct_indices.keys()), [self.variable_name]] = 1
        if not self.levels:
            return df

        levels = list(self.levels.keys())
        levels_list = [f"{self.variable_name}.{level}" for level in levels]
        df_levels = pd.DataFrame(0, index=range(self.number_elements), columns=levels_list)
        for index, level in enumerate(levels):
            index_keys = list(self.levels[level].keys())
            df_levels.loc[index_keys, [levels_list[index]]] = 1
        factors = pd.concat([df, df_levels], axis=1)
        if factor_encoding == "one-hot":
            return factors
        sum_factors = factors.sum(axis=1)
        if sum_factors.max() > 1:
            raise HedFileError("MultipleFactorSameEvent",
                               f"{self.variable_name} has multiple occurrences at index{sum_factors.idxmax()}", "")
        if factor_encoding == "categorical":
            return self.factors_to_vector(factors, levels)
        else:
            raise ValueError("BadFactorEncoding",
                             f"{factor_encoding} is not in the allowed encodings: {str(self.ALLOWED_ENDCODINGS)}")

    def factors_to_vector(self, factors, levels):
        df = pd.DataFrame('n/a', index=range(len(factors.index)), columns=[self.variable_name])
        for index, row in factors.iterrows():
            if row[self.variable_name]:
                df.at[index, self.variable_name] = self.variable_name
                continue
            for level in levels:
                if row[f"{self.variable_name}.{level}"]:
                    df.at[index, self.variable_name] = level
                    break
        return df

    def get_summary(self, full=True):
        count_list = [0] * self.number_elements
        for index in list(self.direct_indices.keys()):
            count_list[index] = count_list[index] + 1
        for level, cond in self.levels.items():
            for index, item in cond.items():
                count_list[index] = count_list[index] + 1
        number_events, number_multiple, max_multiple = self.count_events(count_list)
        summary = {'name': self.variable_name, 'variable_type': self.variable_type, 'levels': len(self.levels.keys()),
                   'direct_references': len(self.direct_indices.keys()),
                   'total_events': self.number_elements, 'number_type_events': number_events,
                   'number_multiple_events': number_multiple, 'multiple_event_maximum': max_multiple}
        if full:
            summary['level_counts'] = self._get_level_counts()
        return summary

    def _get_level_counts(self):
        count_dict = {}
        for level, cond in self.levels.items():
            count_dict[level] = len(cond.values())
        return count_dict

    @staticmethod
    def count_events(count_list):
        if not len(count_list):
            return 0, 0, None
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


class VariableManager:

    def __init__(self, hed_strings, hed_schema, hed_definitions, variable_type="condition-variable"):
        """ Create a variable manager for an events file.

        Args:
            hed_strings (list): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use for processing.
            hed_definitions (dict): A dictionary of DefinitionEntry objects.
            variable_type (str): Lowercase short form of the variable to be managed.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.
        """

        self.variable_type = variable_type.lower()
        self.hed_schema = hed_schema
        self.definitions = DefinitionManager(hed_definitions, hed_schema, variable_type=variable_type)

        onset_manager = OnsetManager(hed_strings, hed_schema)
        self.hed_strings = onset_manager.hed_strings
        self._contexts = onset_manager.contexts
        self._variable_map = {}
        self._extract_variables()

    def get_variable(self, var_name):
        """ Return the VariableFactors associated with var_name or None. """
        return self._variable_map.get(var_name, None)

    @property
    def variables(self):
        return list(self._variable_map.keys())

    def summarize_variables(self, as_json=False):
        summary = self._variable_map.copy()
        for var_name, var_sum in summary.items():
            summary[var_name] = var_sum.get_summary()
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def get_variable_factors(self, variables=None, factor_encoding="one-hot"):
        if variables is None:
            variables = self.variables
        df_list = [0]*len(variables)
        for index, variable in enumerate(variables):
            var_sum = self._variable_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        return pd.concat(df_list, axis=1)

    def __str__(self):
        return f"{self.variable_type} variables: {str(list(self._variable_map.keys()))}"

    def _extract_definition_variables(self, item, index):
        """ Extract the definition uses from a HedTag, HedGroup, or HedString.

        Args:
            item (HedTag, HedGroup, or HedString): The item to extract variable information from.
            index (int):  Position of this item in the object's hed_strings.

        Notes:
            This updates the VariableFactors information.

        """

        if isinstance(item, HedTag):
            tags = [item]
        else:
            tags = item.get_all_tags()
        for tag in tags:
            if tag.short_base_tag.lower() != "def":
                continue
            hed_vars = self.definitions.get_vars(tag)
            if not hed_vars:
                continue
            self._update_definition_variables(tag, hed_vars, index)

    def _update_definition_variables(self, tag, hed_vars, index):
        """Update the VariableFactors map with information from Def tag.

        Args:
            tag (HedTag): A HedTag that is a Def tag.
            hed_vars (list): A list of names of the hed variables
            index (ind):  The event number associated with this.

        Notes:
            This modifies the VariableFactors map.

        """
        level = tag.extension_or_value_portion.lower()
        for var_name in hed_vars:
            hed_var = self._variable_map.get(var_name, None)
            if hed_var is None:
                hed_var = VariableFactors(var_name, len(self.hed_strings))
                self._variable_map[var_name] = hed_var
            var_levels = hed_var.levels.get(level, {index: 0})
            var_levels[index] = 0
            hed_var.levels[level] = var_levels

    def _extract_variables(self):
        """ Extract all condition variables from hed_strings and event_contexts. """
        for index, hed in enumerate(self.hed_strings):
            self._extract_direct_variables(hed, index)
            self._extract_definition_variables(hed, index)
            for item in self._contexts[index]:
                self._extract_direct_variables(item, index)
                self._extract_definition_variables(item, index)

    def _extract_direct_variables(self, item, index):
        """ Extract the condition variables from a HedTag, HedGroup, or HedString.

        Args:
            item (HedTag or HedGroup): The item from which to extract condition variables.
            index (int):  Position in the array.

        """
        if isinstance(item, HedTag) and item.short_base_tag.lower() == self.variable_type:
            tag_list = [item]
        elif isinstance(item, HedGroup) and item.children:
            tag_list = item.find_tags_with_term(self.variable_type, recursive=True, include_groups=0)
        else:
            tag_list = []
        self._update_variables(tag_list, index)

    def _update_variables(self, tag_list, index):
        """ Update the VariableFactors based on tags in the list.

        Args:
            tag_list (list): A list of Condition-variable HedTags.
            index (int):  An integer representing the position in an array

        """
        for tag in tag_list:
            name = tag.extension_or_value_portion.lower()
            if not name:
                name = self.variable_type
            hed_var = self._variable_map.get(name, None)
            if hed_var is None:
                hed_var = VariableFactors(name, len(self.hed_strings))
            self._variable_map[name] = hed_var
            hed_var.direct_indices[index] = ''


if __name__ == '__main__':
    import os
    from hed import Sidecar, TabularInput, HedFileError
    from hed.tools.analysis.analysis_util import get_assembled_strings
    hed_schema = load_schema_version(xml_version="8.1.0")
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
    # conditions = VariableManager(test_strings1, schema, defs)
    # conditions = VariableManager(test_strings2, schema, defs)
    # conditions = VariableManager(test_strings3, schema, defs)
    bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   '../../../tests/data/bids/eeg_ds003654s_hed'))
    events_path = os.path.realpath(os.path.join(bids_root_path,
                                                'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    events_path = os.path.realpath('d:/sub-002_task-FacePerception_run-1_events.tsv')

    sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    definitions = input_data.get_definitions(as_strings=False)
    var_manager = VariableManager(hed_strings, hed_schema, definitions)
    df = var_manager.get_variable_factors()
    summary = var_manager.summarize_variables()
    df.to_csv("D:/wh_conditionslong.csv", sep='\t', index=False)
    with open('d:/wh_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)

    df_no_hot = var_manager.get_variable_factors(factor_encoding="categorical")
    df_no_hot.to_csv("D:/wh_conditions_no_hot.csv", sep='\t', index=False)
    with open('d:/wh_summarylong.json', 'w') as f:
        json.dump(summary, f, indent=4)
    print("to here")
    #
    # df = var_manager.get_variable_factors(factor_encoding="categorical")
    # df.to_csv("D:/wh_conditions_direct.csv", sep='\t', index=False)

    # df = pd.read_csv(events_path, sep='\t')
    # df = df.replace('n/a', np.NaN)
    # input_data = TabularInput(df, hed_schema=hed_schema, sidecar=sidecar_path)
    # hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    # definitions = input_data.get_definitions(as_strings=False)
    # var_manager = VariableManager(hed_strings, hed_schema, definitions)
    # df = var_manager.get_variable_factors()
    # summary = var_manager.summarize_variables()
    # print("to here")
    #
    # df_factors = var_manager.get_variable_factors(factor_encoding="categorical")
    # print("to there")
    # print(conditions)
    # test_var = conditions.get_variable('var2')
    # s = test_var.get_summary()
    # print("s")
    # test_sum = test_var.get_summary()
    # print(f"{test_sum}")
    # test_lumber = conditions.get_variable('lumber')
    # test_sum_lumber = test_lumber.get_summary()
    #
    # lumber_factor = test_lumber.get_factors()
    # print(f"lumber_factor: {lumber_factor.to_string()}")
    #
    # test_fast = conditions.get_variable('fast')
    # fast_factor = test_fast.get_factors()
    # print(f"fast_factor: {fast_factor.to_string()}")
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
    # conditions = VariableManager(test_strings1, schema, defs)
    # print("to here")
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
    hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    definitions = input_data.get_definitions(as_strings=False)
    var_manager = VariableManager(hed_strings, hed_schema, definitions)

    for man_var in var_manager.variables:
        var_sum = var_manager.get_variable(man_var)
        factors = var_sum.get_factors(factor_encoding="categorical")
        s = var_sum.get_summary()
        print(json.dumps(s))
        # s = var_sum.get_summary(full=False)
        # print(json.dumps(s))
