"""
Classes to resolve ambiguities, gather, expand definitions.
"""
import pandas as pd
from hed.models.definition_dict import DefinitionDict
from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString


class AmbiguousDef:
    """ Determine whether expanded definitions are consistent. """
    def __init__(self):
        self.def_tag_name = None
        self.actual_contents = {}
        self.placeholder_defs = []
        self.matching_names = None
        self.has_errors = False

    def add_def(self, def_tag, def_expand_group):
        """ Adds a definition to this ambiguous definition.

        Parameters:
            def_tag (HedTag): The Def-expand tag representing this definition.
            def_expand_group (HedGroup): The Definition group including the tag and contents.

        Raises:
            ValueError: if this group could not match any of the other possible matches.

        """
        orig_group = def_expand_group.get_first_group()
        def_extension = def_tag.extension.split('/')[-1]
        self.actual_contents.setdefault(def_extension, []).append(orig_group)
        if self.def_tag_name is None:
            self.def_tag_name = def_tag.short_tag
        group = orig_group.copy()
        matching_tags = [tag for tag in group.get_all_tags() if
                         tag.extension == def_extension and tag.is_takes_value_tag()]
        if len(matching_tags) == 0:
            self.has_errors = True
            raise ValueError("Invalid Definition")
        matching_names = set([tag.short_base_tag for tag in matching_tags])
        if self.matching_names is not None:
            self.matching_names = self.matching_names & matching_names
        else:
            self.matching_names = matching_names
        if len(self.matching_names) == 0:
            self.has_errors = True
            raise ValueError("Invalid Definition")
        for tag in matching_tags:
            tag.extension = "#"
        self.placeholder_defs.append(group)

    def validate(self):
        """ Validate the given ambiguous definition.

        Returns:
            bool: True if this is a valid definition with exactly 1 placeholder.

        raises:
            ValueError: Raised if this is an invalid(not ambiguous) definition.
        """
        # todo: improve this and get_group
        # Check whether all of the actual items with the same key agree:
        for key, contents in self.actual_contents.items():
            sorted = contents[0].sort()
            if any(item.sort() != sorted for item in contents):
                raise ValueError('Invalid Definition')
        return True

    def get_definition_string(self):
        x = f"(Definition/{self.def_tag_name}, {str(self.placeholder_defs[0])})"
        print(x)
        return x

    @staticmethod
    def _get_matching_value(tags):
        """ Get the matching value for a set of HedTag extensions.

        Parameters:
            tags (iterator): The list of HedTags to find a matching value for.

        Returns:
            str or None: The matching value if found, None otherwise.
        """
        extensions = [tag.extension for tag in tags if tag.is_takes_value_tag()]
        unique_extensions = set(extensions)

        if len(unique_extensions) == 1:
            return unique_extensions.pop()
        elif "#" in unique_extensions:
            unique_extensions.remove("#")
            if len(unique_extensions) == 1:
                return unique_extensions.pop()
        return None



    # def get_group(self):
    #     """
    #        Return the first item if there is a matching tag value in each item or None if no match.
    #     """
    #     if len(self.placeholder_defs) == 0:
    #         return None
    #     new_group = self.placeholder_defs[0].copy()
    #     if len(self.placeholder_defs) == 1:
    #         return new_group
    #     comparison_tags = new_group.get_all_tags()
    #     all_tags_list = [group.get_all_tags() for group in self.placeholder_defs]
    #     for tags in all_tags_list:
    #         if len(tags) != len(comparison_tags):
    #             return None
    #         matching_val = self._get_matching_value(tags)
    #         if matching_val is None:
    #             return None
    #     return new_group

    # placeholder_group = self.get_group()
    # placeholder_mask = [(tag.extension == "#") for tag in placeholder_group.get_all_tags()]
    # all_tags_list = [group.get_all_tags() for group in self.actual_defs]
    # for tags, placeholder in zip(zip(*all_tags_list), placeholder_mask):
    #     if placeholder:
    #         continue
    #
    #     tag_set = set(tag.extension for tag in tags)
    #     if len(tag_set) > 1:
    #         raise ValueError("Invalid Definition")
    #
    # return placeholder_mask.count(True) == 1


