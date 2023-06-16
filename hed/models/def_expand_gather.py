import pandas as pd
from hed.models.definition_dict import DefinitionDict
from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString


class AmbiguousDef:
    def __init__(self):
        self.actual_defs = []
        self.placeholder_defs = []

    def add_def(self, def_tag, def_expand_group):
        group_tag = def_expand_group.get_first_group()
        def_extension = def_tag.extension.split('/')[-1]
        self.actual_defs.append(group_tag)
        group_tag = group_tag.copy()
        matching_tags = [tag for tag in group_tag.get_all_tags() if
                         tag.extension == def_extension]

        for tag in matching_tags:
            tag.extension = "#"
        self.placeholder_defs.append(group_tag)

    def validate(self):
        """Validate the given ambiguous definition

        Returns:
            bool: True if this is a valid definition with exactly 1 placeholder.

        raises:
            ValueError: Raised if this is an invalid(not ambiguous) definition.
        """
        # todo: improve this and get_group
        placeholder_group = self.get_group()
        if not placeholder_group:
            raise ValueError("Invalid Definition")
        placeholder_mask = [(tag.extension == "#") for tag in placeholder_group.get_all_tags()]
        all_tags_list = [group.get_all_tags() for group in self.actual_defs]
        for tags, placeholder in zip(zip(*all_tags_list), placeholder_mask):
            if placeholder:
                continue

            tag_set = set(tag.extension for tag in tags)
            if len(tag_set) > 1:
                raise ValueError("Invalid Definition")

        return placeholder_mask.count(True) == 1

    @staticmethod
    def _get_matching_value(tags):
        """Get the matching value for a set of HedTag extensions.

        Parameters:
            tags (iterator): The list of HedTags to find a matching value for.

        Returns:
            str or None: The matching value if found, None otherwise.
        """
        extensions = [tag.extension for tag in tags]
        unique_extensions = set(extensions)

        if len(unique_extensions) == 1:
            return unique_extensions.pop()
        elif "#" in unique_extensions:
            unique_extensions.remove("#")
            if len(unique_extensions) == 1:
                return unique_extensions.pop()
        return None

    def get_group(self):
        new_group = self.placeholder_defs[0].copy()

        all_tags_list = [group.get_all_tags() for group in self.placeholder_defs]
        for tags, new_tag in zip(zip(*all_tags_list), new_group.get_all_tags()):
            matching_val = self._get_matching_value(tags)
            if matching_val is None:
                return None
            new_tag.extension = matching_val

        return new_group


class DefExpandGatherer:
    """Class for gathering definitions from a series of def-expands, including possibly ambiguous ones"""
    def __init__(self, hed_schema, known_defs=None, ambiguous_defs=None, errors=None):
        """Initialize the DefExpandGatherer class.

        Parameters:
            hed_schema (HedSchema): The HED schema to be used for processing.
            known_defs (dict, optional): A dictionary of known definitions.
            ambiguous_defs (dict, optional): A dictionary of ambiguous def-expand definitions.

        """
        self.hed_schema = hed_schema
        self.ambiguous_defs = ambiguous_defs if ambiguous_defs else {}
        self.errors = errors if errors else {}
        self.def_dict = DefinitionDict(known_defs, self.hed_schema)

    def process_def_expands(self, hed_strings, known_defs=None):
        """Process the HED strings containing def-expand tags.

        Parameters:
            hed_strings (pd.Series or list): A Pandas Series or list of HED strings to be processed.
            known_defs (dict, optional): A dictionary of known definitions to be added.

        Returns:
            tuple: A tuple containing the DefinitionDict, ambiguous definitions, and errors.
        """
        if not isinstance(hed_strings, pd.Series):
            hed_strings = pd.Series(hed_strings)

        def_expand_mask = hed_strings.str.contains('Def-Expand/', case=False)

        if known_defs:
            self.def_dict.add_definitions(known_defs, self.hed_schema)
        for i in hed_strings[def_expand_mask].index:
            string = hed_strings.loc[i]
            self._process_def_expand(string)

        return self.def_dict, self.ambiguous_defs, self.errors

    def _process_def_expand(self, string):
        """Process a single HED string to extract definitions and handle known and ambiguous definitions.

        Parameters:
            string (str): The HED string to be processed.
        """
        hed_str = HedString(string, self.hed_schema)

        for def_tag, def_expand_group, def_group in hed_str.find_def_tags(recursive=True):
            if def_tag == def_expand_group:
                continue

            if not self._handle_known_definition(def_tag, def_expand_group, def_group):
                self._handle_ambiguous_definition(def_tag, def_expand_group)

    def _handle_known_definition(self, def_tag, def_expand_group, def_group):
        """Handle known def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the def-expand tag.
            def_group (HedGroup): The group containing the def-expand group.

        Returns:
            bool: True if the def-expand tag is known and handled, False otherwise.
        """
        def_tag_name = def_tag.extension.split('/')[0]
        def_group_contents = self.def_dict._get_definition_contents(def_tag)
        def_expand_group.sort()

        if def_group_contents:
            if def_group_contents != def_expand_group:
                self.errors.setdefault(def_tag_name.lower(), []).append(def_expand_group.get_first_group())
            return True

        has_extension = "/" in def_tag.extension
        if not has_extension:
            group_tag = def_expand_group.get_first_group()
            self.def_dict.defs[def_tag_name.lower()] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                                       takes_value=False,
                                                                       source_context=[])
            return True

        # this is needed for the cases where we have a definition with errors, but it's not a known definition.
        if def_tag_name.lower() in self.errors:
            self.errors.setdefault(f"{def_tag_name.lower()}", []).append(def_expand_group.get_first_group())
            return True

        return False

    def _handle_ambiguous_definition(self, def_tag, def_expand_group):
        """Handle ambiguous def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the def-expand tag.
        """
        def_tag_name = def_tag.extension.split('/')[0]
        these_defs = self.ambiguous_defs.setdefault(def_tag_name.lower(), AmbiguousDef())
        these_defs.add_def(def_tag, def_expand_group)

        try:
            if these_defs.validate():
                new_contents = these_defs.get_group()
                self.def_dict.defs[def_tag_name.lower()] = DefinitionEntry(name=def_tag_name, contents=new_contents,
                                                                           takes_value=True,
                                                                           source_context=[])
                del self.ambiguous_defs[def_tag_name.lower()]
        except ValueError as e:
            for ambiguous_def in these_defs.placeholder_defs:
                self.errors.setdefault(def_tag_name.lower(), []).append(ambiguous_def)
            del self.ambiguous_defs[def_tag_name.lower()]

        return

    @staticmethod
    def get_ambiguous_group(ambiguous_def):
        """Turns an entry in the ambiguous_defs dict into a single HedGroup

        Returns:
            HedGroup: the ambiguous definition with known placeholders filled in
        """
        if not ambiguous_def:
            # mostly to not crash, this shouldn't happen.
            return HedString("")
        return ambiguous_def.get_group()
