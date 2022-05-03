"""
    This module is used to easily concatenate multiple hed strings in place
"""
from hed.models.hed_string import HedString


class HedStringComb(HedString):
    """Represents a hed string made from other hed strings(generally multiple columns)."""

    def __init__(self, hed_string_obj_list):
        """Constructor for the HedStringComb class.

        Parameters
        ----------
        hed_string_obj_list: [HedString]
            A list of component HedStrings for this combined

        Returns
        -------
        """
        super().__init__("")
        self._children = list(hed_string for hed_string in hed_string_obj_list if hed_string is not None)
        self._original_children = self._children

    def get_original_hed_string(self):
        return "".join([group._hed_string for group in self._children])

    @property
    def span(self):
        """ Return the source span of this group from the source hed string.

        Return:
            int: start index of the group (including parentheses) from the source string.
            int: end index of the group (including parentheses) from the source string.
        """
        return 0, len(self.get_original_hed_string())

    @property
    def children(self):
        """ Returns the direct children of this string.

        Returns:
            The list of direct children of this group
        """
        return [child for sub_string in self._children for child in sub_string._children]

    def remove_groups(self, remove_groups):
        """
            Remove any tags/groups in remove_groups found in this hed string.

            Any groups that become empty will also be pruned.

            Note: this goes by identity, not equivalence.

        Parameters
        ----------
        remove_groups : [HedGroup or HedTag]
            A list of groups or tags to remove.
        """
        all_groups = [group for sub_group in self._children for group in sub_group.get_all_groups()]
        self._remove_groups(remove_groups, all_groups)
        # Remove any lingering empty HedStrings
        if any(not hed_string for hed_string in self._children):
            if self._original_children is self._children:
                self._original_children = self._children.copy()
            self._children = [child for child in self._children if child]

    def replace_tag(self, tag_or_group, new_contents):
        """ Replaces an existing tag in the group with a new tag, list, or group

        Parameters
        ----------
        tag_or_group : HedTag or HedGroup
            The tag to replace.  It must exist or this will raise an error.
        new_contents : HedTag or HedGroup or [HedTag or HedGroup]
            What to replace the tag with.
        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        # this needs to pass the tag off to the appropriate group
        replace_sub_string = None
        for sub_string in self._children:
            for i, child in enumerate(sub_string.children):
                if tag_or_group is child:
                    replace_sub_string = sub_string
                    break

        replace_sub_string.replace_tag(tag_or_group, new_contents)

    def __copy__(self):
        """
            Returns a copy of this combined string converted to HedString

        Returns
        -------

        """
        # When we copy a combined string, just turn it into a normal string.
        result = HedString.__new__(HedString)
        result.__dict__.update(self.__dict__)
        result._startpos, result._endpos = self.span
        result._hed_string = self.get_original_hed_string()
        result._children = self.children.copy()
        result.mutable = True
        return result

    def _get_org_span(self, tag_or_group):
        """
            If this tag or group was in the original hed string, find it's original span.

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
        found_string = None
        string_start_index = 0
        for string in self._children:
            if string.check_if_in_original_tags_and_groups(tag_or_group):
                found_string = string
                break
            # Add 1 for comma
            string_start_index += string.span[1] + 1

        if not found_string:
            return None, None

        return tag_or_group.span[0] + string_start_index, tag_or_group.span[1] + string_start_index
