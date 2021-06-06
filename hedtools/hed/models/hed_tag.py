

class HedTag:
    """
        A single HedTag in a string, keeps track of original value and positioning
    """
    def __init__(self, hed_string, span):
        """

        Parameters
        ----------
        hed_string : str
            Source hed string for this tag
        span : (int, int)
            The start and end indexes of the tag in the hed_string..
        """
        self._hed_string = hed_string
        # This is the span into the original hed string for this tag
        self.span = span

        # If this is present, use this as the output tag.  Priority is _tag, _long_tag, then _hed_string[span]
        # this is generally only filled out if we're changing a tag from the source(adding a prefix, etc)
        self._tag = None

        # The long form of the tag, if generated.
        self._long_tag = None
        # offset into _long_tag where the short tag starts at.
        self._short_tag_index = None

    # Note this is only valid after calling compute canonical forms
    @property
    def short_tag(self):
        if self._short_tag_index is None:
            return str(self)

        return self._long_tag[self._short_tag_index:]

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
