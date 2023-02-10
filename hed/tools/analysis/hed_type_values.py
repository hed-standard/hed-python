""" Manages a type variable and its associated context. """

import pandas as pd
from hed.models.hed_tag import HedTag
from hed.models.hed_group import HedGroup
from hed.tools.analysis.hed_type_definitions import HedTypeDefinitions
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.hed_type_factors import HedTypeFactors


class HedTypeValues:

    def __init__(self, context_manager, definitions, name, type_tag="condition-variable"):
        """ Create a variable manager for one type-variable for one tabular file.

        Parameters:
            context_manager (HedContextManager): A list of HED strings.
            definitions (dict): A dictionary of DefinitionEntry objects.
            name (str): Name of the tabular file as a unique identifier.
            type_tag (str): Lowercase short form of the tag to be managed.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.

        """
        self.name = name
        self.type_tag = type_tag.lower()
        self.definitions = HedTypeDefinitions(definitions, context_manager.hed_schema, type_tag=type_tag)
        hed_strings = context_manager.hed_strings
        hed_contexts = context_manager.contexts
        self.total_events = len(hed_strings)
        self._type_value_map = {}
        self._extract_variables(hed_strings, hed_contexts)

    def get_type_value_factors(self, type_value):
        """ Return the HedTypeFactors associated with type_name or None.

        Parameters:
            type_value (str): The tag corresponding to the type's value (such as the name of the condition variable).

        Returns:
            HedTypeFactors or None

        """
        return self._type_value_map.get(type_value.lower(), None)

    def get_type_value_level_info(self, type_value):
        """ Return type variable corresponding to type_value.

        Parameters:
            type_value (str) - name of the type variable

        Returns:


        """
        return self._type_value_map.get(type_value, None)

    @property
    def type_variables(self):
        return set(self._type_value_map.keys())

    def get_type_def_names(self):
        """ Return the definitions """
        tag_list = []
        for variable, factor in self._type_value_map.items():
            tag_list = tag_list + [key for key in factor.levels.keys()]
        return list(set(tag_list))

    def get_type_value_names(self):
        return list(self._type_value_map.keys())

    def get_summary(self):
        var_summary = self._type_value_map.copy()
        summary = {}
        for var_name, var_sum in var_summary.items():
            summary[var_name] = var_sum.get_summary()
        return summary

    def get_type_factors(self, type_values=None, factor_encoding="one-hot"):
        """ Create a dataframe with the indicated type tag values as factors.

        Parameters:
            type_values (list or None): A list of values of type tags for which to generate factors.
            factor_encoding (str):      Type of factor encoding (one-hot or categorical).

        Returns:
            DataFrame:  Contains the specified factors associated with this type tag.


        """
        if type_values is None:
            type_values = self.get_type_value_names()
        df_list = []
        for index, type_value in enumerate(type_values):
            var_sum = self._type_value_map.get(type_value, None)
            if not var_sum:
                continue
            df_list.append(var_sum.get_factors(factor_encoding=factor_encoding))
        if not df_list:
            return None
        else:
            return pd.concat(df_list, axis=1)

    def __str__(self):
        return f"{self.type_tag} type_variables: {str(list(self._type_value_map.keys()))}"

    def _extract_definition_variables(self, item, index):
        """ Extract the definition uses from a HedTag, HedGroup, or HedString.

        Parameters:
            item (HedTag, HedGroup, or HedString): The item to extract variable information from.
            index (int):  Position of this item in the object's hed_strings.

        Notes:
            This updates the HedTypeFactors information.

        """

        if isinstance(item, HedTag):
            tags = [item]
        else:
            tags = item.get_all_tags()
        for tag in tags:
            if tag.short_base_tag.lower() != "def":
                continue
            hed_vars = self.definitions.get_type_values(tag)
            if not hed_vars:
                continue
            self._update_definition_variables(tag, hed_vars, index)

    def _update_definition_variables(self, tag, hed_vars, index):
        """Update the HedTypeFactors map with information from Def tag.

        Parameters:
            tag (HedTag): A HedTag that is a Def tag.
            hed_vars (list): A list of names of the hed type_variables
            index (ind):  The event number associated with this.

        Notes:
            This modifies the HedTypeFactors map.

        """
        level = tag.extension_or_value_portion.lower()
        for var_name in hed_vars:
            hed_var = self._type_value_map.get(var_name, None)
            if hed_var is None:
                hed_var = HedTypeFactors(self.type_tag, var_name, self.total_events)
                self._type_value_map[var_name] = hed_var
            var_levels = hed_var.levels.get(level, {index: 0})
            var_levels[index] = 0
            hed_var.levels[level] = var_levels

    def _extract_variables(self, hed_strings, hed_contexts):
        """ Extract all type_variables from hed_strings and event_contexts. """
        for index, hed in enumerate(hed_strings):
            self._extract_direct_variables(hed, index)
            self._extract_definition_variables(hed, index)

            self._extract_direct_variables(hed_contexts[index], index)
            self._extract_definition_variables(hed_contexts[index], index)

    def _extract_direct_variables(self, item, index):
        """ Extract the condition type_variables from a HedTag, HedGroup, or HedString.

        Parameters:
            item (HedTag or HedGroup): The item from which to extract condition type_variables.
            index (int):  Position in the array.

        """
        if isinstance(item, HedTag) and item.short_base_tag.lower() == self.type_tag:
            tag_list = [item]
        elif isinstance(item, HedGroup) and item.children:
            tag_list = item.find_tags_with_term(self.type_tag, recursive=True, include_groups=0)
        else:
            tag_list = []
        self._update_variables(tag_list, index)

    def _update_variables(self, tag_list, index):
        """ Update the HedTypeFactors based on tags in the list.

        Parameters:
            tag_list (list): A list of Condition-variable HedTags.
            index (int):  An integer representing the position in an array

        """
        for tag in tag_list:
            tag_value = tag.extension_or_value_portion.lower()
            if not tag_value:
                tag_value = self.type_tag
            hed_var = self._type_value_map.get(tag_value, None)
            if hed_var is None:
                hed_var = HedTypeFactors(self.type_tag, tag_value, self.total_events)
            self._type_value_map[tag_value] = hed_var
            hed_var.direct_indices[index] = ''


