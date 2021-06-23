"""
This module is used to split tags in a HED string.
"""
from hed.models.hed_group import HedGroup
from hed.models.hed_tag import HedTag


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
        try:
            contents, self._flat_tags = self.split_hed_string_into_groups(hed_string, also_return_flat_version=True)
        except ValueError:
            contents = []
            self._flat_tags = []

        super().__init__(hed_string, include_paren=False, contents=contents)

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
        new_hed_string_obj = HedString("")
        first_one = True
        for hed_string_obj in hed_string_obj_list:
            if not first_one:
                new_hed_string_obj._flat_tags.append(",")
            first_one = False
            new_hed_string_obj._flat_tags += hed_string_obj._flat_tags
            new_hed_string_obj._children += hed_string_obj._children

        hed_string = ",".join([hed_string_obj._hed_string for hed_string_obj in hed_string_obj_list])
        new_hed_string_obj._hed_string = hed_string
        new_hed_string_obj._startpos = 0
        new_hed_string_obj._endpos = len(hed_string)
        new_hed_string_obj._include_paren = False

        return new_hed_string_obj

    def convert_to_canonical_forms(self, hed_schema, error_handler=None):
        if not hed_schema:
            return []

        validation_issues = []
        for tag in self.get_all_tags():
            validation_issues += tag.convert_to_canonical_forms(hed_schema, error_handler)
        return validation_issues

    def convert_to_short(self, hed_schema, error_handler=None):
        once = True
        conversion_issues = []
        for tag in self.get_all_tags():
            if tag._short_tag_index is None and once:
                once = False
                conversion_issues = self.convert_to_canonical_forms(hed_schema, error_handler=error_handler)
            tag._tag = tag.short_tag
        return conversion_issues

    def convert_to_long(self, hed_schema, error_handler=None):
        once = True
        conversion_issues = []
        for tag in self.get_all_tags():
            if tag._short_tag_index is None and once:
                once = False
                conversion_issues = self.convert_to_canonical_forms(hed_schema, error_handler=error_handler)
            tag._tag = tag.long_tag
        return conversion_issues

    def convert_to_original(self):
        conversion_issues = []
        for tag in self.get_all_tags():
            tag._tag = tag.org_tag
        return conversion_issues

    @staticmethod
    def split_hed_string_into_groups(hed_string, also_return_flat_version=False):
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
        flat_tags = []

        input_tags = HedString.split_hed_string(hed_string)
        for is_hed_tag, (startpos, endpos) in input_tags:
            if is_hed_tag:
                new_tag = HedTag(hed_string, (startpos, endpos))
                current_tag_group[-1].append(new_tag)
                flat_tags.append(new_tag)
            else:
                string_portion = hed_string[startpos:endpos]
                flat_tags.append(string_portion)
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

        if also_return_flat_version:
            return current_tag_group[0], flat_tags
        return current_tag_group[0]

    @staticmethod
    def _clean_hed_string(hed_string):
        return hed_string.replace("\n", " ")

    def _get_org_tag_span(self, tag):
        """
            If this tag was in the original hed string, find it's original span.

            If the hed tag was not in the original string, returns (None, None)

        Parameters
        ----------
        tag : HedTag
            The hed tag to locate in this string.

        Returns
        -------
        tag_span: (int or None, int or None)
            The starting and ending index of the given tag in the original string
        """
        tag_list = self._flat_tags
        try:
            tag_index = tag_list.index(tag)
        except ValueError:
            # Mainly a concern for replaced groups(is that a concern?)
            return None, None

        final_string = ""
        if tag_index > 0:
            final_tag_list = tag_list[:tag_index]
            final_string += "".join(text if isinstance(text, str) else text.org_tag for text in final_tag_list)


        length = len(final_string)
        return length, length + len(tag_list[tag_index].org_tag)

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
        from hed.models.hed_tag import HedTag
        result_positions = HedString.split_hed_string(hed_string)
        return [HedTag(hed_string, span) for (is_hed_tag, span) in
                result_positions if is_hed_tag]