class DefExpandGatherer:
    """ Gather definitions from a series of def-expands, including possibly ambiguous ones.

    Notes: The def-dict contains the known definitions. After validation, it also contains resolved definitions.
    The errors contain the definition contents that are known to be in error. The ambiguous_defs contain the defintions
    that are not able to be resolved based on the data.

    """
    def __init__(self, hed_schema, known_defs=None, ambiguous_defs=None, errors=None):
        """Initialize the DefExpandGatherer class.

        Parameters:
            hed_schema (HedSchema): The HED schema to be used for processing.
            known_defs (str or list or DefinitionDict): A dictionary of known definitions.
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
        self._validate_ambiguous()
        return self.def_dict, self.ambiguous_defs, self.errors

    def _validate_ambiguous(self):
        """ Do a final validation on each ambiguous group.

        Notes:
            If found to be invalid, the ambiguous definition contents are transferred to the errors.

        """
        for def_name in list(self.ambiguous_defs.keys()):  # Iterate over a copy of the keys
            ambiguous_def = self.ambiguous_defs.get(def_name)
            if ambiguous_def is None:
                continue
            try:
                is_resolved = ambiguous_def.validate()
                if is_resolved:
                    def_string = ambiguous_def.get_definition_string()
                    self.def_dict.add_definitions(def_string, self.hed_schema)
                    del self.ambiguous_defs[def_name]
                # if is_resolved:
                #     self.def_dict.defs[def_name] =
            except ValueError:
                contents_list = self.errors.setdefault(def_name, [])
                contents_list += ambiguous_def.actual_contents
                del self.ambiguous_defs[def_name]

    def _process_def_expand(self, string):
        """Process a single HED string to extract definitions and handle known and ambiguous definitions.

        Parameters:
            string (str): The HED string to be processed.
        """
        hed_str = HedString(string, self.hed_schema)

        for def_tag, def_expand_group, def_group in hed_str.find_def_tags(recursive=True):
            print(f"{str(def_tag)}: {str(def_expand_group)}")
            if def_tag == def_expand_group:
                continue

            if not self._handle_known_definition(def_tag, def_expand_group, def_group):
                self._handle_ambiguous_definition(def_tag, def_expand_group)

    def _handle_known_definition(self, def_tag, def_expand_group, def_group):
        """Handle known def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the entire Def-expand tag and its group.
            def_group (HedGroup): The group containing the Def-expand contents.

        Returns:
            bool: True if the def-expand tag is known and handled, False otherwise.
        """
        def_tag_name = def_tag.extension.split('/')[0]
        def_group_contents = self.def_dict._get_definition_contents(def_tag)
        def_expand_group.sort()

        # If this definition is already known, make sure it agrees.
        if def_group_contents:
            if def_group_contents != def_expand_group:
                self.errors.setdefault(def_tag_name.casefold(), []).append(def_expand_group.get_first_group())
            return True

        has_extension = "/" in def_tag.extension
        if not has_extension:
            group_tag = def_expand_group.get_first_group()
            self.def_dict.defs[def_tag_name.casefold()] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                                          takes_value=False,
                                                                          source_context=[])
            return True

        # this is needed for the cases where we have a definition with errors, but it's not a known definition.
        if def_tag_name.casefold() in self.errors:
            self.errors.setdefault(f"{def_tag_name.casefold()}", []).append(def_expand_group.get_first_group())
            return True

        return False

    def _handle_ambiguous_definition(self, def_tag, def_expand_group):
        """ Handle ambiguous def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the def-expand tag.
        """
        def_tag_name = def_tag.extension.split('/')[0]

        # Return the AmbiguousDefinition object associated with this def_tag name
        these_defs = self.ambiguous_defs.setdefault(def_tag_name.casefold(), AmbiguousDef())
        try:
            these_defs.add_def(def_tag, def_expand_group)
        except ValueError:
            self.errors.setdefault(def_tag_name.casefold(), []).append(def_expand_group)
            del self.ambiguous_defs[def_tag_name.casefold()]


    @staticmethod
    def get_ambiguous_group(ambiguous_def):
        """Turn an entry in the ambiguous_defs dict into a single HedGroup.

        Returns:
            HedGroup: The ambiguous definition with known placeholders filled in.
        """
        return ambiguous_def.get_group()
