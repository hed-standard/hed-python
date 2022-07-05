from hed.errors import HedFileError
from hed.schema import load_schema_version
from hed.models import HedString, HedTag, HedGroup, DefinitionEntry
from hed.tools.analysis.onset_manager import OnsetManager


class ConditionVariable:
    def __init__(self, name):
        self.name = name
        self.levels = {}
        self.direct = []
        self.def_entries = {}

    def __str__(self):
        return f"{self.name}:{self.levels} levels {len(self.direct)} references"


class ConditionManager:

    def __init__(self, hed_strings, hed_schema, definitions):
        """ Create a condition manager for an events file.

        Args:
            hed_strings (list): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup):
            definitions (dict): A dictionary of DefinitionEntry objects

        """

        self.hed_schema = hed_schema
        self.definitions = definitions
        self.condition_variables = {}
        onset_manager = OnsetManager(hed_strings, hed_schema)
        self.hed_strings = onset_manager.hed_strings
        self.event_contexts = onset_manager.event_contexts
        self.def_groups = []   # List same length as hed_strings with def's removed from hed_string
        self.def_map = {}      # Key is def name and value is list of condition variables
        self._extract_def_groups()
        self._extract_direct_conditions()
        self._extract_definitions()
        self._extract_def_conditions()

    def _extract_definitions(self):
        """ Extract all of the condition variables associated with a definition and add them to the dictionary. """
        self.def_map = {}
        for entry in self.definitions.values():
            self.def_map[entry.name.lower()] = []
            cond_vars = self._extract_definition_entry(entry)
            for cond in cond_vars:
                if cond.lower() in self.condition_variables:
                    vars = self.condition_variables[cond.lower()]
                else:
                    vars = ConditionVariable(cond)
                vars.def_entries[entry.name.lower()] = entry
                self.condition_variables[cond.lower()] = vars
                self.def_map[entry.name.lower()].append(vars)

    def _extract_definition_entry(self, defin):
        """ Extract a list of condition variables associated with a definition.

        Args:
            defin (DictionaryEntry): A definition entry to be processed.

        Returns:
            A list of condition variables associated with this definition.


        """
        tags = [HedTag(tag, hed_schema=self.hed_schema) for tag in defin.tag_dict.keys()]
        condvars = []
        for hed_tag in tags:
            if hed_tag.short_base_tag.lower() != 'condition-variable':
                continue
            value = defin.tag_dict[hed_tag.org_tag]
            if value:
                condvars = list(value.keys())
            else:
                condvars = [defin.name]
        return condvars

    def _extract_def_conditions(self):
        for index, def_item in enumerate(self.def_groups):
            def_cond_list = self._extract_cond_list(def_item) # list of Def/xxx in this def_item
            for def_cond in def_cond_list:
                key = def_cond.extension_or_value_portion.lower()
                parts = key.split('/', 1)
                keypart = key[0]
                for cond_val in self.def_map[key]:
                    cond_name = cond_val.name.lower()
                    if cond_name not in self.condition_variables:
                        self.condition_variables[cond_name] = ConditionVariable(cond_val)
                    levels = self.condition_variables[cond_name].levels
                    if key not in levels:
                        levels[key] = [index]
                    else:
                        levels[key].append(index)
            print(f"{index}: {str(def_item)}  {str(def_cond_list)}")

    def _extract_cond_list(self, def_item):
        """ Extract an items in the definition groups.

        Args:
            def_item (list): A list of HedTag or HedGroup items containing a condition variable

        Returns:
            list:  List of condition variable names

        """
        cond_list = []
        for item in def_item:
            if isinstance(item, HedTag):
                cond_list.append(item)
            elif isinstance(item, HedGroup):
                cond_list = cond_list + item.find_def_tags(recursive=True, include_groups=0)
        return cond_list

    def _extract_direct_conditions(self):
        """ Extract the condition variables that appear outside of definitions. """
        for index, hed in enumerate(self.hed_strings):
            tuples = hed.find_tags_with_term("condition-variable", recursive=True, include_groups=2)
            for tup in tuples:
                name = tup[0].extension_or_value_portion
                cond_var = self.condition_variables.get(name.lower(), None)
                if cond_var is None:
                    cond_var = ConditionVariable(name)
                self.condition_variables[name.lower()] = cond_var
                cond_var.direct.append(index)

    def _extract_level_conditions(self):
        print("to here")

    def _extract_def_groups(self):
        """ Removes any def or def-expand group from hed strings and puts in def groups.

        Notes: In addition to initializing def_groups, this method removes these groups from hed_string

        """
        def_groups = [0] * len(self.hed_strings)
        for i in range(len(self.hed_strings)):
            def_groups[i] = []
        for i, hed in enumerate(self.hed_strings):
            def_groups[i] = self._extract_event_defs(hed)
        self.def_groups = def_groups

    @staticmethod
    def _extract_event_defs(hed):
        to_remove = []
        to_append = []
        tups = hed.find_def_tags(recursive=True, include_groups=3)
        for tup in tups:
            if len(tup[2].children) == 1:
                to_append.append(tup[0])
            else:
                to_append.append(tup[2])
            to_remove.append(tup[2])
        hed.remove(to_remove)
        return to_append


if __name__ == '__main__':
    schema = load_schema_version(xml_version="8.1.0")
    test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                               hed_schema=schema),
                     HedString('(Def/Cond1, Offset)', hed_schema=schema),
                     HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast', hed_schema=schema),
                     HedString('', hed_schema=schema),
                     HedString('(Def/Cond2, Onset)', hed_schema=schema),
                     HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                     HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]

    onset_man = OnsetManager(test_strings1, schema)
    def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
    def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
    def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)', hed_schema=schema)
    def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
    defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
            'Cond2': DefinitionEntry('Cond2', def2, False, None),
            'Cond3': DefinitionEntry('Cond3', def3, True, None),
            'Cond4': DefinitionEntry('Cond4', def4, False, None)}
    conditions = ConditionManager(test_strings1, schema, defs)
    print("to Here")