# if __name__ == '__main__':
#     import os
#     from hed import Sidecar, TabularInput, HedString
#     from hed.models import DefinitionEntry
#     from hed.tools.analysis.analysis_util import get_assembled_strings
#     hed_schema = load_schema_version(xml_version="8.1.0")
#     test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
#                                f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=hed_schema),
#                      HedString('(Def/Cond1, Offset)', hed_schema=hed_schema),
#                      HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
#                                hed_schema=hed_schema),
#                      HedString('', hed_schema=hed_schema),
#                      HedString('(Def/Cond2, Onset)', hed_schema=hed_schema),
#                      HedString('(Def/Cond3/4.3, Onset)', hed_schema=hed_schema),
#                      HedString('Arm, Leg, Condition-variable/Fast, Def/Cond6/7.2', hed_schema=hed_schema)]
#
#     test_strings2 = [HedString(f"Def/Cond2, Def/Cond6/4, Def/Cond6/7.8, Def/Cond6/Alpha", hed_schema=hed_schema),
#                      HedString("Yellow", hed_schema=hed_schema),
#                      HedString("Def/Cond2", hed_schema=hed_schema),
#                      HedString("Def/Cond2, Def/Cond6/5.2", hed_schema=hed_schema)]
#     test_strings3 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
#                                hed_schema=hed_schema),
#                      HedString("Yellow", hed_schema=hed_schema),
#                      HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=hed_schema),
#                      HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=hed_schema),
#                      HedString("Def/Cond2, Def/Cond6/4", hed_schema=hed_schema)]
#     def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=hed_schema)
#     def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=hed_schema)
#     def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
#                      hed_schema=hed_schema)
#     def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=hed_schema)
#     def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=hed_schema)
#     def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=hed_schema)
#     defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
#             'Cond2': DefinitionEntry('Cond2', def2, False, None),
#             'Cond3': DefinitionEntry('Cond3', def3, True, None),
#             'Cond4': DefinitionEntry('Cond4', def4, False, None),
#             'Cond5': DefinitionEntry('Cond5', def5, False, None),
#             'Cond6': DefinitionEntry('Cond6', def6, True, None)
#             }
#
#     conditions1 = HedTypeValues(HedContextManager(test_strings1), hed_schema, defs)
#     conditions2 = HedTypeValues(HedContextManager(test_strings2), hed_schema, defs)
#     conditions3 = HedTypeValues(HedContextManager(test_strings3), hed_schema, defs)
#     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#                                                    '../../../tests/data/bids_tests/eeg_ds003645s_hed'))
#     events_path = os.path.realpath(os.path.join(bids_root_path,
#                                                 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
#     sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
#     sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
#     input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
#     hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
#     onset_man = HedContextManager(hed_strings)
#     definitions = input_data.get_definitions().gathered_defs
#     var_type = HedTypeValues(onset_man, hed_schema, definitions)
#     df = var_type.get_type_factors()
#     summary = var_type.get_summary()
#     df.to_csv("D:/wh_conditionslong.csv", sep='\t', index=False)
#     with open('d:/wh_summary.json', 'w') as f:
#         json.dump(summary, f, indent=4)
#
#     df_no_hot = var_type.get_type_factors(factor_encoding="categorical")
#     df_no_hot.to_csv("D:/wh_conditions_no_hot.csv", sep='\t', index=False)
#     with open('d:/wh_summarylong.json', 'w') as f:
#         json.dump(summary, f, indent=4)
