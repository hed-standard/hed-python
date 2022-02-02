from hed.models.hed_string import HedString
from hed.models.hed_group import HedGroup
from hed.errors.error_types import DefinitionErrors, ValidationErrors
from hed.errors.error_reporter import ErrorHandler
import copy
from functools import partial

from hed.models.model_constants import DefTagNames
from hed.models.hed_ops import HedOps


class DefEntry:
    def __init__(self, name, contents, takes_value, source_context):
        """Contains info for a single definition tag

        Parameters
        ----------
        name : str
            The label portion of this name(not including definition/)
        contents: HedGroup
            The contents of this definition
        takes_value : bool
            If True, expects ONE tag to have a single # sign in it.
        source_context: {}
            Info about where this definition was declared.
        """
        self.name = name
        self.contents = contents
        if contents:
            contents.cascade_mutable(False)
        self.takes_value = takes_value
        self.source_context = source_context
        self.tag_dict = {}
        if contents:
            add_group_to_dict_new(contents, self.tag_dict)

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
            output_group = self.contents
            if placeholder_value:
                placeholder_tag = output_group.find_placeholder_tag()
                if not placeholder_tag:
                    raise ValueError("Internal error related to placeholders in definition mapping")
                output_group = copy.copy(self.contents)
                placeholder_tag = output_group.make_tag_mutable(placeholder_tag)
                name = f"{name}/{placeholder_value}"
                placeholder_tag.replace_placeholder(placeholder_value)

            output_contents = [replace_tag, output_group]

        output_contents = HedGroup(replace_tag._hed_string,
                                   startpos=replace_tag.span[0], endpos=replace_tag.span[1], contents=output_contents)
        return f"{DefTagNames.DEF_EXPAND_ORG_KEY}/{name}", output_contents


class DefDict(HedOps):
    """Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids_old style file might have many of these(one for each json dict, and another for the actual file)
    """

    def __init__(self):
        """
        Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids_old style file might have many of these(one for each json dict, and another for the actual file)
        Parameters
        ----------
        """
        super().__init__()
        self._defs = {}

        # Definition related issues
        self._extract_def_issues = []

    @property
    def defs(self):
        """
            Provides direct access to internal dictionary.  Alter at your own risk.

        Returns
        -------
        def_dict: {str: DefEntry}
        """
        return self._defs

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

    def __get_string_funcs__(self, **kwargs):
        error_handler = kwargs.get("error_handler")
        return [partial(self.check_for_definitions, error_handler=error_handler)]

    def __get_tag_funcs__(self, **kwargs):
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
            def_tags, group_tags, other_tags = self._extract_tags_from_group(tag_group)

            # Now validate to see if we have a definition.  We want 1 definition, and the other parts are optional.
            if not def_tags:
                # If we don't have at least one valid definition tag, just move on.
                continue

            if not is_top_level:
                new_def_issues +=\
                    ErrorHandler.format_error_with_context(error_handler,
                                                           ValidationErrors.HED_TAG_GROUP_TAG, tag=def_tags[0])
                continue

            if len(def_tags) > 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_DEFINITION_TAGS,
                                                           def_name=def_tags[0].extension_or_value_portion,
                                                           tag_list=[tag for tag in def_tags[1:]])
                continue
            def_tag = def_tags[0]
            def_tag_name = def_tag.extension_or_value_portion
            if len(group_tags) > 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                           def_name=def_tag_name, tag_list=group_tags + other_tags)
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
            self._defs[def_tag_lower] = DefEntry(name=def_tag_name, contents=group_tag,
                                                 takes_value=def_takes_value,
                                                 source_context=context)

        self._extract_def_issues += new_def_issues
        return new_def_issues

    @staticmethod
    def _extract_tags_from_group(tag_group):
        def_tags = []
        group_tags = []
        other_tags = []
        for tag_or_group in tag_group.get_direct_children():
            if isinstance(tag_or_group, HedGroup):
                group_tags.append(tag_or_group)
            elif tag_or_group.short_base_tag.lower() == DefTagNames.DEFINITION_KEY:
                def_tags.append(tag_or_group)
            else:
                other_tags.append(tag_or_group)
        return def_tags, group_tags, other_tags


def add_group_to_dict_new(group, tag_dict=None):
    """

        Note: Expects tags to have forms calculated already.

    Parameters:
        group: HedGroup
            contents to add to the tag dict
        tag_dict: {}
            Output dictionary

    Returns: dict
        Dictionary of tags with a list of values
    """
    if tag_dict is None:
        tag_dict = {}
    for tag in group.get_all_tags():
        short_base_tag = tag.short_base_tag
        value = tag.extension_or_value_portion
        value_dict = tag_dict.get(short_base_tag, {})
        if value:
            value_dict[value] = ''
        tag_dict[short_base_tag] = value_dict
    return tag_dict