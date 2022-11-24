import copy

from hed.models.hed_group import HedGroup
from hed.models.model_constants import DefTagNames


class DefinitionEntry:
    """ A single definition. """

    def __init__(self, name, contents, takes_value, source_context):
        """ Initialize info for a single definition.

        Parameters:
            name (str):            The label portion of this name (not including Definition/).
            contents (HedGroup):   The contents of this definition.
            takes_value (bool):    If True, expects ONE tag to have a single # sign in it.
            source_context (list, None): List (stack) of dictionaries giving context for reporting errors.
        """
        self.name = name
        if contents:
            contents = contents.copy()
        self.contents = contents
        self.takes_value = takes_value
        self.source_context = source_context
        self.tag_dict = {}
        if contents:
            add_group_to_dict(contents, self.tag_dict)

    def get_definition(self, replace_tag, placeholder_value=None):
        """ Return a copy of the definition with the tag expanded and the placeholder plugged in.

        Parameters:
            replace_tag (HedTag): The def hed tag to replace with an expanded version
            placeholder_value (str or None):    If present and required, will replace any pound signs
                                                in the definition contents.

        Returns:
            str:          The expanded def tag name
            HedGroup:     The contents of this definition(including the def tag itself)

        Raises:
            ValueError:  If a placeholder_value is passed, but this definition doesn't have a placeholder.

        """
        if self.takes_value == (placeholder_value is None):
            return None, []

        output_contents = [replace_tag]
        name = self.name
        if self.contents:
            output_group = self.contents
            if placeholder_value:
                output_group = copy.deepcopy(self.contents)
                placeholder_tag = output_group.find_placeholder_tag()
                if not placeholder_tag:
                    raise ValueError("Internal error related to placeholders in definition mapping")
                name = f"{name}/{placeholder_value}"
                placeholder_tag.replace_placeholder(placeholder_value)

            output_contents = [replace_tag, output_group]

        output_contents = HedGroup(replace_tag._hed_string,
                                   startpos=replace_tag.span[0], endpos=replace_tag.span[1], contents=output_contents)
        return f"{DefTagNames.DEF_EXPAND_ORG_KEY}/{name}", output_contents


def add_group_to_dict(group, tag_dict=None):
    """ Add the tags and their values from a HED group to a tag dictionary.

    Parameters:
        group (HedGroup):   Contents to add to the tag dict.
        tag_dict (dict):    The starting tag dictionary to add to.

    Returns:
        dict:  The updated tag_dict containing the tags with a list of values.

    Notes:
        - Expects tags to have forms calculated already.

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
