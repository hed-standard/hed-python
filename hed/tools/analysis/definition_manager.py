from hed.schema import load_schema_version
from hed.models import HedString, HedTag, DefinitionEntry
from hed.tools.analysis.hed_context_manager import HedContextManager


class DefinitionManager:

    def __init__(self, definitions, hed_schema, variable_type='condition-variable'):
        """ Create a definition manager for a type of variable.

        Args:
            definitions (dict): A dictionary of DefinitionEntry objects.
            hed_schema (Hedschema or HedSchemaGroup): The schema used for parsing.
            variable_type (str): Lower-case string giving the type of HED variable.

        """

        self.variable_type = variable_type.lower()
        self.hed_schema = hed_schema
        self.definitions = definitions
        self.variable_map = {}   # maps def names to conditions.
        self._extract_variable_map()

    def get_vars(self, item):
        """ Return a list of type_variables in item.

        Args:
            item (HedTag, HedGroup, or HedString): An item potentially containing def tags.

        Returns:
            list:

        """
        def_names = self.get_def_names(item, no_value=True)
        var_list = []
        for def_name in def_names:
            hed_vars = self.variable_map.get(def_name.lower(), None)
            if hed_vars:
                var_list = var_list + hed_vars
        return var_list

    def _extract_variable_map(self):
        """ Extract all of the type_variables associated with each definition and add them to the dictionary. """
        self.variable_map = {}
        for entry in self.definitions.values():
            self.variable_map[entry.name.lower()] = self._extract_from_entry(entry)

    def _extract_from_entry(self, entry):
        """ Extract a list of type_variables associated with a definition.

        Args:
            entry (DictionaryEntry): A definition entry to be processed.

        Returns:
            A list of type_variables associated with this definition.


        """
        tag_list = entry.contents.get_all_tags()
        hed_vars = []
        for hed_tag in tag_list:
            hed_tag.convert_to_canonical_forms(self.hed_schema)
            if hed_tag.short_base_tag.lower() != self.variable_type:
                continue
            value = hed_tag.extension_or_value_portion.lower()
            if value:
                hed_vars.append(value)
            else:
                hed_vars.append(entry.name)
        return hed_vars

    @staticmethod
    def get_def_names(item, no_value=True):
        """ Return a list of Def values in item.

        Args:
            item (HedTag, HedGroup, or HedString): An item containing a def tag.
            no_value (bool):  If True, strip off extra values after the definition name.

        Returns:
            list:  A list of definition names (as strings).

        """
        if isinstance(item, HedTag) and 'def' in item.tag_terms:
            names = [item.extension_or_value_portion.lower()]
        else:
            names = [tag.extension_or_value_portion.lower() for tag in item.get_all_tags() if 'def' in tag.tag_terms]
        if no_value:
            for index, name in enumerate(names):
                name, name_value = DefinitionManager.split_name(name)
                names[index] = name
        return names

    @staticmethod
    def split_name(name, lowercase=True):
        """ Split a name/# or name/x into name, x.

        Args:
            name (str):  The extension or value portion of a tag
            lowercase (bool): If True

        Returns:
            tuple:  (name, value)

        """
        if not name:
            return None, None
        parts = name.split('/', 1)
        def_name = parts[0]
        def_value = ''
        if len(parts) > 1:
            def_value = parts[1]
        if lowercase:
            return def_name.lower(), def_value.lower()
        else:
            return def_name, def_value

    @staticmethod
    def remove_defs(hed_strings):
        """ This removes any def or Def-expand from a list of HedStrings.

        Args:
            hed_strings (list):  A list of HedStrings

        Returns:
            list: A list of the removed Defs.

        """
        def_groups = [0] * len(hed_strings)
        for i in range(len(hed_strings)):
            def_groups[i] = []
        for i, hed in enumerate(hed_strings):
            def_groups[i] = DefinitionManager.extract_defs(hed)
        return def_groups

    @staticmethod
    def extract_defs(hed):
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
    test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                               f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=schema),
                     HedString('(Def/Cond1, Offset)', hed_schema=schema),
                     HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast', hed_schema=schema),
                     HedString('', hed_schema=schema),
                     HedString('(Def/Cond2, Onset)', hed_schema=schema),
                     HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                     HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]

    onset_man = HedContextManager(test_strings1, schema)
    def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
    def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
    def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
                     hed_schema=schema)
    def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
    definitions = {'cond1': DefinitionEntry('Cond1', def1, False, None),
                   'cond2': DefinitionEntry('Cond2', def2, False, None),
                   'cond3': DefinitionEntry('Cond3', def3, True, None),
                   'cond4': DefinitionEntry('Cond4', def4, False, None)}
    def_man = DefinitionManager(definitions, schema)
    a = def_man.get_def_names(HedTag('Def/Cond3/4', hed_schema=schema))
    b = def_man.get_def_names(HedString('(Def/Cond3/5,(Red, Blue))', hed_schema=schema))
    c = def_man.get_def_names(HedString('(Def/Cond3/6,(Red, Blue, Def/Cond1), Def/Cond2)', hed_schema=schema))
