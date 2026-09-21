"""Locate the placeholder tag of a value column template."""

from __future__ import annotations

from hed.models.hed_string import HedString
from hed.models.model_constants import DefTagNames


def placeholder_tag(template, hed_schema, def_dict=None):
    """Return the tag of a value column template whose value portion is ``#``, or None if there is none.

    A value column's cell is substituted for the ``#`` of its template, so checking the cell means
    checking that one tag with the value in place: its units and value class. The rest of the template
    (other tags, ``{column}`` references) is the sidecar validator's business.

    For a ``Def/Name/#`` template the ``#`` fills the placeholder inside the definition, so the tag
    returned is the placeholder tag in the definition's body. It is None when the definition is unknown
    or takes no value; the sidecar validator has already reported that.

    Parameters:
        template (str): The value column's HED string, containing one ``#``.
        hed_schema (HedSchema or HedSchemaGroup): The schema that identifies the tags.
        def_dict (DefinitionDict or None): The definitions a ``Def/Name/#`` may refer to.

    Returns:
        HedTag or None: The tag to substitute the value into, with its schema entry resolved.
    """
    hed_string = HedString(template, hed_schema, def_dict=def_dict)
    for tag in hed_string.get_all_tags():
        if "#" not in tag.extension:
            continue
        if tag.short_base_tag.casefold() != DefTagNames.DEF_KEY.casefold():
            return tag
        if def_dict is None:
            return None
        entry = def_dict.get(tag.extension.split("/")[0])
        if entry is None or not entry.takes_value or entry.contents is None:
            return None
        return next((inner for inner in entry.contents.get_all_tags() if "#" in inner.extension), None)
    return None
