"""A single definition."""

import copy
from typing import Union

from hed.models.hed_group import HedGroup


class DefinitionEntry:
    """Stores the resolved contents of a single HED Definition.

    A ``DefinitionEntry`` is created when a ``Definition/`` tag group is parsed
    and stored in a :class:`~hed.models.DefinitionDict`.  It captures:

    - **name** — the lower-cased label portion (without ``Definition/``).
    - **contents** — the inner :class:`~hed.models.HedGroup` of the definition
      (``None`` if the definition body is empty).
    - **takes_value** — whether exactly one tag inside contains a ``#`` placeholder
      (i.e. the definition expects a run-time value via ``Def/name/value``).
    - **source_context** — the error-context stack captured at parse time, used
      to produce precise error messages when the definition is later expanded.

    **Use this class directly when you need to:**

    - Iterate over a :class:`~hed.models.DefinitionDict` and inspect individual
      definition bodies or their placeholder status.
    - Build tooling that expands, serialises, or analyses HED definitions
      programmatically.

    **Most users never need this class** — :meth:`~hed.models.DefinitionDict.get_def_entry`
    and :meth:`~hed.models.DefinitionDict.expand_def_tag` handle the common workflows.
    """

    def __init__(self, name, contents, takes_value, source_context):
        """Initialize info for a single definition.

        Parameters:
            name (str):            The label portion of this name (not including Definition/).
            contents (HedGroup):   The contents of this definition (which could be None).
            takes_value (bool):    If True, expects ONE tag to have a single # sign in it.
            source_context (list, None): List (stack) of dictionaries giving context for reporting errors.
        """
        self.name = name.casefold()
        if contents:
            contents = contents.copy()
            contents.sort()
        if contents:
            contents = contents.copy()
        self.contents = contents
        self.takes_value = takes_value
        self.source_context = source_context

    def get_definition(self, replace_tag, placeholder_value=None, return_copy_of_tag=False) -> Union["HedGroup", None]:
        """Return a copy of the definition with the tag expanded and the placeholder plugged in.

            Returns None if placeholder_value passed when it doesn't take value, or vice versa.

        Parameters:
            replace_tag (HedTag): The def HED tag to replace with an expanded version.
            placeholder_value (str or None): If present and required, will replace any pound signs
                                                in the definition contents.
            return_copy_of_tag (bool): Set to True for validation.

        Returns:
            Union[HedGroup, None]: The contents of this definition(including the def tag itself).

        Raises:
            ValueError: Something internally went wrong with finding the placeholder tag. This should not be possible.
        """
        if self.takes_value == (not placeholder_value):
            return None

        if return_copy_of_tag:
            replace_tag = replace_tag.copy()
        output_contents = [replace_tag]
        if self.contents:
            output_group = copy.deepcopy(self.contents)
            if placeholder_value:
                placeholder_tag = output_group.find_placeholder_tag()
                if not placeholder_tag:
                    raise ValueError("Internal error related to placeholders in definition mapping")
                placeholder_tag.replace_placeholder(placeholder_value)

            output_contents = [replace_tag, output_group]

        output_contents = HedGroup(
            replace_tag._hed_string, startpos=replace_tag.span[0], endpos=replace_tag.span[1], contents=output_contents
        )
        return output_contents

    def __str__(self):
        return str(self.contents)

    def __eq__(self, other):
        """Check equality based on name, contents, and takes_value.

        Parameters:
            other (DefinitionEntry): Another DefinitionEntry to compare with.

        Returns:
            bool: True if name, contents, and takes_value are equal, False otherwise.
        """
        if not isinstance(other, DefinitionEntry):
            return False

        return self.name == other.name and self.contents == other.contents and self.takes_value == other.takes_value
