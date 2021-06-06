"""
This module is used to split tags in a HED string.
"""
from hed.models.hed_group import HedGroup
from hed.models.hed_tag import HedTag
from hed.util import hed_string_util


class HedString:
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
        # The original hed string(all clean does is remove new lines)
        self.hed_string = self._clean_hed_string(hed_string)

        # This is a tree like structure containing the entire hed string
        try:
            self._top_level_group = self.split_hed_string_into_groups(hed_string)
        except ValueError:
            self._top_level_group = None

    @staticmethod
    def create_from_other(hed_string_obj_list):
        hed_string = ",".join([hed_string_obj.hed_string for hed_string_obj in hed_string_obj_list])
        new_hed_string_obj = HedString("")
        new_hed_string_obj.hed_string = hed_string
        children = []
        for hed_string_obj in hed_string_obj_list:
            children += hed_string_obj._top_level_group.get_direct_children()
        new_hed_string_obj._top_level_group = HedGroup(hed_string, 0, len(hed_string),
                                                       include_paren=False, contents=children)

        return new_hed_string_obj

    def get_all_groups(self):
        """
        Returns all tag groups, including the top level one with no parentheses

        Returns
        -------
        group_list: [HedGroup]
            A list of all groups
        """
        return self._top_level_group.get_all_groups()

    def get_all_tags(self):
        """
        Returns all tags, regardless of group level.

        Returns
        -------
        tag_list: [HedTag]
            A list of all tags
        """
        return self._top_level_group.get_all_tags()

    def get_original_hed_string(self):
        """Gets the original input hed string.

        Returns
        -------
        str
            The hed string associated with the object.
        """
        return self.hed_string

    def calculate_canonical_forms(self, hed_schema, error_handler=None):
        if not hed_schema:
            return []

        validation_issues = []
        for tag in self.get_all_tags():
            long_form, short_index, tag_issues = hed_schema._convert_to_canonical_tag(tag, error_handler)
            tag._long_tag = long_form
            tag._short_tag_index = short_index
            validation_issues += tag_issues

        return validation_issues

    def convert_to_short(self, hed_schema, error_handler=None):
        once = True
        conversion_issues = []
        for tag in self.get_all_tags():
            if tag._short_tag_index is None and once:
                once = False
                conversion_issues = self.calculate_canonical_forms(hed_schema, error_handler=error_handler)
            tag._tag = tag.short_tag
        return conversion_issues

    def convert_to_long(self, hed_schema, error_handler=None):
        once = True
        conversion_issues = []
        for tag in self.get_all_tags():
            if tag._short_tag_index is None and once:
                once = False
                conversion_issues = self.calculate_canonical_forms(hed_schema, error_handler=error_handler)
            tag._tag = tag.long_tag
        return conversion_issues

    def convert_to_original(self):
        conversion_issues = []
        for tag in self.get_all_tags():
            tag._tag = tag.org_tag
        return conversion_issues

    def remove_groups(self, remove_groups):
        """
        Takes a list of HedGroups, and removes any that exist from this HedString.

        Parameters
        ----------
        remove_groups : [HedGroup or HedTag]
            A list of groups or tags to remove
        """
        if self._top_level_group in remove_groups:
            self._top_level_group = HedGroup(include_paren=False)
            return

        for group in self.get_all_groups():
            group._children = [child for child in group._children if child not in remove_groups]

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
        current_tag_group = [HedGroup(hed_string, include_paren=False)]

        input_tags = hed_string_util.split_hed_string(hed_string)
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

    def __str__(self):
        """
            Converts this back to a string, including any modifications to tags or groups

        Returns
        -------
        hed_string: str
            The updated hed string
        """
        if self._top_level_group:
            return str(self._top_level_group)
        else:
            return self.hed_string

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()
