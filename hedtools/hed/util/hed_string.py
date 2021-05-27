"""
This module is used to split tags in a HED string.
"""

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


class HedGroup:
    """
        A single HedGroup in a string, containing HedTags and HedGroups
    """
    def __init__(self, hed_string="", startpos=None, endpos=None, include_paren=True,
                 contents=None):
        """
        Returns an empty HedGroup object

        Parameters
        ----------
        hed_string : str
            Source hed string for this group
        startpos : int
            Starting index of group(including parentheses) in hed_string
        endpos : int
            Ending index of group(including parentheses) in hed_string
        include_paren : bool
            If False, this group does not have parentheses(only relevant for top level groups)
        contents : [HedTag or HedGroup]
            A list of tags and groups that will be set as the contents of this group.
        """
        if contents:
            self._children = contents
        else:
            self._children = []
        self._startpos = startpos
        self._endpos = endpos
        self._include_paren = include_paren
        self._hed_string = hed_string

    def append(self, new_tag_or_group):
        """
        Add a tag or group to this group.

        Parameters
        ----------
        new_tag_or_group : HedTag or HedGroup
            The new object to add
        """
        self._children.append(new_tag_or_group)

    def __iter__(self):
        """
        Returns an iterator over all HedTags and HedGroups that are in this group.  Not recursive.

        Returns
        -------
        iterator over the direct children, identical to get_direct_children()
        """
        return iter(self._children)

    def get_direct_children(self):
        """
        Returns an iterator over all HedTags and HedGroups that are in this group.  Not recursive.

        Returns
        -------
        iterator over the direct children
        """
        return iter(self._children)

    def get_all_tags(self):
        """
        Returns all the tags, including descendants.

        Returns
        -------
        tag_list: [HedTag]
            The list of all tags in this group, including descendants.
        """
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = current_group_or_tag._children + node_list
            else:
                final_list.append(current_group_or_tag)
        return final_list

    def get_all_groups(self):
        """
        Returns all the HedGroups, including descendants and self.

        Returns
        -------
        group_list: [HedGroup]
            The list of all HedGroups in this group, including descendants and self.
        """
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = current_group_or_tag._children + node_list
                final_list.append(current_group_or_tag)

        return final_list

    def tags(self):
        """
        Returns the direct child tags of this group, filtering out HedGroup children

        Returns
        -------
        tag_list: [HedTag]
            The list of all tags directly in this group.
        """
        return [tag for tag in self._children if isinstance(tag, HedTag)]

    def get_original_hed_string(self):
        return self._hed_string[self._startpos:self._endpos]

    @property
    def span(self):
        """
        Return the source span of this group from the source hed_string
        Returns
        -------
        span: (int, int)
            The start and end index of the group(including parentheses) from the source string
        """
        return self._startpos, self._endpos

    def __str__(self):
        """
        Convert this HedGroup to a string

        Returns
        -------
        str
            Returns the group as a string, including any modified HedTags
        """
        if self._include_paren:
            return "(" + ",".join([str(child) for child in self._children]) + ")"
        else:
            return ",".join([str(child) for child in self._children])

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def replace_tag(self, tag, new_contents):
        """ Replaces an existing tag in the group with a new tag, list, or group

        Parameters
        ----------
        tag : HedTag
            The tag to replace.  It must exist or this will raise an error.
        new_contents : HedTag or HedGroup or [HedTag or HedGroup]
            What to replace the tag with.
        """
        new_object = new_contents
        if isinstance(new_contents, list):
            new_object = HedGroup(tag._hed_string, startpos=tag.span[0], endpos=tag.span[1], contents=new_contents)

        replace_index = self._children.index(tag)
        self._children[replace_index] = new_object
