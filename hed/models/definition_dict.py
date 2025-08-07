""" Definition handler class. """
from typing import Union

from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString
from hed.errors.error_types import DefinitionErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.model_constants import DefTagNames
from hed.schema.hed_schema_constants import HedKey


class DefinitionDict:
    """ Gathers definitions from a single source. """

    def __init__(self, def_dicts=None, hed_schema=None):
        """ Definitions to be considered a single source.

        Parameters:
            def_dicts (str or list or DefinitionDict): DefDict or list of DefDicts/strings or
                a single string whose definitions should be added.
            hed_schema (HedSchema or None): Required if passing strings or lists of strings, unused otherwise.

        Raises:
             TypeError: Bad type passed as def_dicts.
        """

        self.defs = {}
        self._issues = []
        if def_dicts:
            self.add_definitions(def_dicts, hed_schema)

    def add_definitions(self, def_dicts, hed_schema=None):
        """ Add definitions from dict(s) or strings(s) to this dict.

        Parameters:
            def_dicts (list, DefinitionDict, dict, or str): DefinitionDict or list of DefinitionDicts/strings/dicts
                                                            whose definitions should be added.
            hed_schema (HedSchema or None): Required if passing strings or lists of strings, unused otherwise.

        Note - dict form expects DefinitionEntries in the same form as a DefinitionDict
                Note - str or list of strings will parse the strings using the hed_schema.
                Note - You can mix and match types, eg [DefinitionDict, str, list of str] would be valid input.

        Raises:
             TypeError: Bad type passed as def_dicts.
        """
        if not isinstance(def_dicts, list):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            if isinstance(def_dict, (DefinitionDict, dict)):
                self._add_definitions_from_dict(def_dict)
            elif isinstance(def_dict, str) and hed_schema:
                self.check_for_definitions(HedString(def_dict, hed_schema))
            elif isinstance(def_dict, list) and hed_schema:
                for definition in def_dict:
                    self.check_for_definitions(HedString(definition, hed_schema))
            else:
                raise TypeError(f"Invalid type '{type(def_dict)}' passed to DefinitionDict")

    def _add_definition(self, def_tag, def_value):
        if def_tag in self.defs:
            error_context = self.defs[def_tag].source_context
            self._issues += ErrorHandler.format_error_from_context(DefinitionErrors.DUPLICATE_DEFINITION,
                error_context=error_context, def_name=def_tag, actual_error=DefinitionErrors.DUPLICATE_DEFINITION)
        else:
            self.defs[def_tag] = def_value

    def _add_definitions_from_dict(self, def_dict):
        """ Add the definitions found in the given definition dictionary to this mapper.

         Parameters:
             def_dict (DefinitionDict or dict): DefDict whose definitions should be added.

        """
        for def_tag, def_value in def_dict.items():
            self._add_definition(def_tag, def_value)

    def get(self, def_name) -> Union[DefinitionEntry, None]:
        """ Get the definition entry for the definition name.

            Not case-sensitive

        Parameters:
            def_name (str):  Name of the definition to retrieve.

        Returns:
            Union[DefinitionEntry, None]:  Definition entry for the requested definition.
        """
        return self.defs.get(def_name.casefold())

    def __iter__(self):
        return iter(self.defs)

    def __len__(self):
        return len(self.defs)

    def items(self):
        """ Return the dictionary of definitions.

            Alias for .defs.items()

        Returns:
            def_entries({str: DefinitionEntry}): A list of definitions.
        """
        return self.defs.items()

    @property
    def issues(self):
        """Return issues about duplicate definitions."""
        return self._issues

    def check_for_definitions(self, hed_string_obj, error_handler=None) -> list[dict]:
        """ Check string for definition tags, adding them to self.

        Parameters:
            hed_string_obj (HedString): A single HED string to gather definitions from.
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list[dict]:  List of issues encountered in checking for definitions. Each issue is a dictionary.
        """
        def_issues = []
        for definition_tag, group in hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY}):
            group_tag, new_def_issues = self._find_group(definition_tag, group, error_handler)
            def_tag_name, def_takes_value = self._strip_value_placeholder(definition_tag.extension)

            if "/" in def_tag_name or "#" in def_tag_name:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                         tag=definition_tag,
                                                                         def_name=def_tag_name)

            if new_def_issues:
                def_issues += new_def_issues
                continue

            new_def_issues = self._validate_contents(definition_tag, group_tag, error_handler)
            new_def_issues += self._validate_placeholders(def_tag_name, group_tag, def_takes_value, error_handler)

            if new_def_issues:
                def_issues += new_def_issues
                continue

            new_def_issues, context = self._validate_name_and_context(def_tag_name, error_handler)
            if new_def_issues:
                def_issues += new_def_issues
                continue

            self.defs[def_tag_name.casefold()] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                                 takes_value=def_takes_value,
                                                                 source_context=context)

        return def_issues

    @staticmethod
    def _strip_value_placeholder(def_tag_name):
        def_takes_value = def_tag_name.endswith("/#")
        if def_takes_value:
            def_tag_name = def_tag_name[:-len("/#")]
        return def_tag_name, def_takes_value

    def _validate_name_and_context(self, def_tag_name, error_handler):
        if error_handler:
            context = error_handler.error_context
        else:
            context = []
        new_def_issues = []
        if def_tag_name.casefold() in self.defs:
            new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                     DefinitionErrors.DUPLICATE_DEFINITION,
                                                                     def_name=def_tag_name)
        return new_def_issues, context

    @staticmethod
    def _validate_placeholders(def_tag_name, group, def_takes_value, error_handler):
        """ Check the definition for the correct placeholders (exactly 1 placeholder when takes value).

        Parameters:
            def_tag_name (str): The name of the definition without any Definition tag or value.
            group (HedGroup): The contents of the definition.
            def_takes_value (bool): True if the definition takes a value (should have #).
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list:  List of issues encountered in checking for definitions. Each issue is a dictionary.

        """
        new_issues = []
        placeholder_tags = []
        tags_with_issues = []

        # Find the tags that have # in their strings and return issues of count > 1.
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
        # Make sure placeholder count is correct.
        if (len(placeholder_tags) == 1) != def_takes_value:
            new_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                 DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                 def_name=def_tag_name,
                                                                 tag_list=placeholder_tags,
                                                                 expected_count=1 if def_takes_value else 0)
            return new_issues

        # Make sure that the tag with the placeholder is allowed to take a value.
        if def_takes_value:
            placeholder_tag = placeholder_tags[0]
            if not placeholder_tag.is_takes_value_tag():
                new_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                     DefinitionErrors.PLACEHOLDER_NO_TAKES_VALUE,
                                                                     def_name=def_tag_name,
                                                                     placeholder_tag=placeholder_tag)

        return new_issues

    @staticmethod
    def _find_group(definition_tag, group, error_handler):
        """ Check the definition for the correct placeholders (exactly 1 placeholder when takes value).

        Parameters:
            definition_tag (HedTag): The Definition tag itself.
            group (HedGroup): The entire definition group include the Definition tag.
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list:  List of issues encountered in checking for definitions. Each issue is a dictionary.

        """
        # initial validation
        groups = group.groups()
        issues = []
        if len(groups) > 1:
            issues += \
                ErrorHandler.format_error_with_context(error_handler,
                                                       DefinitionErrors.WRONG_NUMBER_GROUPS,
                                                       def_name=definition_tag.extension, tag_list=groups)
        elif len(groups) == 0 and '#' in definition_tag.extension:
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

    @staticmethod
    def _validate_contents(definition_tag, group, error_handler):
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

    def get_definition_entry(self, def_tag):
        """ Get the entry for a given def tag.

            Does not validate at all.

        Parameters:
            def_tag (HedTag): Source HED tag that may be a Def or Def-expand tag.

        Returns:
            def_entry(DefinitionEntry or None): The definition entry if it exists
        """
        tag_label, _, placeholder = def_tag.extension.partition('/')

        label_tag_lower = tag_label.casefold()
        def_entry = self.defs.get(label_tag_lower)
        return def_entry

    def _get_definition_contents(self, def_tag):
        """ Get the contents for a given def tag.

            Does not validate at all.

        Parameters:
            def_tag (HedTag): Source HED tag that may be a Def or Def-expand tag.

        Returns:
            HedGroup: The contents to replace the previous def-tag with.
        """
        tag_label, _, placeholder = def_tag.extension.partition('/')

        label_tag_lower = tag_label.casefold()
        def_entry = self.defs.get(label_tag_lower)
        if def_entry is None:
            # Could raise an error here?
            return None

        def_contents = def_entry.get_definition(def_tag, placeholder_value=placeholder)
        return def_contents

    @staticmethod
    def get_as_strings(def_dict) -> dict[str, str]:
        """ Convert the entries to strings of the contents

        Parameters:
            def_dict (dict): A dict of definitions

        Returns:
            dict[str,str]: Definition name and contents
        """
        if isinstance(def_dict, DefinitionDict):
            def_dict = def_dict.defs

        return {key: str(value.contents) for key, value in def_dict.items()}
