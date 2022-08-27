import pandas as pd
import json
from hed.schema import load_schema_version
from hed.models import DefMapper
from hed.tools.analysis.hed_type_variable import HedTypeVariable
from hed.tools.analysis.hed_context_manager import HedContextManager


class HedVariableManager:

    def __init__(self, hed_strings, hed_schema, def_mapper):
        """ Create a variable manager for an events file.

        Args:
            hed_strings (list): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use for processing.
            def_mapper (DefMapper): A dictionary of DefinitionEntry objects.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.
        """

        self.hed_schema = hed_schema
        self.def_mapper = def_mapper
        self.context_manager = HedContextManager(hed_strings, hed_schema)
        self._variable_type_map = {}   # a map of type variable into HedTypeVariable objects

    @property
    def type_variables(self):
        return list(self._variable_type_map.keys())

    def add_type_variable(self, type_name):
        if type_name.lower() in self._variable_type_map:
            return
        self._variable_type_map[type_name.lower()] = HedTypeVariable(self.context_manager, self.hed_schema,
                                                                     self.def_mapper.gathered_defs,
                                                                     variable_type=type_name)

    def get_factor_vectors(self, type_name, type_variables=None, factor_encoding="one-hot"):
        this_map = self.get_type_variable_map(type_name)
        if this_map is None:
            return None
        variables = this_map.get_variable_names()
        if variables is None:
            variables = type_variables
        df_list = [0]*len(variables)
        for index, variable in enumerate(variables):
            var_sum = this_map._variable_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        return pd.concat(df_list, axis=1)

    def get_type_variable_map(self, type_name):
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

    # def _extract_definition_variables(self, item, index):
    #     """ Extract the definition uses from a HedTag, HedGroup, or HedString.
    #
    #     Args:
    #         item (HedTag, HedGroup, or HedString): The item to extract variable information from.
    #         index (int):  Position of this item in the object's hed_strings.
    #
    #     Notes:
    #         This updates the HedTypeFactors information.
    #
    #     """
    #
    #     if isinstance(item, HedTag):
    #         tags = [item]
    #     else:
    #         tags = item.get_all_tags()
    #     for tag in tags:
    #         if tag.short_base_tag.lower() != "def":
    #             continue
    #         hed_vars = self.definitions.get_vars(tag)
    #         if not hed_vars:
    #             continue
    #         self._update_definition_variables(tag, hed_vars, index)
    #
    # def _update_definition_variables(self, tag, hed_vars, index):
    #     """Update the HedTypeFactors map with information from Def tag.
    #
    #     Args:
    #         tag (HedTag): A HedTag that is a Def tag.
    #         hed_vars (list): A list of names of the hed type_variables
    #         index (ind):  The event number associated with this.
    #
    #     Notes:
    #         This modifies the HedTypeFactors map.
    #
    #     """
    #     level = tag.extension_or_value_portion.lower()
    #     for var_name in hed_vars:
    #         hed_var = self._variable_map.get(var_name, None)
    #         if hed_var is None:
    #             hed_var = HedTypeFactors(var_name, len(self.hed_strings))
    #             self._variable_map[var_name] = hed_var
    #         var_levels = hed_var.levels.get(level, {index: 0})
    #         var_levels[index] = 0
    #         hed_var.levels[level] = var_levels
    #
    # def _extract_variables(self):
    #     """ Extract all condition type_variables from hed_strings and event_contexts. """
    #     for index, hed in enumerate(self.hed_strings):
    #         self._extract_direct_variables(hed, index)
    #         self._extract_definition_variables(hed, index)
    #         for item in self._contexts[index]:
    #             self._extract_direct_variables(item, index)
    #             self._extract_definition_variables(item, index)
    #
    # def _extract_direct_variables(self, item, index):
    #     """ Extract the condition type_variables from a HedTag, HedGroup, or HedString.
    #
    #     Args:
    #         item (HedTag or HedGroup): The item from which to extract condition type_variables.
    #         index (int):  Position in the array.
    #
    #     """
    #     if isinstance(item, HedTag) and item.short_base_tag.lower() == self.variable_type:
    #         tag_list = [item]
    #     elif isinstance(item, HedGroup) and item.children:
    #         tag_list = item.find_tags_with_term(self.variable_type, recursive=True, include_groups=0)
    #     else:
    #         tag_list = []
    #     self._update_variables(tag_list, index)
    #
    # def _update_variables(self, tag_list, index):
    #     """ Update the HedTypeFactors based on tags in the list.
    #
    #     Args:
    #         tag_list (list): A list of Condition-variable HedTags.
    #         index (int):  An integer representing the position in an array
    #
    #     """
    #     for tag in tag_list:
    #         name = tag.extension_or_value_portion.lower()
    #         if not name:
    #             name = self.variable_type
    #         hed_var = self._variable_map.get(name, None)
    #         if hed_var is None:
    #             hed_var = HedTypeFactors(name, len(self.hed_strings))
    #         self._variable_map[name] = hed_var
    #         hed_var.direct_indices[index] = ''


