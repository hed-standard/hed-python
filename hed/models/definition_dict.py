from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString
from hed.errors.error_types import DefinitionErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.model_constants import DefTagNames


class DefinitionDict:
    """ Gathers definitions from a single source.

    """

    def __init__(self, def_dicts=None, hed_schema=None):
        """ Definitions to be considered a single source. """

        self.defs = {}
        self._label_tag_name = DefTagNames.DEF_KEY
        self._issues = []
        if def_dicts:
            self.add_definitions(def_dicts, hed_schema)

    def add_definitions(self, def_dicts, hed_schema=None):
        """ Add definitions from dict(s) to this dict.

        Parameters:
            def_dicts (list or DefinitionDict): DefDict or list of DefDicts/strings whose definitions should be added.
            hed_schema(HedSchema or None): Required if passing strings or lists of strings, unused otherwise.
        """
        if not isinstance(def_dicts, list):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            if isinstance(def_dict, DefinitionDict):
                self._add_definitions_from_dict(def_dict)
            elif isinstance(def_dict, str) and hed_schema:
                self.check_for_definitions(HedString(def_dict, hed_schema))
            elif isinstance(def_dict, list) and hed_schema:
                for definition in def_dict:
                    self.check_for_definitions(HedString(definition, hed_schema))
            else:
                print(f"Invalid input type '{type(def_dict)} passed to DefDict.  Skipping.")

    def _add_definition(self, def_tag, def_value):
        if def_tag in self.defs:
            error_context = self.defs[def_tag].source_context
            self._issues += ErrorHandler.format_error_from_context(DefinitionErrors.DUPLICATE_DEFINITION,
                                                                   error_context=error_context, def_name=def_tag)
        else:
            self.defs[def_tag] = def_value

    def _add_definitions_from_dict(self, def_dict):
        """ Add the definitions found in the given definition dictionary to this mapper.

         Parameters:
             def_dict (DefinitionDict): DefDict whose definitions should be added.

        """
        for def_tag, def_value in def_dict:
            self._add_definition(def_tag, def_value)

    def get(self, def_name):
        return self.defs.get(def_name.lower())

    def __iter__(self):
        return iter(self.defs.items())

    @property
    def issues(self):
        """Returns issues about duplicate definitions."""
        return self._issues

    def get_def_entry(self, def_name):
        """ Get the definition entry for the definition name.

        Parameters:
            def_name (str):  Name of the definition to retrieve.

        Returns:
            DefinitionEntry:  Definition entry for the requested definition.

        """

        return self.defs.get(def_name.lower())

    def check_for_definitions(self, hed_string_obj, error_handler=None):
        """ Check string for definition tags, adding them to self.

        Parameters:
            hed_string_obj (HedString): A single hed string to gather definitions from.
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list:  List of issues encountered in checking for definitions. Each issue is a dictionary.

        """
        new_def_issues = []
        for definition_tag, group in hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY}):
            def_tag_name = definition_tag.extension_or_value_portion

            # initial validation
            groups = group.groups()
            if len(groups) > 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                           def_name=def_tag_name, tag_list=groups)
                continue
            if len(group.tags()) != 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                           def_name=def_tag_name,
                                                           tag_list=[tag for tag in group.tags()
                                                                     if tag is not definition_tag])
                continue

            group_tag = groups[0] if groups else None

            # final validation
            # Verify no other def or def expand tags found in group
            if group_tag:
                for def_tag in group.find_def_tags(recursive=True, include_groups=0):
                    new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                             DefinitionErrors.DEF_TAG_IN_DEFINITION,
                                                                             tag=def_tag,
                                                                             def_name=def_tag_name)
                    continue
            def_takes_value = def_tag_name.lower().endswith("/#")
            if def_takes_value:
                def_tag_name = def_tag_name[:-len("/#")]

            def_tag_lower = def_tag_name.lower()
            if "/" in def_tag_lower or "#" in def_tag_lower:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                         def_name=def_tag_name)
                continue

            # # Verify placeholders here.
            placeholder_tags = []
            if group_tag:
                for tag in group_tag.get_all_tags():
                    if "#" in str(tag):
                        placeholder_tags.append(tag)

            if (len(placeholder_tags) == 1) != def_takes_value:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                         def_name=def_tag_name,
                                                                         tag_list=placeholder_tags,
                                                                         expected_count=1 if def_takes_value else 0)
                continue

            if error_handler:
                context = error_handler.get_error_context_copy()
            else:
                context = []
            if def_tag_lower in self.defs:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.DUPLICATE_DEFINITION,
                                                                         def_name=def_tag_name)
                continue
            self.defs[def_tag_lower] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                       takes_value=def_takes_value,
                                                       source_context=context)

        return new_def_issues

    def construct_def_tags(self, hed_string_obj):
        """ Identify def/def-expand tag contents in the given string.

        Parameters:
            hed_string_obj(HedString): The hed string to identify definition contents in
        """
        for def_tag, def_expand_group, def_group in hed_string_obj.find_def_tags(recursive=True):
            def_contents = self._get_definition_contents(def_tag)
            if def_contents is not None:
                def_tag._expandable = def_contents
                def_tag._expanded = def_tag != def_expand_group

    def construct_def_tag(self, hed_tag):
        """ Identify def/def-expand tag contents in the given HedTag.

        Parameters:
            hed_tag(HedTag): The hed tag to identify definition contents in
        """
        if hed_tag.short_base_tag in {DefTagNames.DEF_ORG_KEY, DefTagNames.DEF_EXPAND_ORG_KEY}:
            def_contents = self._get_definition_contents(hed_tag)
            if def_contents is not None:
                hed_tag._expandable = def_contents
                hed_tag._expanded = hed_tag.short_base_tag == DefTagNames.DEF_EXPAND_ORG_KEY

    def expand_def_tags(self, hed_string_obj):
        """ Expands def tags to def-expand tags.

        Parameters:
            hed_string_obj (HedString): The hed string to process.
        """
        # First see if the "def" is found at all.  This covers def and def-expand.
        hed_string_lower = hed_string_obj.lower()
        if self._label_tag_name not in hed_string_lower:
            return []

        def_issues = []
        # We need to check for labels to expand in ALL groups
        for def_tag, def_group in hed_string_obj.find_tags(DefTagNames.DEF_KEY, recursive=True):
            def_contents = self._get_definition_contents(def_tag)
            if def_contents is not None:
                def_tag.short_base_tag = DefTagNames.DEF_EXPAND_ORG_KEY
                def_group.replace(def_tag, def_contents)

        return def_issues

    def _get_definition_contents(self, def_tag):
        """ Get the contents for a given def tag.

            Does not validate at all.

        Parameters:
            def_tag (HedTag): Source hed tag that may be a Def or Def-expand tag.

        Returns:
            def_contents: HedGroup
            The contents to replace the previous def-tag with.
        """
        is_label_tag = def_tag.extension_or_value_portion
        placeholder = None
        found_slash = is_label_tag.find("/")
        if found_slash != -1:
            placeholder = is_label_tag[found_slash + 1:]
            is_label_tag = is_label_tag[:found_slash]

        label_tag_lower = is_label_tag.lower()
        def_entry = self.defs.get(label_tag_lower)
        if def_entry is None:
            # Could raise an error here?
            return None
        else:
            def_tag_name, def_contents = def_entry.get_definition(def_tag, placeholder_value=placeholder)
            if def_tag_name:
                return def_contents

        return None

    @staticmethod
    def get_as_strings(def_dict):
        """ Convert the entries to strings of the contents

        Parameters:
            def_dict(DefinitionDict or dict): A dict of definitions

        Returns:
            dict(str: str): definition name and contents
        """
        if isinstance(def_dict, DefinitionDict):
            def_dict = def_dict.defs

        return {key: str(value.contents) for key, value in def_dict.items()}
