import pandas as pd
from hed.models import DefinitionDict, DefinitionEntry, HedString


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
        self.known_defs = known_defs if known_defs else {}
        self.ambiguous_defs = ambiguous_defs if ambiguous_defs else {}
        self.errors = errors if errors else {}
        self.def_dict = DefinitionDict(self.known_defs, self.hed_schema)

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
            self._process_hed_string(string)

        return self.def_dict, self.ambiguous_defs, self.errors

    def _process_hed_string(self, string):
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
                self.errors.setdefault(def_tag_name.lower(), []).append(def_group)
            return True

        if def_tag_name.lower() in self.errors:
            self.errors.setdefault(def_tag_name.lower(), []).append(def_group)
            return True

        return False

    def _handle_ambiguous_definition(self, def_tag, def_expand_group):
        """Handle ambiguous def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the def-expand tag.
        """
        def_tag_name = def_tag.extension.split('/')[0]

        has_extension = "/" in def_tag.extension

        if not has_extension:
            group_tag = def_expand_group.get_first_group()
            self.def_dict.defs[def_tag_name.lower()] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                                       takes_value=False,
                                                                       source_context=[])
        else:
            self._process_ambiguous_extension(def_tag, def_expand_group)

    def _process_ambiguous_extension(self, def_tag, def_expand_group):
        """Process ambiguous extensions in a def-expand HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the def-expand tag.
        """
        def_tag_name = def_tag.extension.split('/')[0]
        def_extension = def_tag.extension.split('/')[-1]

        matching_tags = [tag for tag in def_expand_group.get_all_tags() if
                         tag.extension == def_extension and tag != def_tag]

        for tag in matching_tags:
            tag.extension = "#"

        group_tag = def_expand_group.get_first_group()

        these_defs = self.ambiguous_defs.setdefault(def_tag_name.lower(), [])
        these_defs.append(group_tag)

        value_per_tag = []
        if len(these_defs) >= 1:
            all_tags_list = [group.get_all_tags() for group in these_defs]
            for tags in zip(*all_tags_list):
                matching_val = self._get_matching_value(tags)
                value_per_tag.append(matching_val)

            self._handle_value_per_tag(def_tag_name, value_per_tag, group_tag)

    def _handle_value_per_tag(self, def_tag_name, value_per_tag, group_tag):
        """Handle the values per tag in ambiguous def-expand tag.

        Parameters:
            def_tag_name (str): The name of the def-expand tag.
            value_per_tag (list): The list of values per HedTag.
            group_tag (HedGroup): The def expand contents
        """
        if value_per_tag.count(None):
            groups = self.ambiguous_defs.get(def_tag_name.lower(), [])
            for group in groups:
                self.errors.setdefault(def_tag_name.lower(), []).append(group)

            del self.ambiguous_defs[def_tag_name.lower()]
            return

        ambiguous_values = value_per_tag.count("#")
        if ambiguous_values == 1:
            new_contents = group_tag.copy()
            for tag, value in zip(new_contents.get_all_tags(), value_per_tag):
                if value is not None:
                    tag.extension = f"{value}"
            self.def_dict.defs[def_tag_name.lower()] = DefinitionEntry(name=def_tag_name, contents=new_contents,
                                                                       takes_value=True,
                                                                       source_context=[])

            del self.ambiguous_defs[def_tag_name.lower()]

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
