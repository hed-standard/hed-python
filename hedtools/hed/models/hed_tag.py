

class HedTag:
    """
        A single HedTag in a string, keeps track of original value and positioning
    """
    def __init__(self, hed_string, span=None, extension_index=None):
        """

        Parameters
        ----------
        hed_string : str
            Source hed string for this tag
        span : (int, int)
            The start and end indexes of the tag in the hed_string.
        extension_index: int or None
            Only used to initialize a HedTag easily by a user.  Index the extension/value portion of the tag starts.
        """
        self._hed_string = hed_string
        if span is None:
            span = (0, len(hed_string))
        # This is the span into the original hed string for this tag
        self.span = span

        # If this is present, use this as the output tag.  Priority is _tag, _long_tag, then _hed_string[span]
        # this is generally only filled out if we're changing a tag from the source(adding a prefix, etc)
        self._tag = None

        # The long form of the tag, if generated.
        self._long_tag = None

        # offset into _long_tag where the short tag starts at.
        self._short_tag_index = None

        # offset into _long_tag where the base_tag ends at.  The "base tag" is the long form with no extension/value.
        self._extension_index = None

        if extension_index:
            self._extension_index = extension_index
            self._long_tag = self._hed_string

    @property
    def short_tag(self):
        """
            Returns the short version of the tag, including value or extension

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        short_tag: str
            The short version of the tag, including value or extension
        """
        if self._short_tag_index is None:
            return str(self)

        return self._long_tag[self._short_tag_index:]

    @property
    def base_tag(self):
        """
            Returns the short version of the tag, without value or extension

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        base_tag: str
            The short version of the tag, without value or extension
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[:self._extension_index]

    @property
    def tag(self):
        """
            Returns the entire user editable attribute in the tag

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        tag: str
            The custom set user version of the tag.
        """
        return self._tag

    @tag.setter
    def tag(self, new_tag_val):
        """
            Allows you to overwrite the tag output text.

            Primarily used to expand def tags.

            Note: only valid after calling convert_to_canonical_forms

        Parameters
        ----------
        new_tag_val : str
            New (implicitly long form) of tag to set
        """
        if self._long_tag:
            raise ValueError("Can edit tags before calculating canonical forms.")
        self._tag = new_tag_val

    @property
    def extension_or_value_portion(self):
        """Gets the extension or value portion at the end of a hed tag, if one exists

        Generally this is just the portion after the last slash.  Note: This tag must have been computed first.

        Returns
        -------
        str
            The tag name.
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[self._extension_index + 1:]

    @property
    def long_tag(self):
        if self._long_tag is None:
            return str(self)
        return self._long_tag

    @property
    def org_tag(self):
        return self._hed_string[self.span[0]:self.span[1]]

    def __str__(self):
        """
        Convert this HedTag to a string

        Returns
        -------
        str
            Return the original tag if we haven't set a new tag.(eg short to long)
        """
        if self._tag:
            return self._tag

        if self._long_tag:
            return self._long_tag

        return self._hed_string[self.span[0]:self.span[1]]

    def add_prefix_if_not_present(self, required_prefix):
        """Add a prefix to this tag *unless* the tag is already formatted.

        This means we verify the tag does not have the required prefix, or any partial prefix

        Ex:
        RequiredPrefix: KnownTag1/KnownTag2
        Case 1: KnownTag1/KnownTag2/ColumnValue
            Will not be changed, has prefix already
        Case 2: KnownTag2/ColumnValue
            Will not be changed, has partial prefix already
        Case 3: ColumnValue
            Prefix will be added.

        Parameters
        ----------
        required_prefix : str
            The full prefix to add if not present
        """
        checking_prefix = required_prefix
        while checking_prefix:
            if self.lower().startswith(checking_prefix.lower()):
                return
            slash_index = checking_prefix.find("/") + 1
            if slash_index == 0:
                break
            checking_prefix = checking_prefix[slash_index:]
        self._tag = required_prefix + str(self)

    def remove_prefix_if_present(self, prefix_to_remove):
        if self.lower().startswith(prefix_to_remove.lower()):
            self._tag = str(self)[len(prefix_to_remove):]

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def convert_to_canonical_forms(self, hed_schema, error_handler=None):
        """
            This updates the internal tag states from the schema, so you can convert from short to long etc

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to validate this tag
        error_handler : ErrorHandler or None
            The error handler to generate errors with

        Returns
        -------
        conversion_issues: [{}]
            A list of issues found during conversion
        """
        if not hed_schema:
            return []

        long_form, short_index, remainder_index, tag_issues = hed_schema.calculate_canonical_forms(self, error_handler)
        self._long_tag = long_form
        self._short_tag_index = short_index
        self._extension_index = remainder_index

        return tag_issues