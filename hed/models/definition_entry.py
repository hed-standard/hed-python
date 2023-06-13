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
            contents = contents.copy().sort()
        self.contents = contents
        self.takes_value = takes_value
        self.source_context = source_context

    def get_definition(self, replace_tag, placeholder_value=None, return_copy_of_tag=False):
        """ Return a copy of the definition with the tag expanded and the placeholder plugged in.

        Parameters:
            replace_tag (HedTag): The def hed tag to replace with an expanded version
            placeholder_value (str or None):    If present and required, will replace any pound signs
                                                in the definition contents.
            return_copy_of_tag(bool): Set to true for validation

        Returns:
            str:          The expanded def tag name
            HedGroup:     The contents of this definition(including the def tag itself)

        :raises ValueError:
            - If a placeholder_value is passed, but this definition doesn't have a placeholder.

        """
        if self.takes_value == (placeholder_value is None):
            return None, []

        if return_copy_of_tag:
            replace_tag = replace_tag.copy()
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

    def __str__(self):
        return str(self.contents)