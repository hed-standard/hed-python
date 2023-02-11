"""
    This module is used to easily concatenate multiple hed strings in place
"""
from hed.models.hed_string import HedString


class HedStringGroup(HedString):
    """ A container with hed string objects.

    Notes:
        - Often this is used for assembling the hed strings from multiple columns.
        - The HedStringGroup passes through many of the HedString operations.

    """

    def __init__(self, hed_string_obj_list):
        """ Constructor for the HedStringGroup class.

        Parameters:
            hed_string_obj_list ([HedString]): A list of component HedStrings for this combined string.

        """
        super().__init__("")
        self._children = list(hed_string for hed_string in hed_string_obj_list if hed_string is not None)
        # Update the direct children to point to this combined string, rather than their original string
        for child in self._children:
            for sub_child in child.children:
                sub_child._parent = self

        self._original_children = self._children

    def get_original_hed_string(self):
        return "".join([group._hed_string for group in self._children])

    def sort(self):
        combined_string = HedString.from_hed_strings(self._children)
        combined_string.sorted(update_self=True)
        return combined_string

    @property
    def span(self):
        """ Return the source span of this group from the source hed string.

        Return:
            tuple:
                - int: start index of the group (including parentheses) from the source string.
                - int: end index of the group (including parentheses) from the source string.

        """
        return 0, len(self.get_original_hed_string())

    @property
    def children(self):
        """ Return the direct children of this string.

        Returns:
            list: a list of direct children of this group.

        """
        return [child for sub_string in self._children for child in sub_string._children]

    def remove(self, items_to_remove):
        """ Remove any tags/groups in items_to_remove.

        Parameters:
            items_to_remove (list): A list of HedGroup and HedTag objects to remove.

        Notes:
            - Any groups that become empty will also be pruned.
            - This goes by identity, not equivalence.

        """
        all_groups = [group for sub_group in self._children for group in sub_group.get_all_groups()]
        self._remove(items_to_remove, all_groups)
        # Remove any lingering empty HedStrings
        if any(not hed_string for hed_string in self._children):
            if self._original_children is self._children:
                self._original_children = self._children.copy()
            self._children = [child for child in self._children if child]

    def replace(self, item_to_replace, new_contents):
        """ Replace an existing tag or group.

        Parameters:
            item_to_replace (HedTag or HedGroup): The tag to replace.
            new_contents (HedTag or HedGroup or list): The replacements for the tag.

        Notes:
            - It tag must exist in this an error is raised.

        """

        # this needs to pass the tag off to the appropriate group
        replace_sub_string = None
        for sub_string in self._children:
            for i, child in enumerate(sub_string.children):
                if item_to_replace is child:
                    replace_sub_string = sub_string
                    break

        replace_sub_string.replace(item_to_replace, new_contents)

    def _get_org_span(self, tag_or_group):
        """ If this tag or group was in the original hed string, find it's original span.

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
            if string.check_if_in_original(tag_or_group):
                found_string = string
                break
            # Add 1 for comma
            string_start_index += string.span[1] + 1

        if not found_string:
            return None, None

        return tag_or_group.span[0] + string_start_index, tag_or_group.span[1] + string_start_index
