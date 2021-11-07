"""
This module is used to split tags in a HED string.
"""
from hed.models.hed_group import HedGroup
from hed.schema.hed_tag import HedTag
from hed.errors.error_reporter import ErrorHandler, check_for_any_errors
from hed.errors.error_types import ErrorContext
from hed.models.util import translate_ops
from hed.models.model_constants import DefTagNames


class HedString(HedGroup):
    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'

    def __init__(self, hed_string):
        """Constructor for the HedString class.

            raises ValueError if the string cannot be parsed due to bad groups.

        Parameters
        ----------
        hed_string: str
            A HED string consisting of tags and tag groups.
        Returns
        -------
        """
        # This is a tree like structure containing the entire hed string
        hed_string = self._clean_hed_string(hed_string)

        # The sub HedStrings that make up this object.  Empty if this is the lowest level one.
        self._component_strings = []
        try:
            contents = self.split_hed_string_into_groups(hed_string)
        except ValueError:
            contents = []

        super().__init__(hed_string, include_paren=False, contents=contents, startpos=0, endpos=len(hed_string))

    @staticmethod
    def create_from_other(hed_string_obj_list):
        """
            Creates a hed string from a list of hed strings.

            Note: This does not allocate new tags for the new strings, they point to the same internal tags.

        Parameters
        ----------
        hed_string_obj_list : [HedString]
            The list of strings to combine

        Returns
        -------
        combined_hed_string_obj: HedString
            The combined hed string, containing all tags and delimiters from the list
        """
        hed_string_obj_list = [hed_string_obj for hed_string_obj in hed_string_obj_list if hed_string_obj is not None]
        new_hed_string_obj = HedString("")
        for hed_string_obj in hed_string_obj_list:
            new_hed_string_obj._children += hed_string_obj._children
        new_hed_string_obj._component_strings = list(hed_string_obj_list)

        hed_string = ",".join([hed_string_obj._hed_string for hed_string_obj in hed_string_obj_list])
        new_hed_string_obj._hed_string = hed_string
        new_hed_string_obj._startpos = 0
        new_hed_string_obj._endpos = len(hed_string)
        new_hed_string_obj._include_paren = False

        return new_hed_string_obj

    def convert_to_canonical_forms(self, hed_schema):
        """
            Identify all tags using the given schema.  If no schema, still identify "key" tags such as definitions.

            Also sets the "isDefinition" property on tags and groups.

        Parameters
        ----------
        hed_schema : HedSchema or None
            The schema to use to validate/convert tags.

        Returns
        -------
        conversion_issues: [{}]
            A list of issues found while converting the string.
        """
        validation_issues = []
        for tag in self.get_all_tags():
            validation_issues += tag.convert_to_canonical_forms(hed_schema)

        self._identify_definitions()
        return validation_issues

    def _identify_definitions(self):
        """
            Mark any definitions found in this string.  Including groups or tags that are part of a definition.

            This should possibly be removed later.

        Returns
        -------

        """
        for tag_group in self.groups():
            for tag in tag_group.tags():
                if tag.short_base_tag.lower() == DefTagNames.DEFINITION_KEY:
                    for def_tag in tag_group.get_all_tags():
                        def_tag.is_definition = True
                    tag_group.is_definition = True

    def remove_definitions(self):
        """
            Removes any definition tags and groups from this string.

        Returns
        -------
        issues: [{}]
            There are no possible issues, this list is always blank.
        """
        definition_groups = []
        for tag_group in self.get_all_groups():
            if tag_group.is_definition:
                definition_groups.append(tag_group)

        if definition_groups:
            self.remove_groups(definition_groups)

        return []

    def convert_to_short(self, hed_schema):
        """
            Compute string canonical forms and return the long form and issues.

        Parameters
        ----------
        hed_schema : HedSchema or None
            The schema to use to calculate forms.
        Returns
        -------
        short_form: str
            The string with all tags converted to short form
        conversion_issues: [{}]
            Issues found during conversion.  No issues will be found if no schema is passed.
        """
        conversion_issues = self.convert_to_canonical_forms(hed_schema)
        short_string = self.get_as_short()
        return short_string, conversion_issues

    def convert_to_long(self, hed_schema):
        """
            Compute string canonical forms and return the long form and issues.

        Parameters
        ----------
        hed_schema : HedSchema or None
            The schema to use to calculate forms.
        Returns
        -------
        long_form: str
            The string with all tags converted to long form
        conversion_issues: [{}]
            Issues found during conversion.  No issues will be found if no schema is passed.
        """
        conversion_issues = self.convert_to_canonical_forms(hed_schema)
        short_string = self.get_as_long()
        return short_string, conversion_issues

    def convert_to_original(self):
        """
            Returns the original form of this string, though potentially with some extraneous spaces removed.

        Returns
        -------
        org_string: str
            The string with all the tags in their original form.
        """
        return self.get_as_form("org_tag")

    @staticmethod
    def split_hed_string_into_groups(hed_string):
        """Splits the hed_string into a tree of tag groups, tags, and delimiters.

        Parameters
        ----------
        hed_string
            A hed string consisting of tags and tag groups.
        Returns
        -------

        """
        # Stack variable while processing
        current_tag_group = [[]]

        input_tags = HedString.split_hed_string(hed_string)
        for is_hed_tag, (startpos, endpos) in input_tags:
            if is_hed_tag:
                new_tag = HedTag(hed_string, (startpos, endpos))
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
                        raise ValueError(f"Closing parentheses in hed string {hed_string}")

        # Comma delimiter issues are ignored and assumed already validated currently.
        if len(current_tag_group) != 1:
            raise ValueError(f"Unmatched opening parentheses in hed string {hed_string}")

        return current_tag_group[0]

    @staticmethod
    def _clean_hed_string(hed_string):
        return hed_string.replace("\n", " ")

    def _get_org_span(self, tag_or_group):
        """
            If this tag or group was in the original hed string, find it's original span.

            This handles all cases of strings, including hed strings made of other hed strings.

            If the hed tag or group was not in the original string, returns (None, None)

        Parameters
        ----------
        tag_or_group : HedTag or HedGroup
            The hed tag to locate in this string.

        Returns
        -------
        tag_span: (int or None, int or None)
            The starting and ending index of the given tag in the original string
        """
        strings_list = self._component_strings
        found_string = None
        string_start_index = 0
        if not self._component_strings:
            if tag_or_group in self.get_original_tags_and_groups():
                return tag_or_group.span
        for string in strings_list:
            if tag_or_group in string.get_original_tags_and_groups():
                found_string = string
                break
            # Add 1 for comma
            string_start_index += string.span[1] + 1

        if not found_string:
            return None, None

        return tag_or_group.span[0] + string_start_index, tag_or_group.span[1] + string_start_index

    @staticmethod
    def split_hed_string(hed_string):
        """
        Takes a hed string and splits it into delimiters and tags

        Note: This does not validate tags or delimiters in any form.

        Parameters
        ----------
            hed_string: string
                the hed string to split
        Returns
        -------
        [tuple]
            each tuple: (is_hed_tag, (start_pos, end_pos))
            is_hed_tag: bool
                This is a (possible) hed tag if true, delimiter if not
            start_pos: int
                index of start of string in hed_string
            end_pos: int
                index of end of string in hed_string
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
                    # view_string = hed_string[last_end_pos: i]
                    if last_end_pos != i:
                        result_positions.append((False, (last_end_pos, i)))
                    last_end_pos = i
                elif not found_symbol:
                    found_symbol = True
                    last_end_pos = i - current_spacing
                    # view_string = hed_string[tag_start_pos: last_end_pos]
                    result_positions.append((True, (tag_start_pos, last_end_pos)))
                    current_spacing = 0
                    tag_start_pos = None
                continue

            # If we have a current delimiter, end it here.
            if found_symbol and last_end_pos is not None:
                # view_string = hed_string[last_end_pos: i]
                if last_end_pos != i:
                    result_positions.append((False, (last_end_pos, i)))
                last_end_pos = None

            found_symbol = False
            current_spacing = 0
            if tag_start_pos is None:
                tag_start_pos = i

        if last_end_pos is not None and len(hed_string) != last_end_pos:
            # view_string = hed_string[last_end_pos: len(hed_string)]
            result_positions.append((False, (last_end_pos, len(hed_string))))
        if tag_start_pos is not None:
            # view_string = hed_string[tag_start_pos: len(hed_string)]
            result_positions.append((True, (tag_start_pos, len(hed_string) - current_spacing)))
            if current_spacing:
                result_positions.append((False, (len(hed_string) - current_spacing, len(hed_string))))

        return result_positions

    @staticmethod
    def split_hed_string_return_tags(hed_string):
        """
        An easier to use variant of split_hed_string if you're only interested in tags

        Parameters
        ----------
        hed_string : str
            A hed string to split into tags
        Returns
        -------
        hed_tags: [HedTag]
            The string split apart into hed tags with all delimiters removed
        """
        result_positions = HedString.split_hed_string(hed_string)
        return [HedTag(hed_string, span) for (is_hed_tag, span) in
                result_positions if is_hed_tag]

    def apply_ops(self, string_ops):
        """
            Run the list of functions on this string and gather up issues found.

            This potentially modifies the hed string object.

        Parameters
        ----------
        string_ops : [func]
            A list of functions that take a hed string object and return a list of issues.

        Returns
        -------
        issues_list: [{}]
            A list of issues found by these operations
        """
        string_issues = []
        for string_validator in string_ops:
            string_issues += string_validator(self)
            if string_issues:
                if check_for_any_errors(string_issues):
                    break

        return string_issues

    def validate(self, validators=None, error_handler=None, **kwargs):
        """
            Run the given validators on this string.

        Parameters
        ----------
        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in this sidecar.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        kwargs:
            See util.translate_ops or the specific validators for additional options

        Returns
        -------

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        tag_ops = translate_ops(validators, **kwargs)

        error_handler.push_error_context(ErrorContext.HED_STRING, self, increment_depth_after=False)
        issues = self.apply_ops(tag_ops)
        error_handler.add_context_to_issues(issues)
        error_handler.pop_error_context()

        return issues
