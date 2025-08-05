""" A HED string with its schema and definitions. """
from __future__ import annotations

import copy
from hed.models.hed_group import HedGroup
from hed.models.hed_tag import HedTag
from hed.models.model_constants import DefTagNames


class HedString(HedGroup):
    """ A HED string with its schema and definitions. """

    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'

    def __init__(self, hed_string, hed_schema, def_dict=None, _contents=None):
        """ Constructor for the HedString class.

        Parameters:
            hed_string (str): A HED string consisting of tags and tag groups.
            hed_schema (HedSchema): The schema to use to identify tags.
            def_dict (DefinitionDict or None): The def dict to use to identify def/def expand tags.
            _contents ([HedGroup and/or HedTag] or None): Create a HedString from this exact list of children.
                                                          Does not make a copy.
        Notes:
            - The HedString object parses its component tags and groups into a tree-like structure.

        """

        if _contents is not None:
            contents = _contents
        else:
            try:
                contents = self.split_into_groups(hed_string, hed_schema, def_dict)
            except ValueError:
                contents = []
        super().__init__(hed_string, contents=contents, startpos=0, endpos=len(hed_string))
        self._schema = hed_schema
        self._from_strings = None
        self._def_dict = def_dict

    @staticmethod
    def from_hed_strings(hed_strings) -> HedString:
        """ Create a new HedString from a list of HedStrings.

        Parameters:
            hed_strings (list or None): A list of HedString objects to combine.
                                        This takes ownership of their children.

        Returns:
            HedString: The newly combined HedString.
        """
        if not hed_strings:
            raise TypeError("Passed an empty list to from_hed_strings")
        new_string = HedString.__new__(HedString)
        hed_string = ",".join([group._hed_string for group in hed_strings])
        contents = [child for sub_string in hed_strings for child in sub_string.children]
        first_schema = hed_strings[0]._schema
        first_dict = hed_strings[0]._def_dict
        new_string.__init__(hed_string=hed_string, _contents=contents, hed_schema=first_schema, def_dict=first_dict)
        new_string._from_strings = hed_strings
        return new_string

    @property
    def is_group(self):
        """ Always False since the underlying string is not a group with parentheses. """
        return False

    def _calculate_to_canonical_forms(self, hed_schema):
        """ Identify all tags using the given schema.

        Parameters:
            hed_schema (HedSchema, HedSchemaGroup): The schema to use to validate/convert tags.

        Returns:
            list: A list of issues found while converting the string. Each issue is a dictionary.

        """
        validation_issues = []
        for tag in self.get_all_tags():
            validation_issues += tag._calculate_to_canonical_forms(hed_schema)

        return validation_issues

    def __deepcopy__(self, memo):
        # check if the object has already been copied
        if id(self) in memo:
            return memo[id(self)]

        # create a new instance of HedString class, and direct copy all parameters
        new_string = self.__class__.__new__(self.__class__)
        new_string.__dict__.update(self.__dict__)

        # add the new object to the memo dictionary
        memo[id(self)] = new_string

        # Deep copy the attributes that need it(most notably, we don't copy schema/schema entry)
        new_string._original_children = copy.deepcopy(self._original_children, memo)
        new_string._from_strings = copy.deepcopy(self._from_strings, memo)
        new_string.children = copy.deepcopy(self.children, memo)

        return new_string

    def copy(self) -> 'HedString':
        """ Return a deep copy of this string.

        Returns:
            HedString: The copied group.

        """
        return_copy = copy.deepcopy(self)
        return return_copy

    def remove_definitions(self):
        """ Remove definition tags and groups from this string.

            This does not validate definitions and will blindly removing invalid ones as well.
        """
        definition_groups = self.find_top_level_tags({DefTagNames.DEFINITION_KEY}, include_groups=1)
        if definition_groups:
            self.remove(definition_groups)

    def shrink_defs(self) -> 'HedString':
        """ Replace def-expand tags with def tags.

            This does not validate them and will blindly shrink invalid ones as well.

        Returns:
            HedString: self
        """
        for def_expand_tag, def_expand_group in self.find_tags({DefTagNames.DEF_EXPAND_KEY}, recursive=True):
            expanded_parent = def_expand_group._parent
            if expanded_parent:
                def_expand_tag.short_base_tag = DefTagNames.DEF_KEY
                def_expand_tag._parent = expanded_parent
                expanded_parent.replace(def_expand_group, def_expand_tag)

        return self

    def expand_defs(self) -> "HedString":
        """ Replace def tags with def-expand tags.

            This does very minimal validation.

        Returns:
            HedString: self
        """
        def_tags = self.find_def_tags(recursive=True, include_groups=0)

        replacements = []
        for tag in def_tags:
            if tag.expandable and not tag.expanded:
                replacements.append((tag, tag.expandable))

        for tag, group in replacements:
            tag_parent = tag._parent
            tag_parent.replace(tag, group)
            tag._parent = group
            tag.short_base_tag = DefTagNames.DEF_EXPAND_KEY

        return self

    def get_as_original(self) -> str:
        """ Return the original form of this string.

        Returns:
            str: The string with all the tags in their original form.

        Notes:
            Potentially with some extraneous spaces removed on returned string.
        """
        return self.get_as_form("org_tag")

    @staticmethod
    def split_into_groups(hed_string, hed_schema, def_dict=None) -> list:
        """ Split the HED string into a parse tree.

        Parameters:
            hed_string (str): A HED string consisting of tags and tag groups to be processed.
            hed_schema (HedSchema): HED schema to use to identify tags.
            def_dict (DefinitionDict): The definitions to identify.

        Returns:
            list:  A list of HedTag and/or HedGroup.

        Raises:
            ValueError: If the string is significantly malformed, such as mismatched parentheses.

        Notes:
            - The parse tree consists of tag groups, tags, and delimiters.
        """
        current_tag_group = [[]]

        input_tags = HedString.split_hed_string(hed_string)
        for is_hed_tag, (startpos, endpos) in input_tags:
            if is_hed_tag:
                new_tag = HedTag(hed_string, hed_schema, (startpos, endpos), def_dict)
                current_tag_group[-1].append(new_tag)
            else:
                string_portion = hed_string[startpos:endpos]
                delimiter_index = 0
                for i, char in enumerate(string_portion):
                    if not char.isspace():
                        delimiter_index = i
                        break

                delimiter_char = string_portion[delimiter_index]

                if delimiter_char is HedString.OPENING_GROUP_CHARACTER:
                    current_tag_group.append(HedGroup(hed_string, startpos + delimiter_index))

                if delimiter_char is HedString.CLOSING_GROUP_CHARACTER:
                    # Terminate existing group, and save it off.
                    paren_end = startpos + delimiter_index + 1

                    if len(current_tag_group) > 1:
                        new_group = current_tag_group.pop()
                        new_group._endpos = paren_end

                        current_tag_group[-1].append(new_group)
                    else:
                        raise ValueError(f"Closing parentheses in HED string {hed_string}")

        # Comma delimiter issues are ignored and assumed already validated currently.
        if len(current_tag_group) != 1:
            raise ValueError(f"Unmatched opening parentheses in HED string {hed_string}")

        return current_tag_group[0]

    def _get_org_span(self, tag_or_group):
        """ If this tag or group was in the original HED string, find its original span.

        Parameters:
            tag_or_group (HedTag or HedGroup): The HED tag to locate in this string.

        Returns:
            int or None:   Starting position of the given item in the original string.
            int or None:   Ending position of the given item in the original string.

        Notes:
            - If the HED tag or group was not in the original string, returns (None, None).

        """
        if self._from_strings:
            return self._get_org_span_from_strings(tag_or_group)

        if self.check_if_in_original(tag_or_group):
            return tag_or_group.span

        return None, None

    def _get_org_span_from_strings(self, tag_or_group):
        """ A different case of the above, to handle if this was created from HED string objects."""
        found_string = None
        string_start_index = 0
        for string in self._from_strings:
            if string.check_if_in_original(tag_or_group):
                found_string = string
                break
            # Add 1 for comma
            string_start_index += string.span[1] + 1

        if not found_string:
            return None, None

        return tag_or_group.span[0] + string_start_index, tag_or_group.span[1] + string_start_index

    @staticmethod
    def split_hed_string(hed_string) -> list[tuple[bool, tuple[int, int]]]:
        """ Split a HED string into delimiters and tags.

        Parameters:
            hed_string (str): The HED string to split.

        Returns:
            list[tuple[bool, tuple[int, int]]]:  A list of tuples where each tuple is (is_hed_tag, (start_pos, end_pos)).

        Notes:
            - The tuple format is as follows
                - is_hed_tag (bool): A (possible) HED tag if True, delimiter if not.
                - start_pos (int):   Index of start of string in hed_string.
                - end_pos (int):     Index of end of string in hed_string.

            - This function does not validate tags or delimiters in any form.

        """
        tag_delimiters = ",()"
        current_spacing = 0
        found_symbol = True
        result_positions = []
        tag_start_pos = None
        last_end_pos = 0
        for i, char in enumerate(hed_string):
            if char == " ":
                current_spacing += 1
                continue

            if char in tag_delimiters:
                if found_symbol:
                    if last_end_pos != i:
                        result_positions.append((False, (last_end_pos, i)))
                    last_end_pos = i
                elif not found_symbol:
                    found_symbol = True
                    last_end_pos = i - current_spacing
                    result_positions.append((True, (tag_start_pos, last_end_pos)))
                    current_spacing = 0
                    tag_start_pos = None
                continue

            # If we have a current delimiter, end it here.
            if found_symbol and last_end_pos is not None:
                if last_end_pos != i:
                    result_positions.append((False, (last_end_pos, i)))
                last_end_pos = None

            found_symbol = False
            current_spacing = 0
            if tag_start_pos is None:
                tag_start_pos = i

        if last_end_pos is not None and len(hed_string) != last_end_pos:
            result_positions.append((False, (last_end_pos, len(hed_string))))
        if tag_start_pos is not None:
            result_positions.append((True, (tag_start_pos, len(hed_string) - current_spacing)))
            if current_spacing:
                result_positions.append((False, (len(hed_string) - current_spacing, len(hed_string))))

        return result_positions

    def validate(self, allow_placeholders=True, error_handler=None) -> list[dict]:
        """ Validate the string using the schema.

        Parameters:
            allow_placeholders (bool): Allow placeholders in the string.
            error_handler (ErrorHandler or None): The error handler to use, creates a default one if none passed.

        Returns:
            list[dict]: A list of issues for HED string.
        """
        from hed.validator import HedValidator

        validator = HedValidator(self._schema, def_dicts=self._def_dict)
        return validator.validate(self, allow_placeholders=allow_placeholders, error_handler=error_handler)

    def find_top_level_tags(self, anchor_tags, include_groups=2) -> list:
        """ Find top level groups with an anchor tag.

            A max of 1 tag located per top level group.

        Parameters:
            anchor_tags (container):  A list/set/etc. of short_base_tags to find groups by.
            include_groups (0, 1 or 2):  Parameter indicating what return values to include.
                If 0: return only tags.
                If 1: return only groups.
                If 2 or any other value: return both.

        Returns:
            list: The returned result depends on include_groups.
        """
        anchor_tags = {tag.casefold() for tag in anchor_tags}
        top_level_tags = []
        for group in self.groups():
            for tag in group.tags():
                if tag.short_base_tag.casefold() in anchor_tags:
                    top_level_tags.append((tag, group))
                    # Only capture a max of 1 per group.  These are implicitly unique.
                    break

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in top_level_tags]
        return top_level_tags

    def remove_refs(self):
        """ Remove any refs(tags contained entirely inside curly braces) from the string.

            This does NOT validate the contents of the curly braces.  This is only relevant when directly
            editing sidecar strings.  Tools will naturally ignore these.
        """
        ref_tags = [tag for tag in self.get_all_tags() if tag.is_column_ref()]
        if ref_tags:
            self.remove(ref_tags)