if __name__ == '__main__':
    import os
    from hed import Sidecar, TabularInput, HedString
    from hed.models import DefinitionEntry
    from hed.tools.analysis.analysis_util import get_assembled_strings
    hed_schema = load_schema_version(xml_version="8.1.0")

    bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   '../../../tests/data/bids/eeg_ds003654s_hed'))
    events_path = os.path.realpath(os.path.join(bids_root_path,
                                                'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    def_mapper = input_data.get_definitions()
    var_manager = HedVariableManager(hed_strings, hed_schema, def_mapper)
    var_manager.add_type_variable("condition-variable")
    var_type = var_manager.get_type_variable("condition-variable")
    summary = var_type.summarize_variables()
    with open('d:/wh_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    df = var_type.get_variable_factors()
    df.to_csv("D:/wh_conditionslong.csv", sep='\t', index=False)
    df_no_hot = var_type.get_variable_factors(factor_encoding="categorical")
    df_no_hot.to_csv("D:/wh_conditions_no_hot.csv", sep='\t', index=False)
    with open('d:/wh_summarylong.json', 'w') as f:
        json.dump(summary, f, indent=4)
    summary_total = var_manager.summarize_all()
    print("to here")
    #
    # df = var_manager.get_variable_factors(factor_encoding="categorical")
    # df.to_csv("D:/wh_conditions_direct.csv", sep='\t', index=False)

    # df = pd.read_csv(events_path, sep='\t')
    # df = df.replace('n/a', np.NaN)
    # input_data = TabularInput(df, hed_schema=hed_schema, sidecar=sidecar_path)
    # hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    # definitions = input_data.get_definitions(as_strings=False)
    # var_manager = HedVariableManager(hed_strings, hed_schema, definitions)
    # df = var_manager.get_variable_factors()
    # summary = var_manager.summarize()
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
    # conditions = HedVariableManager(test_strings1, schema, defs)
    # print("to here")
    # for man_var in conditions.type_variables:
    #     var_sum = conditions.get_variable(man_var)
    #     s = var_sum.get_summary()
    #     print(json.dumps(s))
    #     s = var_sum.get_summary(full=False)
    #     print(json.dumps(s))

    # bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                                                '../../../tests/data/bids/eeg_ds003654s_hed'))
    # events_path = os.path.realpath(os.path.join(bids_root_path,
    #                                             'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    # sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    # sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    # input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    # hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    # definitions = input_data.get_definitions(as_strings=False)
    # var_manager = HedVariableManager(hed_strings, hed_schema, definitions)
    #
    # for man_var in var_manager.type_variables:
    #     var_sum = var_manager.get_variable(man_var)
    #     factors = var_sum.get_factors(factor_encoding="categorical")
    #     s = var_sum.get_summary()
    #     print(json.dumps(s))
    #     # s = var_sum.get_summary(full=False)
    #     # print(json.dumps(s))
    # list1 = conditions1.get_variable_tags()
    # print(f"List1: {str(list1)}")
    # list2 = conditions2.get_variable_tags()
    # print(f"List2: {str(list2)}")
    # list3 = conditions2.get_variable_tags()
    # print(f"List3: {str(list3)}")

    # test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
    #                            f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=hed_schema),
    #                  HedString('(Def/Cond1, Offset)', hed_schema=hed_schema),
    #                  HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
    #                            hed_schema=hed_schema),
    #                  HedString('', hed_schema=hed_schema),
    #                  HedString('(Def/Cond2, Onset)', hed_schema=hed_schema),
    #                  HedString('(Def/Cond3/4.3, Onset)', hed_schema=hed_schema),
    #                  HedString('Arm, Leg, Condition-variable/Fast, Def/Cond6/7.2', hed_schema=hed_schema)]
    #
    # test_strings2 = [HedString(f"Def/Cond2, Def/Cond6/4, Def/Cond6/7.8, Def/Cond6/Alpha", hed_schema=hed_schema),
    #                  HedString("Yellow", hed_schema=hed_schema),
    #                  HedString("Def/Cond2", hed_schema=hed_schema),
    #                  HedString("Def/Cond2, Def/Cond6/5.2", hed_schema=hed_schema)]
    # test_strings3 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
    #                            hed_schema=hed_schema),
    #                  HedString("Yellow", hed_schema=hed_schema),
    #                  HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=hed_schema),
    #                  HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=hed_schema),
    #                  HedString("Def/Cond2, Def/Cond6/4", hed_schema=hed_schema)]
    # def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=hed_schema)
    # def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=hed_schema)
    # def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
    #                  hed_schema=hed_schema)
    # def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=hed_schema)
    # def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=hed_schema)
    # def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=hed_schema)
    # defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
    #         'Cond2': DefinitionEntry('Cond2', def2, False, None),
    #         'Cond3': DefinitionEntry('Cond3', def3, True, None),
    #         'Cond4': DefinitionEntry('Cond4', def4, False, None),
    #         'Cond5': DefinitionEntry('Cond5', def5, False, None),
    #         'Cond6': DefinitionEntry('Cond6', def6, True, None)
    #         }
    #
    # conditions1 = HedVariableManager(test_strings1, hed_schema, defs)
    # conditions2 = HedVariableManager(test_strings2, hed_schema, defs)
    # conditions3 = HedVariableManager(test_strings3, hed_schema, defs)
