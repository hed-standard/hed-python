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
        self._top_level_group = self.split_hed_string_into_groups(hed_string)

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
            group.children = [child for child in group.children if child not in remove_groups]

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
                        new_group.endpos = paren_end

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
        return str(self._top_level_group)


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
        # This is the span into the original hed string - before spaces and such are removed.
        self.span = span

        # The current output tag/text, uses org_tag if this is None.
        self._tag = None

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

        return self._hed_string[self.span[0]:self.span[1]]

    @property
    def tag(self):
        """Returns the hed tag, identical to str(self)"""
        return str(self)

    @tag.setter
    def tag(self, new_tag):
        """
            Set the tag to a new value.  Eg filling in a placeholder, short to long, etc.

        Parameters
        ----------
        new_tag : str
            New tag text
        """
        self._tag = new_tag

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
            self.children = contents
        else:
            self.children = []
        self.startpos = startpos
        self.endpos = endpos
        self.include_paren = include_paren
        self._hed_string = hed_string

    def append(self, new_tag_or_group):
        """
        Add a tag or group to this group.

        Parameters
        ----------
        new_tag_or_group : HedTag or HedGroup
            The new object to add
        """
        self.children.append(new_tag_or_group)

    def __iter__(self):
        """
        Returns an iterator over all HedTags and HedGroups that are in this group.  Not recursive.

        Returns
        -------
        iterator over the direct children, identical to get_direct_children()
        """
        return iter(self.children)

    def get_direct_children(self):
        """
        Returns an iterator over all HedTags and HedGroups that are in this group.  Not recursive.

        Returns
        -------
        iterator over the direct children
        """
        return iter(self.children)

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
                node_list = current_group_or_tag.children + node_list
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
                node_list = current_group_or_tag.children + node_list
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
        return [tag for tag in self.children if isinstance(tag, HedTag)]

    @property
    def span(self):
        """
        Return the source span of this group from the source hed_string
        Returns
        -------
        span: (int, int)
            The start and end index of the group(including parentheses) from the source string
        """
        return self.startpos, self.endpos

    def __str__(self):
        """
        Convert this HedGroup to a string

        Returns
        -------
        str
            Returns the group as a string, including any modified HedTags
        """
        if self.include_paren:
            return "(" + ",".join([str(child) for child in self.children]) + ")"
        else:
            return ",".join([str(child) for child in self.children])

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def replace_tag_object(self, old_tag, new_tag_or_group):
        """
        Takes a given HedTag(exact match, not string comparison) and replaces it with the specified one

        Parameters
        ----------
        old_tag : HedTag
            The HedTag to replace
        new_tag_or_group : HedTag or HedGroup
            What to replace the tag with
        """
        replace_index = self.children.index(old_tag)
        self.children[replace_index] = new_tag_or_group

    def set_contents(self, new_contents):
        """
        Sets the children of this HedGroup to be the passed in list

        Parameters
        ----------
        new_contents : [HedTag or HedGroup]
            The new contents of this group, obliterating any existing contents.
        """
        self.children = new_contents