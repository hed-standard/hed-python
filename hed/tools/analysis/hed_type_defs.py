""" Manager for definitions associated with a type such as condition-variable. """

from hed.models.hed_tag import HedTag
from hed.models.definition_dict import DefinitionDict


class HedTypeDefs:
    """Manager for definitions associated with a type such as condition-variable.

    Properties:
        def_map (dict):  keys are definition names, values are dict {type_values, description, tags}.

    Example: A definition 'famous-face-cond' with contents:

        '(Condition-variable/Face-type,Description/A face that should be recognized.,(Image,(Face,Famous)))'

    would have type_values ['face_type'].  All items are strings not objects.


    """
    def __init__(self, definitions, type_tag='condition-variable'):
        """ Create a definition manager for a type of variable.

        Parameters:
            definitions (dict or DefinitionDict): A dictionary of DefinitionEntry objects.
            type_tag (str): Lower-case HED tag string representing the type managed.

        """

        self.type_tag = type_tag.casefold()
        if isinstance(definitions, DefinitionDict):
            self.definitions = definitions.defs
        elif isinstance(definitions, dict):
            self.definitions = definitions
        else:
            self.definitions = {}
        self.def_map = self._extract_def_map()  # dict def names vs {description, tags, type_values}
        self.type_map = self._extract_type_map()  # Dictionary of type_values vs dict definition names

    def get_type_values(self, item):
        """ Return a list of type_tag values in item.

        Parameters:
            item (HedTag, HedGroup, or HedString): An item potentially containing def tags.

        Returns:
            list:  A list of the unique values associated with this type

        """
        def_names = self.extract_def_names(item, no_value=True)
        type_values = []
        for def_name in def_names:
            values = self.def_map.get(def_name.casefold(), {})
            if "type_values" in values:
                type_values = type_values + values["type_values"]
        return type_values

    @property
    def type_def_names(self):
        """ Return list of names of definition that have this type-variable.

        Returns:
            list:  definition names that have this type.

        """
        return list(self.def_map.keys())

    @property
    def type_names(self):
        """ Return list of names of the type-variables associated with type definitions.

        Returns:
            list:  type names associated with the type definitions

        """
        return list(self.type_map.keys())

    def _extract_def_map(self):
        """ Extract type_variables associated with each definition and add them to def_map. """
        def_map = {}
        for entry in self.definitions.values():
            type_def, type_values, description, other_tags = self._extract_entry_values(entry)
            if type_def:
                def_map[type_def.casefold()] = \
                    {'def_name': type_def, 'type_values': type_values, 'description': description, 'tags': other_tags}
        return def_map

    def _extract_type_map(self):
        """ Extract the definitions associated with each type value and add them to the dictionary. """

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
        type_values = []
        type_def = ""
        description = ''
        other_tags = []
        for hed_tag in tag_list:
            if hed_tag.short_base_tag == 'Description':
                description = hed_tag.extension
            elif hed_tag.short_base_tag.casefold() != self.type_tag:
                other_tags.append(hed_tag.short_base_tag)
            else:
                type_values.append(hed_tag.extension.casefold())
                type_def = entry.name
        return type_def, type_values, description, other_tags

    @staticmethod
    def extract_def_names(item, no_value=True):
        """ Return a list of Def values in item.

           Parameters:
               item (HedTag, HedGroup, or HedString): An item containing a def tag.
               no_value (bool):  If True, strip off extra values after the definition name.

           Returns:
               list:  A list of definition names (as strings).

           """
        if isinstance(item, HedTag) and 'def' in item.tag_terms:
            names = [item.extension.casefold()]
        else:
            names = [tag.extension.casefold() for tag in item.get_all_tags() if 'def' in tag.tag_terms]
        if no_value:
            for index, name in enumerate(names):
                name, name_value = HedTypeDefs.split_name(name)
                names[index] = name
        return names

    @staticmethod
    def split_name(name, lowercase=True):
        """ Split a name/# or name/x into name, x.

        Parameters:
            name (str):  The extension or value portion of a tag.
            lowercase (bool): If True (default), return values are converted to lowercase.

        Returns:
            tuple[str, str]:
            - Name of the definition.
            - Value of the definition if it has one.

        """
        if not name:
            return None, None
        parts = name.split('/', 1)
        def_name = parts[0]
        def_value = ''
        if len(parts) > 1:
            def_value = parts[1]
        if lowercase:
            return def_name.casefold(), def_value.casefold()
        else:
            return def_name, def_value
