"""
"""

# todo: Switch various properties to this once we require python 3.8

from hed.errors.exceptions import HedExceptions, HedFileError


class HedSchemaGroup:
    """
        This class handles combining multiple HedSchema objects for validation.

        You cannot save/load/etc the combined schema object directly.
    """
    def __init__(self, schema_list):
        """
        Create combination of multiple HedSchema objects you can use with the validator.

        Note: will raise HedFileError if two schemas share the same prefix

        Parameters
        ----------
        Returns
        -------
        HedSchemaGroup
            A HedSchemaCombined object.
        """
        library_prefixes = [hed_schema._library_prefix for hed_schema in schema_list]
        if len(set(library_prefixes)) != len(library_prefixes):
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                               "Multiple schemas share the same tag prefix.  This is not allowed.",
                               filename="Combined Schema")
        self._schemas = {hed_schema._library_prefix: hed_schema for hed_schema in schema_list}

    # ===============================================
    # General schema properties/functions
    # ===============================================
    @property
    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return any([schema.has_duplicate_tags for schema in self._schemas.values()])

    @property
    def unit_classes(self):
        return all([schema.unit_classes for schema in self._schemas.values()])

    @property
    def is_hed3_compatible(self):
        return all([schema.is_hed3_compatible for schema in self._schemas.values()])

    @property
    def is_hed3_schema(self):
        # All combined schemas are implicitly hed3.
        return True

    @property
    def unit_modifiers(self):
        return all([schema.unit_modifiers for schema in self._schemas.values()])

    @property
    def value_classes(self):
        return all([schema.value_classes for schema in self._schemas.values()])

    def __eq__(self, other):
        return self._schemas == other._schemas

    def schema_for_prefix(self, prefix):
        """
            Return the specific HedSchema object for the given tag prefix.

            Returns None if prefix is invalid.

        Parameters
        ----------
        prefix : str
            A schema library prefix to get the schema for.

        Returns
        -------
        schema: HedSchema
            The specific schema for this library prefix
        """
        schema = self._schemas.get(prefix)
        return schema

    @property
    def valid_prefixes(self):
        """
            Gets a list of all prefixes this schema will accept.

        Returns
        -------
        valid_prefixes: [str]
            A list of valid tag prefixes for this schema.
        """
        return list(self._schemas.keys())

    # ===============================================
    # Basic tag attributes
    # ===============================================
    def is_extension_allowed_tag(self, original_tag):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        tag_takes_extension: bool
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.
        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.is_extension_allowed_tag(original_tag)

    def is_takes_value_tag(self, original_tag):
        """Checks to see if the tag has the 'takesValue' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'takesValue' attribute. False, if otherwise.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.is_takes_value_tag(original_tag)

    def is_unit_class_tag(self, original_tag):
        """Checks to see if the tag has the 'unitClass' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'unitClass' attribute. False, if otherwise.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.is_unit_class_tag(original_tag)

    def is_value_class_tag(self, original_tag):
        """Checks to see if the tag has the 'valueClass' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'valueClass' attribute. False, if otherwise.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.is_value_class_tag(original_tag)

    def is_basic_tag(self, original_tag):
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.is_basic_tag(original_tag)

    def base_tag_has_attribute(self, original_tag, tag_attribute):
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.base_tag_has_attribute(original_tag, tag_attribute)

    def tag_has_attribute(self, original_tag, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        original_tag: HedTag
            A tag.
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.tag_has_attribute(original_tag, tag_attribute)

    # ===============================================
    # More complex tag attributes/combinations of tags etc.
    # ===============================================
    def get_tag_unit_classes(self, original_tag):
        """Gets the unit classes associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        []
            A list containing the unit classes associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit classes associated with it.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.get_tag_unit_classes(original_tag)

    def get_tag_value_classes(self, original_tag):
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.get_tag_value_classes(original_tag)

    def get_unit_class_default_unit(self, original_tag):
        """Gets the default unit class unit that is associated with the specified tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        str
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.get_unit_class_default_unit(original_tag)

    def get_tag_unit_class_units(self, original_tag):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        []
            A list containing the unit class units associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.get_tag_unit_class_units(original_tag)

    def get_stripped_unit_value(self, original_tag):
        """
        Returns the extension portion of the tag if it exists, without the units.

        eg 'Duration/3 ms' will return '3'

        Parameters
        ----------
        original_tag : HedTag
            The hed tag you want the units portion for.

        Returns
        -------
        stripped_unit_value: str
            The extension portion with the units removed.
        """
        schema = self._schemas.get(original_tag.library_prefix)
        if schema:
            return schema.get_stripped_unit_value(original_tag)

    def get_all_tags_with_attribute(self, key):
        all_tags = set()
        for schema in self._schemas.values():
            all_tags.update(schema.get_all_tags_with_attribute(key))
        return all_tags
