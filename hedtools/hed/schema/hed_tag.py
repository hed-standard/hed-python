from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler


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

        # If this is present, use this as the org tag for most purposes.  This is generally only filled out
        # if the tag has a prefix added, or is an expanded def.
        self._tag = None

        # The long form of the tag, if generated.
        self._long_tag = None

        # offset into _long_tag where the short tag starts at.
        self._short_tag_index = None

        # offset into _long_tag where the base_tag ends at.  The "base tag" is the long form with no extension/value.
        self._extension_index = None

        self._library_prefix = self._get_library_prefix(self.org_tag)

        if extension_index:
            self._extension_index = extension_index
            self._long_tag = self._hed_string

        self.is_definition = False

    @property
    def library_prefix(self):
        return self._library_prefix

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

        return self._library_prefix + self._long_tag[self._short_tag_index:]

    @property
    def base_tag(self):
        """
            Returns the long version of the tag, without value or extension

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        base_tag: str
            The long version of the tag, without value or extension
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[:self._extension_index]

    @property
    def short_base_tag(self):
        """
            Returns just the short non-extension portion of a tag.

            eg ParentNodes/Def/DefName would return just "Def"

        Returns
        -------
        base_tag: str
            The short non-extension port of a tag.
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[self._short_tag_index:self._extension_index]

    @short_base_tag.setter
    def short_base_tag(self, new_tag_val):
        """
            Change the short term of the tag.

            Note: This does not change the long form location, so only set this on tags with the same parent node.

        Parameters
        ----------
        new_tag_val : str
            The new short_base_tag for this tag.  Generally this is used to swap def to def-expand.
        Returns
        -------

        """
        long_part = self._long_tag[:self._short_tag_index]
        self._long_tag = f"{long_part}{new_tag_val}/{self.extension_or_value_portion}"
        self._extension_index = self._short_tag_index + len(new_tag_val)

    @property
    def org_base_tag(self):
        """
            Returns the original version of the tag, without value or extension

            Warning: This could be empty if the original tag had a prefix prepended.
                eg a column where "Label/" is prepended, thus the column value has zero base portion.

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        base_tag: str
            The original version of the tag, without value or extension
        """
        if self._extension_index is None:
            return str(self)

        # This mess could be optimized better
        extension_len = len(self.extension_or_value_portion)
        if not extension_len:
            return self.tag

        org_len = len(self.tag)
        if org_len == extension_len:
            return ""

        return self.tag[:org_len - (extension_len + 1)]

    def tag_modified(self):
        """
            Returns true if this tag has been modified from it's original form.

            Modifications can include adding a column prefix.

        Returns
        -------
        was_modified: bool

        """
        return bool(self._tag)

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
        if self._tag:
            return self._tag

        return self.org_tag

    # Honestly this should probably be removed
    # this should be replaced with a "set long tag" which updates the short and long versions automatically.
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
            raise ValueError("Can only edit tags before calculating canonical forms. " +
                             "This could be updated to instead remove computed forms.")
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
        """
            Returns the long form of the tag if it exists, otherwise returns the default tag form.

        Returns
        -------
        long_tag: str
            The long form of this tag.
        """
        if self._long_tag is None:
            return str(self)
        return self._long_tag

    @property
    def org_tag(self):
        """
            Returns the original unmodified tag.

        Returns
        -------
        original_tag: str
            The original unmodified tag.
        """
        return self._hed_string[self.span[0]:self.span[1]]

    def __str__(self):
        """
        Convert this HedTag to a string

        Returns
        -------
        str
            Return the original tag if we haven't set a new tag.(eg short to long)
        """
        if self._long_tag:
            return self._long_tag

        if self._tag:
            return self._tag

        return self._hed_string[self.span[0]:self.span[1]]

    def _str_no_long_tag(self):
        if self._tag:
            return self._tag

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
        self._tag = required_prefix + self.org_tag

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def replace_placeholder(self, placeholder_value):
        """
            If this tag a placeholder character(#), replace them with the placeholder value.

        Parameters
        ----------
        placeholder_value : str
            Value to replace placeholder with.
        """
        if "#" in self.org_tag:
            if self._long_tag:
                # This could possibly be more efficient
                self._tag = self.org_tag.replace("#", placeholder_value)
                self._long_tag = self._long_tag.replace("#", placeholder_value)
            else:
                self._tag = self.org_tag.replace("#", placeholder_value)

    def convert_to_canonical_forms(self, hed_schema):
        """
            This updates the internal tag states from the schema, so you can convert from short to long etc

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to validate this tag

        Returns
        -------
        conversion_issues: [{}]
            A list of issues found during conversion
        """
        if not hed_schema:
            return self._convert_key_tags_to_canonical_form()

        specific_schema = hed_schema.schema_for_prefix(self.library_prefix)
        if not specific_schema:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_PREFIX, self,
                                                          self.library_prefix, hed_schema.valid_prefixes)
            return validation_issues

        long_form, short_index, remainder_index, tag_issues = \
            self._calculate_canonical_forms(specific_schema)
        self._long_tag = long_form
        self._short_tag_index = short_index
        self._extension_index = remainder_index

        return tag_issues

    def _convert_key_tags_to_canonical_form(self):
        # todo: eventually make this function less bad.
        # Finds the canonical form for basic known tags such as definition and def.
        tags_to_identify = ["def", "onset", "definition", "offset", "def-expand"]
        for key_tag in tags_to_identify:
            is_key_tag = self._check_tag_starts_with(str(self), key_tag)
            if is_key_tag is not None:
                self._long_tag = str(self)
                self._extension_index = len(str(self)) - len(is_key_tag)
                self._short_tag_index = self._extension_index - len(key_tag)

        return []

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

    def _validate_parent_nodes(self, long_org_tags, main_hed_portion):
        long_org_tag = None
        if isinstance(long_org_tags, str):
            tag_string = long_org_tags.lower()

            # Verify the tag has the correct path above it.
            if tag_string.endswith(main_hed_portion):
                long_org_tag = long_org_tags
        else:
            for org_tag_string in long_org_tags:
                tag_string = org_tag_string.lower()

                if tag_string.endswith(main_hed_portion):
                    long_org_tag = org_tag_string
                    break

        return long_org_tag

    def _format_state_error(self, error_code, state, **kwargs):
        return ErrorHandler.format_error(error_code, self,
                                         index_in_tag=state["index_start"] + state["prefix_tag_adj"],
                                         index_in_tag_end=state["index_in_tag_end"] + state["prefix_tag_adj"],
                                         **kwargs)

    def _handle_unknown_term(self, hed_schema, term, clean_tag, state):
        if term not in hed_schema.short_tag_mapping:
            state["found_unknown_extension"] = True
            if not state["found_long_org_tag"]:
                return self._format_state_error(ValidationErrors.NO_VALID_TAG_FOUND, state)
            return None

        long_org_tags = hed_schema.short_tag_mapping[term]
        long_org_tag = self._validate_parent_nodes(long_org_tags, clean_tag[:state["index_in_tag_end"]])
        if not long_org_tag:
            return self._format_state_error(ValidationErrors.INVALID_PARENT_NODE, state,
                                            expected_parent_tag=long_org_tags)

        # In hed2 compatible, reject short tags.
        if hed_schema.has_duplicate_tags:
            if not clean_tag.startswith(long_org_tag.lower()):
                return self._format_state_error(ValidationErrors.NO_VALID_TAG_FOUND, state)

        state["found_index_start"] = state["index_start"]
        state["found_index_end"] = state["index_in_tag_end"]
        state["found_long_org_tag"] = long_org_tag

    def _calculate_canonical_forms(self, hed_schema):
        """
        This takes a hed tag(short or long form) and converts it to the long form
        Works left to right.(mostly relevant for errors)
        Note: This only does minimal validation

        Parameters
        ----------
        hed_schema: HedSchema
            The hed schema to use to compute forms of this tag.
        Returns
        -------
        long_tag: str
            The converted long tag
        short_tag_index: int
            The position the short tag starts at in long_tag
        extension_index: int
            The position the extension or value starts at in the long_tag
        errors: list
            a list of errors while converting
        """
        clean_tag = self.tag.lower()
        prefix = self.library_prefix
        clean_tag = clean_tag[len(prefix):]
        split_tags = clean_tag.split("/")
        state = {}
        state["found_unknown_extension"] = False
        state["found_index_end"] = 0
        state["found_index_start"] = 0
        state["found_long_org_tag"] = ""
        state["index_in_tag_end"] = 0
        state["prefix_tag_adj"] = len(prefix)
        state["index_start"] = 0

        # Iterate over terms left to right keeping track of current state
        for term in split_tags:
            term_len = len(term)
            # Skip slashes
            if state["index_in_tag_end"] != 0:
                state["index_in_tag_end"] += 1
            state["index_start"] = state["index_in_tag_end"]
            state["index_in_tag_end"] += term_len

            # If we already found an unknown tag, it's implicitly an extension.  No known tags can follow it.
            if not state["found_unknown_extension"]:
                error = self._handle_unknown_term(hed_schema, term, clean_tag, state)
                if error:
                    return str(self), None, None, error
            else:
                # These means we found a known tag in the remainder/extension section, which is an error
                if term in hed_schema.short_tag_mapping:
                    error = self._format_state_error(ValidationErrors.INVALID_PARENT_NODE, state,
                                                     expected_parent_tag=hed_schema.short_tag_mapping[term])
                    return str(self), None, None, error

        full_tag_string = self._str_no_long_tag()
        # skip over the tag prefix if present
        full_tag_string = full_tag_string[len(prefix):]
        # Finally don't actually adjust the tag if it's hed2 style.
        if hed_schema.has_duplicate_tags:
            return full_tag_string, None, state["found_index_end"], []

        remainder = full_tag_string[state["found_index_end"]:]
        long_tag_string = state["found_long_org_tag"] + remainder

        # calculate short_tag index into long tag.
        state["found_index_start"] += (len(long_tag_string) - len(full_tag_string))
        remainder_start_index = state["found_index_end"] + (len(long_tag_string) - len(full_tag_string))
        return prefix + long_tag_string, \
               state["found_index_start"] + state["prefix_tag_adj"], \
               remainder_start_index + state["prefix_tag_adj"], \
               {}

    def _get_library_prefix(self, org_tag):
        first_slash = org_tag.find("/")
        first_colon = org_tag.find(":")

        if first_colon != -1:
            if first_slash != -1 and first_colon > first_slash:
                return ""

            return org_tag[:first_colon + 1]
        return ""
