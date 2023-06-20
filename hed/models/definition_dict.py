from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString
from hed.errors.error_types import DefinitionErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.model_constants import DefTagNames
from hed.schema.hed_schema_constants import HedKey


class DefinitionDict:
    """ Gathers definitions from a single source.

    """

    def __init__(self, def_dicts=None, hed_schema=None):
        """ Definitions to be considered a single source. 
            
        Parameters:
            def_dicts (str or list or DefinitionDict): DefDict or list of DefDicts/strings or 
                a single string whose definitions should be added.
            hed_schema(HedSchema or None): Required if passing strings or lists of strings, unused otherwise.

        :raises TypeError:
            - Bad type passed as def_dicts
        """

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
            
        :raises TypeError:
            - Bad type passed as def_dicts
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
                raise TypeError("Invalid type '{type(def_dict)}' passed to DefinitionDict")

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
        for def_tag, def_value in def_dict.items():
            self._add_definition(def_tag, def_value)

    def get(self, def_name):
        """ Get the definition entry for the definition name.

            Not case-sensitive

        Parameters:
            def_name (str):  Name of the definition to retrieve.

        Returns:
            DefinitionEntry:  Definition entry for the requested definition.
        """
        return self.defs.get(def_name.lower())

    def __iter__(self):
        return iter(self.defs)

    def __len__(self):
        return len(self.defs)

    def items(self):
        """ Returns the dictionary of definitions

            Alias for .defs.items()

        Returns:
            def_entries({str: DefinitionEntry}): A list of definitions
        """
        return self.defs.items()

    @property
    def issues(self):
        """Returns issues about duplicate definitions."""
        return self._issues

    def check_for_definitions(self, hed_string_obj, error_handler=None):
        """ Check string for definition tags, adding them to self.

        Parameters:
            hed_string_obj (HedString): A single hed string to gather definitions from.
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list:  List of issues encountered in checking for definitions. Each issue is a dictionary.
        """
        def_issues = []
        for definition_tag, group in hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY}):
            group_tag, new_def_issues = self._find_group(definition_tag, group, error_handler)
            def_tag_name = definition_tag.extension

            def_takes_value = def_tag_name.lower().endswith("/#")
            if def_takes_value:
                def_tag_name = def_tag_name[:-len("/#")]

            def_tag_lower = def_tag_name.lower()
            if "/" in def_tag_lower or "#" in def_tag_lower:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                         tag=definition_tag,
                                                                         def_name=def_tag_name)

            if new_def_issues:
                def_issues += new_def_issues
                continue

            new_def_issues += self._validate_contents(definition_tag, group_tag, error_handler)
            new_def_issues += self._validate_placeholders(def_tag_name, group_tag, def_takes_value, error_handler)

            if new_def_issues:
                def_issues += new_def_issues
                continue

            if error_handler:
                context = error_handler.get_error_context_copy()
            else:
                context = []
            if def_tag_lower in self.defs:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.DUPLICATE_DEFINITION,
                                                                         def_name=def_tag_name)
                def_issues += new_def_issues
                continue
            self.defs[def_tag_lower] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                       takes_value=def_takes_value,
                                                       source_context=context)

        return def_issues

    def _validate_placeholders(self, def_tag_name, group, def_takes_value, error_handler):
        new_issues = []
        placeholder_tags = []
        tags_with_issues = []
        if group:
            for tag in group.get_all_tags():
                count = str(tag).count("#")
                if count:
                    placeholder_tags.append(tag)
                if count > 1:
                    tags_with_issues.append(tag)

        if tags_with_issues:
            new_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                 DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                 def_name=def_tag_name,
                                                                 tag_list=tags_with_issues,
                                                                 expected_count=1 if def_takes_value else 0)

        if (len(placeholder_tags) == 1) != def_takes_value:
            new_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                 DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                 def_name=def_tag_name,
                                                                 tag_list=placeholder_tags,
                                                                 expected_count=1 if def_takes_value else 0)
            return new_issues

        if def_takes_value:
            placeholder_tag = placeholder_tags[0]
            if not placeholder_tag.is_takes_value_tag():
                new_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                     DefinitionErrors.PLACEHOLDER_NO_TAKES_VALUE,
                                                                     def_name=def_tag_name,
                                                                     placeholder_tag=placeholder_tag)

        return new_issues

    def _find_group(self, definition_tag, group, error_handler):
        # initial validation
        groups = group.groups()
        issues = []
        if len(groups) > 1:
            issues += \
                ErrorHandler.format_error_with_context(error_handler,
                                                       DefinitionErrors.WRONG_NUMBER_GROUPS,
                                                       def_name=definition_tag.extension, tag_list=groups)
        elif len(groups) == 0:
            issues += \
                ErrorHandler.format_error_with_context(error_handler,
                                                       DefinitionErrors.NO_DEFINITION_CONTENTS,
                                                       def_name=definition_tag.extension)
        if len(group.tags()) != 1:
            issues += \
                ErrorHandler.format_error_with_context(error_handler,
                                                       DefinitionErrors.WRONG_NUMBER_TAGS,
                                                       def_name=definition_tag.extension,
                                                       tag_list=[tag for tag in group.tags()
                                                                 if tag is not definition_tag])

        group_tag = groups[0] if groups else None

        return group_tag, issues

    def _validate_contents(self, definition_tag, group, error_handler):
        issues = []
        if group:
            def_keys = {DefTagNames.DEF_KEY, DefTagNames.DEF_EXPAND_KEY, DefTagNames.DEFINITION_KEY}
            for def_tag in group.find_tags(def_keys, recursive=True, include_groups=0):
                issues += ErrorHandler.format_error_with_context(error_handler,
                                                                 DefinitionErrors.DEF_TAG_IN_DEFINITION,
                                                                 tag=def_tag,
                                                                 def_name=definition_tag.extension)

            for tag in group.get_all_tags():
                if tag.has_attribute(HedKey.Unique) or tag.has_attribute(HedKey.Required):
                    issues += ErrorHandler.format_error_with_context(error_handler,
                                                                     DefinitionErrors.BAD_PROP_IN_DEFINITION,
                                                                     tag=tag,
                                                                     def_name=definition_tag.extension)

        return issues

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
            save_parent = hed_tag._parent
            def_contents = self._get_definition_contents(hed_tag)
            hed_tag._parent = save_parent
            if def_contents is not None:
                hed_tag._expandable = def_contents
                hed_tag._expanded = hed_tag.short_base_tag == DefTagNames.DEF_EXPAND_ORG_KEY

    def _get_definition_contents(self, def_tag):
        """ Get the contents for a given def tag.

            Does not validate at all.

        Parameters:
            def_tag (HedTag): Source hed tag that may be a Def or Def-expand tag.

        Returns:
            def_contents: HedGroup
            The contents to replace the previous def-tag with.
        """
        is_label_tag = def_tag.extension
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
