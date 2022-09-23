import json
import pandas as pd

from hed.models.hed_tag import HedTag
from hed.models.hed_group import HedGroup
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_definition_manager import HedDefinitionManager
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.hed_type_factors import HedTypeFactors


class HedTypeVariable:

    def __init__(self, context_manager, hed_schema, hed_definitions, variable_type="condition-variable"):
        """ Create a variable manager for one type-variable for one tabular file.

        Args:
            context_manager (HedContextManager): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use for processing.
            hed_definitions (dict): A dictionary of DefinitionEntry objects.
            variable_type (str): Lowercase short form of the variable to be managed.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.
        """

        self.variable_type = variable_type.lower()
        self.definitions = HedDefinitionManager(hed_definitions, hed_schema, variable_type=variable_type)
        hed_strings = context_manager.hed_strings
        hed_contexts = context_manager.contexts
        self.number_events = len(hed_strings)
        self._variable_map = {}
        self._extract_variables(hed_strings, hed_contexts)

    def get_variable(self, var_name):
        """ Return the HedTypeFactors associated with var_name or None. """
        return self._variable_map.get(var_name, None)

    @property
    def type_variables(self):
        return set(self._variable_map.keys())

    def get_variable_def_names(self):
        tag_list = []
        for variable, factor in self._variable_map.items():
            tag_list = tag_list + [key for key in factor.levels.keys()]
        return list(set(tag_list))

    def get_variable_type_map(self, type_name):
        return self._variable_map.get(type_name.lower(), None)

    def get_variable_names(self):
        return list(self._variable_map.keys())

    def summarize(self, as_json=False):
        summary = self._variable_map.copy()
        for var_name, var_sum in summary.items():
            summary[var_name] = var_sum.get_summary()
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def get_variable_factors(self, variables=None, factor_encoding="one-hot"):
        if variables is None:
            variables = self.get_variable_names()
        df_list = [0]*len(variables)
        for index, variable in enumerate(variables):
            var_sum = self._variable_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        return pd.concat(df_list, axis=1)

    def __str__(self):
        return f"{self.variable_type} type_variables: {str(list(self._variable_map.keys()))}"

    def _extract_definition_variables(self, item, index):
        """ Extract the definition uses from a HedTag, HedGroup, or HedString.

        Args:
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
            hed_vars = self.definitions.get_vars(tag)
            if not hed_vars:
                continue
            self._update_definition_variables(tag, hed_vars, index)

    def _update_definition_variables(self, tag, hed_vars, index):
        """Update the HedTypeFactors map with information from Def tag.

        Args:
            tag (HedTag): A HedTag that is a Def tag.
            hed_vars (list): A list of names of the hed type_variables
            index (ind):  The event number associated with this.

        Notes:
            This modifies the HedTypeFactors map.

        """
        level = tag.extension_or_value_portion.lower()
        for var_name in hed_vars:
            hed_var = self._variable_map.get(var_name, None)
            if hed_var is None:
                hed_var = HedTypeFactors(var_name, self.number_events)
                self._variable_map[var_name] = hed_var
            var_levels = hed_var.levels.get(level, {index: 0})
            var_levels[index] = 0
            hed_var.levels[level] = var_levels

    def _extract_variables(self, hed_strings, hed_contexts):
        """ Extract all condition type_variables from hed_strings and event_contexts. """
        for index, hed in enumerate(hed_strings):
            self._extract_direct_variables(hed, index)
            self._extract_definition_variables(hed, index)
            for item in hed_contexts[index]:
                self._extract_direct_variables(item, index)
                self._extract_definition_variables(item, index)

    def _extract_direct_variables(self, item, index):
        """ Extract the condition type_variables from a HedTag, HedGroup, or HedString.

        Args:
            item (HedTag or HedGroup): The item from which to extract condition type_variables.
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
        """ Update the HedTypeFactors based on tags in the list.

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
                hed_var = HedTypeFactors(name, self.number_events)
            self._variable_map[name] = hed_var
            hed_var.direct_indices[index] = ''


if __name__ == '__main__':
    import os
    from hed import Sidecar, TabularInput, HedString
    from hed.models import DefinitionEntry
    from hed.tools.analysis.analysis_util import get_assembled_strings
    hed_schema = load_schema_version(xml_version="8.1.0")
    test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                               f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=hed_schema),
                     HedString('(Def/Cond1, Offset)', hed_schema=hed_schema),
                     HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                               hed_schema=hed_schema),
                     HedString('', hed_schema=hed_schema),
                     HedString('(Def/Cond2, Onset)', hed_schema=hed_schema),
                     HedString('(Def/Cond3/4.3, Onset)', hed_schema=hed_schema),
                     HedString('Arm, Leg, Condition-variable/Fast, Def/Cond6/7.2', hed_schema=hed_schema)]

    test_strings2 = [HedString(f"Def/Cond2, Def/Cond6/4, Def/Cond6/7.8, Def/Cond6/Alpha", hed_schema=hed_schema),
                     HedString("Yellow", hed_schema=hed_schema),
                     HedString("Def/Cond2", hed_schema=hed_schema),
                     HedString("Def/Cond2, Def/Cond6/5.2", hed_schema=hed_schema)]
    test_strings3 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                               hed_schema=hed_schema),
                     HedString("Yellow", hed_schema=hed_schema),
                     HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=hed_schema),
                     HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=hed_schema),
                     HedString("Def/Cond2, Def/Cond6/4", hed_schema=hed_schema)]
    def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=hed_schema)
    def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=hed_schema)
    def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
                     hed_schema=hed_schema)
    def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=hed_schema)
    def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=hed_schema)
    def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=hed_schema)
    defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
            'Cond2': DefinitionEntry('Cond2', def2, False, None),
            'Cond3': DefinitionEntry('Cond3', def3, True, None),
            'Cond4': DefinitionEntry('Cond4', def4, False, None),
            'Cond5': DefinitionEntry('Cond5', def5, False, None),
            'Cond6': DefinitionEntry('Cond6', def6, True, None)
            }

    conditions1 = HedTypeVariable(HedContextManager(test_strings1, hed_schema), hed_schema, defs)
    conditions2 = HedTypeVariable(HedContextManager(test_strings2, hed_schema), hed_schema, defs)
    conditions3 = HedTypeVariable(HedContextManager(test_strings3, hed_schema), hed_schema, defs)
    bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   '../../../tests/data/bids/eeg_ds003654s_hed'))
    events_path = os.path.realpath(os.path.join(bids_root_path,
                                                'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
    sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
    hed_strings = get_assembled_strings(input_data, hed_schema=hed_schema, expand_defs=False)
    onset_man = HedContextManager(hed_strings, hed_schema=hed_schema)
    definitions = input_data.get_definitions().gathered_defs
    var_type = HedTypeVariable(onset_man, hed_schema, definitions)
    df = var_type.get_variable_factors()
    summary = var_type.summarize()
    df.to_csv("D:/wh_conditionslong.csv", sep='\t', index=False)
    with open('d:/wh_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)

    df_no_hot = var_type.get_variable_factors(factor_encoding="categorical")
    df_no_hot.to_csv("D:/wh_conditions_no_hot.csv", sep='\t', index=False)
    with open('d:/wh_summarylong.json', 'w') as f:
        json.dump(summary, f, indent=4)
