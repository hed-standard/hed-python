from hed.models.hed_string import HedString
from hed.models.hed_group import HedGroup
from hed.errors.error_types import DefinitionErrors, ValidationErrors
from hed.errors.error_reporter import ErrorHandler
import copy
from functools import partial

from hed.models.model_constants import DefTagNames


class DefEntry:
    def __init__(self, name, contents_string, takes_value, source_context):
        """Contains info for a single definition tag

        Parameters
        ----------
        name : str
            The label portion of this name(not including definition/)
        contents_string: HedGroup
            The contents of this definition
        takes_value : bool
            If True, expects ONE tag to have a single # sign in it.
        source_context: {}
            Info about where this definition was declared.
        """
        self.name = name
        self.contents = contents_string
        self.takes_value = takes_value
        self.source_context = source_context

    def get_definition(self, replace_tag, placeholder_value=None):
        """
            Returns a copy of the definition with the tag expanded and the placeholder plugged in

        Parameters
        ----------
        replace_tag : HedTag
            The def hed tag to replace with an expanded version
        placeholder_value : str or None
            If present and required, will replace any pound signs in the definition contents

        Returns
        -------
        expanded_tag_name, def_contents: str, [HedGroup or HedTag]
            The expanded def tag name, and the contents of this definition(including the def tag itself)
        """
        if self.takes_value == (placeholder_value is None):
            return None, []

        output_contents = [replace_tag]
        name = self.name
        if self.contents:
            output_group = copy.deepcopy(self.contents)
            if placeholder_value:
                name = f"{name}/{placeholder_value}"
                output_group.replace_placeholder(placeholder_value)

            output_contents = [replace_tag, output_group]

        return f"{DefTagNames.DEF_EXPAND_ORG_KEY}/{name}", output_contents


class DefDict:
    """Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
    """

    def __init__(self):
        """
        Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
        Parameters
        ----------
        """
        self._defs = {}

        # Definition related issues
        self._extract_def_issues = []

    def get_definition_issues(self):
        """
            Returns definition errors found during extraction

        Parameters
        ----------
        Returns
        -------
        issues_list: [{}]
            List of DefinitionErrors found.
        """
        return self._extract_def_issues

    def __iter__(self):
        return iter(self._defs.items())

    def __get_string_ops__(self, **kwargs):
        error_handler = kwargs.get("error_handler")
        return [partial(self.check_for_definitions, error_handler=error_handler)]

    def __get_tag_ops__(self, **kwargs):
        return []

    def check_for_definitions(self, hed_string_obj, error_handler=None):
        """
        Check a given hed string for definition tags, and add them to the dictionary if so.

        Parameters
        ----------
        hed_string_obj : HedString
            A single hed string to gather definitions from
        error_handler: ErrorHandler
            Used to note where definitions are found.  Optional.
        Returns
        ----------
        """
        new_def_issues = []
        for tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            def_tags = []
            group_tags = []
            other_tags = []
            for tag_or_group in tag_group.get_direct_children():
                if isinstance(tag_or_group, HedGroup):
                    group_tags.append(tag_or_group)
                    continue
                else:
                    if tag_or_group.short_base_tag.lower() == DefTagNames.DEFINITION_KEY:
                        def_tags.append(tag_or_group)
                        continue

                other_tags.append(tag_or_group)

            # Now validate to see if we have a definition.  We want 1 definition, and the other parts are optional.
            if not def_tags:
                # If we don't have at least one valid definition tag, just move on.  This is probably a tag with
                # the word definition somewhere else in the text.
                continue

            if not is_top_level:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         ValidationErrors.HED_TAG_GROUP_TAG,
                                                                         tag=def_tags[0])
                continue

            if len(def_tags) > 1:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.WRONG_NUMBER_DEFINITION_TAGS,
                                                                         def_name=def_tags[0].extension_or_value_portion,
                                                                         tag_list=[tag for tag in
                                                                                   def_tags[1:]])
                continue
            def_tag = def_tags[0]
            def_tag_name = def_tag.extension_or_value_portion
            if len(group_tags) > 1:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                                         def_name=def_tag_name,
                                                                         tag_list=group_tags + other_tags)
                continue
            if len(other_tags) > 0:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                                         def_name=def_tag_name,
                                                                         tag_list=other_tags + group_tags)
                continue

            group_tag = group_tags[0] if group_tags else None

            def_takes_value = def_tag_name.lower().endswith("/#")
            if def_takes_value:
                def_tag_name = def_tag_name[:-len("/#")]

            def_tag_lower = def_tag_name.lower()
            if "/" in def_tag_lower or "#" in def_tag_lower:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                         def_name=def_tag_name)
                continue

            # Verify placeholders here.
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
            if def_tag_lower in self._defs:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.DUPLICATE_DEFINITION,
                                                                         def_name=def_tag_name)
                continue
            self._defs[def_tag_lower] = DefEntry(name=def_tag_name, contents_string=group_tag,
                                                 takes_value=def_takes_value,
                                                 source_context=context)

        self._extract_def_issues += new_def_issues
        return new_def_issues

    @staticmethod
    def _check_tag_starts_with(hed_tag, target_tag_short_name):
        """ Check if a given tag starts with a given string, and returns the tag with the prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        target_tag_short_name : str
            The string to match eg find target_tag_short_name in hed_tag
        Returns
        -------
            str: the tag without the removed prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        found_index = hed_tag_lower.find(target_tag_short_name)

        if found_index == -1:
            return None

        if found_index == 0 or hed_tag_lower[found_index - 1] == "/":
            return hed_tag[found_index + len(target_tag_short_name):]
        return None
