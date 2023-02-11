""" Manages definitions associated with a type such as condition-variable. """

from hed.models.hed_tag import HedTag
from hed.models.def_mapper import DefMapper


class HedTypeDefinitions:

    def __init__(self, definitions, hed_schema, type_tag='condition-variable'):
        """ Create a definition manager for a type of variable.

        Parameters:
            definitions (dict or DefMapper): A dictionary of DefinitionEntry objects.
            hed_schema (Hedschema or HedSchemaGroup): The schema used for parsing.
            type_tag (str): Lower-case HED tag string representing the type managed.

        """

        self.type_tag = type_tag.lower()
        self.hed_schema = hed_schema
        if isinstance(definitions, DefMapper):
            self.definitions = definitions.gathered_defs
        elif isinstance(definitions, dict):
            self.definitions = definitions
        else:
            self.definitions = {}
        self.def_map = self._extract_def_map()   # maps def names to conditions.
        self.type_map = self._extract_type_map()

    def get_type_values(self, item):
        """ Return a list of type_tag values in item.

        Parameters:
            item (HedTag, HedGroup, or HedString): An item potentially containing def tags.

        Returns:
            list:  A list of the unique values associated with this type

        """
        def_names = self.get_def_names(item, no_value=True)
        type_tag_values = []
        for def_name in def_names:
            values = self.def_map.get(def_name.lower(), None)
            if values and values["type_values"]:
                type_tag_values = type_tag_values + values["type_values"]
        return type_tag_values

    def _extract_def_map(self):
        """ Extract all of the type_variables associated with each definition and add them to def_map. """
        def_map = {}
        for entry in self.definitions.values():
            type_values, description, other_tags = self._extract_entry_values(entry)
            def_map[entry.name.lower()] = \
                {'type_values': type_values, 'description': description, 'tags': other_tags}
        return def_map

    def _extract_type_map(self):
        """ Extract all of the definitions associated with each type value and add them to the dictionary. """

        type_map = {}
        for def_name, def_values in self.def_map.items():
            if not def_values['type_values']:
                continue
            for type_value in def_values['type_values']:
                this_map = type_map.get(type_value, {})
                this_map[def_name] = ''
                type_map[type_value] = this_map
        return type_map

    def _extract_entry_values(self, entry):
        """ Extract a list of type_variables associated with a definition.

        Parameters:
            entry (DictionaryEntry): A definition entry to be processed.

        Returns:
            list: A list of type_variables associated with this definition.
            str:  The contents of a description tag if any.



        """
        tag_list = entry.contents.get_all_tags()
        type_tag_values = []
        description = ''
        other_tags = []
        for hed_tag in tag_list:
            hed_tag.convert_to_canonical_forms(self.hed_schema)
            if hed_tag.short_base_tag.lower() == 'description':
                description = hed_tag.extension_or_value_portion
            elif hed_tag.short_base_tag.lower() != self.type_tag:
                other_tags.append(hed_tag.short_base_tag)
            else:
                value = hed_tag.extension_or_value_portion.lower()
                if value:
                    type_tag_values.append(value)
                else:
                    type_tag_values.append(entry.name)
        return type_tag_values, description, other_tags

    @staticmethod
    def get_def_names(item, no_value=True):
        """ Return a list of Def values in item.

           Parameters:
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
                name, name_value = HedTypeDefinitions.split_name(name)
                names[index] = name
        return names

    @staticmethod
    def split_name(name, lowercase=True):
        """ Split a name/# or name/x into name, x.

        Parameters:
            name (str):  The extension or value portion of a tag
            lowercase (bool): If True

        Returns:
            str:   name of the definition
            str:   value of the definition if it has one

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
