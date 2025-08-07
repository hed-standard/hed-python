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
        self.matching_names = None
        self.resolved_definition = None

    def add_def(self, def_tag, def_expand_group):
        """ Adds a definition to this ambiguous definition.

        Parameters:
            def_tag (HedTag): The Def-expand tag representing this definition.
            def_expand_group (HedGroup): The Definition group including the tag and contents.

        Raises:
            ValueError: if this group could not match any of the other possible matches.

        """
        orig_group = def_expand_group.get_first_group()
        def_extension = def_tag.extension.split('/')
        existing_contents = self.actual_contents.get(def_extension[1], None)
        if existing_contents and existing_contents != orig_group:
            raise ValueError("Invalid Definition")
        elif existing_contents:
            return
        self.actual_contents[def_extension[1]] = orig_group.copy()
        if self.def_tag_name is None:
            self.def_tag_name = 'Definition/' + def_extension[0] + '/#'
        matching_tags = [tag for tag in orig_group.get_all_tags() if
                         tag.extension == def_extension[1] and tag.is_takes_value_tag()]
        if len(matching_tags) == 0:
            raise ValueError("Invalid Definition")
        matching_names = set([tag.short_base_tag for tag in matching_tags])
        if self.matching_names is not None:
            self.matching_names = self.matching_names & matching_names
        else:
            self.matching_names = matching_names
        if len(self.matching_names) == 0:
            raise ValueError("Invalid Definition")

    def resolve_definition(self):
        """ Try to resolve the definition based on the information available.

        Returns:
            boolean: True if successfully resolved and False if it can't be resolved from information available.

        Raises:
            ValueError: If the actual_contents conflict.

        If the definition has already been resolved, this rechecks based on the information.

        """
        tuple_list = [(key, value) for key, value in self.actual_contents.items()]
        candidate_tuple = tuple_list[0]
        candidate_contents = candidate_tuple[1].copy()
        match_tags = candidate_contents.find_tags(self.matching_names, True, include_groups=0)
        candidate_tags = []
        for tag in match_tags:
            is_match = True
            tag_extension = tag.extension
            for this_tuple in tuple_list[1:]:
                tag.extension = this_tuple[0]
                is_match = candidate_contents == this_tuple[1]
                tag.extension = tag_extension
                if not is_match:
                    break
            if is_match:
                candidate_tags.append(tag)
        if len(candidate_tags) == 1:
            candidate_tags[0].extension = '#'
            self.resolved_definition = candidate_contents
            return True
        if len(candidate_tags) == 0 or (1 < len(candidate_tags) < len(tuple_list)):
            raise ValueError("Invalid Definition")
        return False

    def get_definition_string(self):
        if self.def_tag_name is None or self.resolved_definition is None:
            return None
        return f"({self.def_tag_name}, {str(self.resolved_definition)})"


class DefExpandGatherer:
    """ Gather definitions from a series of def-expands, including possibly ambiguous ones.

    Notes: The def-dict contains the known definitions. After validation, it also contains resolved definitions.
    The errors contain the definition contents that are known to be in error. The ambiguous_defs contain the definitions
    that cannot be resolved based on the data.

    """
    def __init__(self, hed_schema, known_defs=None, ambiguous_defs=None, errors=None):
        """Initialize the DefExpandGatherer class.

        Parameters:
            hed_schema (HedSchema): The HED schema to be used for processing.
            known_defs (str or list or DefinitionDict): A dictionary of known definitions.
            ambiguous_defs (dict or None): An optional dictionary of ambiguous def-expand definitions.
            errors (dict or None): An optional dictionary to store errors keyed by definition names.

        """
        self.hed_schema = hed_schema
        self.ambiguous_defs = ambiguous_defs if ambiguous_defs else {}
        self.errors = errors if errors else {}
        self.def_dict = DefinitionDict(known_defs, self.hed_schema)

    def process_def_expands(self, hed_strings, known_defs=None) -> tuple ['DefinitionDict', dict, dict]:
        """Process the HED strings containing def-expand tags.

        Parameters:
            hed_strings (pd.Series or list): A Pandas Series or list of HED strings to be processed.
            known_defs (dict, optional): A dictionary of known definitions to be added.

        Returns:
            tuple [DefinitionDict, dict, dict]: A tuple containing the DefinitionDict, ambiguous definitions, and a
                                            dictionary of error lists keyed by definition name
        """
        if not isinstance(hed_strings, pd.Series):
            hed_strings = pd.Series(hed_strings)

        def_expand_mask = hed_strings.str.contains('Def-Expand/', case=False)

        if known_defs:
            self.def_dict.add_definitions(known_defs, self.hed_schema)
        for i in hed_strings[def_expand_mask].index:
            string = hed_strings.loc[i]
            self._process_def_expand(string)
        self._resolve_ambiguous()
        return self.def_dict, self.ambiguous_defs, self.errors

    def _process_def_expand(self, string):
        """Process a single HED string to extract definitions and handle known and ambiguous definitions.

        Parameters:
            string (str): The HED string to be processed.
        """
        hed_str = HedString(string, self.hed_schema)
        hed_str.sort()
        for def_tag, def_expand_group, def_group in hed_str.find_def_tags(recursive=True):
            if def_tag == def_expand_group:
                continue

            if not self._handle_known_definition(def_tag, def_expand_group):
                self._handle_ambiguous_definition(def_tag, def_expand_group)

    def _handle_known_definition(self, def_tag, def_expand_group):
        """Handle known def-expand tag in a HED string.

        Parameters:
            def_tag (HedTag): The def-expand tag.
            def_expand_group (HedGroup): The group containing the entire Def-expand tag and its group.

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
            errors = self.errors.setdefault(def_tag_name.casefold(), [])
            errors = errors + list(these_defs.actual_contents.values())
            self.errors[def_tag_name.casefold()] = errors
            del self.ambiguous_defs[def_tag_name.casefold()]

    def _resolve_ambiguous(self):
        """ Do a final validation on each ambiguous group.

        Notes:
            If found to be invalid, the ambiguous definition contents are transferred to the errors.

        """
        delete_list = []
        for def_name, ambiguous_def in self.ambiguous_defs.items():  # Iterate over a copy of the keys
            try:
                is_resolved = ambiguous_def.resolve_definition()
                if is_resolved:
                    def_string = ambiguous_def.get_definition_string()
                    if def_string is None:
                        return
                    self.def_dict.add_definitions(def_string, self.hed_schema)
                    delete_list.append(def_name)
            except ValueError:
                contents_list = self.errors.setdefault(def_name, [])
                contents_list += list(ambiguous_def.actual_contents.values())
                self.errors[def_name] = contents_list
                delete_list.append(def_name)

        for def_name in delete_list:
            del self.ambiguous_defs[def_name]
