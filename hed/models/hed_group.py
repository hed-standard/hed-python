from hed.models.hed_tag import HedTag
from hed.models.hed_group_base import HedGroupBase
import copy


class HedGroup(HedGroupBase):
    """ A single parenthesized hed string. """

    def __init__(self, hed_string="", startpos=None, endpos=None, contents=None):
        """ Return an empty HedGroup object.

        Args:
            hed_string (str or None): Source hed string for this group.
            startpos (int or None):   Starting index of group(including parentheses) in hed_string.
            endpos (int or None):     Position after the end (including parentheses) in hed_string.
            contents (list or None):  A list of HedTags and/or HedGroups that will be set as the contents of this group.

        Notes:
            - contents parameter is mainly used for processing definitions.

        """

        super().__init__(hed_string=hed_string, startpos=startpos, endpos=endpos)
        if contents:
            self._children = contents
            for child in self._children:
                child._parent = self
        else:
            self._children = []
        self._original_children = self._children

    def append(self, tag_or_group):
        """ Add a tag or group to this group.

        Args:
            tag_or_group (HedTag or HedGroup): The new object to add to this group.

        Raises:
            ValueError: If a HedGroupFrozen.

        """
        tag_or_group._parent = self
        self._children.append(tag_or_group)

    def check_if_in_original(self, tag_or_group):
        """ Check if the tag or group in original string.

        Args:
            tag_or_group (HedTag or HedGroup): The HedTag or HedGroup to be looked for in this group.

        Returns:
            bool:  True if in this group.
        """
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = current_group_or_tag._original_children + node_list
            final_list.append(current_group_or_tag)

        return self._check_in_group(tag_or_group, final_list)

    def replace(self, item_to_replace, new_contents):
        """ Replace an existing tag or group.

        Args:
            item_to_replace (HedTag or HedGroup): The item to replace must exist or this will raise an error.
            new_contents (HedTag or HedGroup): Replacement contents.

        """
        if self._original_children is self._children:
            self._original_children = self._children.copy()

        replace_index = -1
        for i, child in enumerate(self._children):
            if item_to_replace is child:
                replace_index = i
                break
        self._children[replace_index] = new_contents
        new_contents._parent = self

    def remove(self, items_to_remove):
        """ Remove any tags/groups in items_to_remove.

        Args:
            items_to_remove (list):  List of HedGroups and/or HedTags to remove.

        Notes:
            - Any groups that become empty will also be pruned.
            - Identity, not equivalence is used in determining whether to remove.

        """
        all_groups = self.get_all_groups()
        self._remove(items_to_remove, all_groups)

    def _remove(self, items_to_remove, all_groups):
        """ Needs to be documented.

        Args:
            items_to_remove (list):  List of HedGroups and/or HedTags to remove.
            all_groups (list):   List of HedGroups.

        """
        empty_groups = []
        for remove_child in items_to_remove:
            for group in all_groups:
                # only proceed if we have an EXACT match for this child
                if any(remove_child is child for child in group._children):
                    if group._original_children is group._children:
                        group._original_children = group._children.copy()

                    group._children = [child for child in group._children if child is not remove_child]
                    # If this was the last child, flag this group to be removed on a second pass
                    if not group._children and group is not self:
                        empty_groups.append(group)
                    break

        if empty_groups:
            self.remove(empty_groups)

    def get_frozen(self):
        """ Return a frozen (non-mutable) copy of this HedGroup.

            This is a deep copy if the group was not already frozen.

        Returns:
            HedGroupFrozen: A frozen copy of this HedGroup.
        """
        return HedGroupFrozen(self)


class HedGroupFrozen(HedGroupBase):
    """ A frozen version of the HedGroup.

    Notes:
        - Searching and getting all tags/groups will be faster.
        - Additionally, HedGroupFrozen is order-agnostic: (a, b) = (b, a).

    """
    def __init__(self, contents, hed_string=None):
        """ Initialize a frozen group.

        Args:
            contents (HedGroupBase or list): Used to set the contents of this group.
            hed_string (str or None): If contents is a list, this is the raw string the contents came from.

        Notes:
            - This makes a complete copy of the HedString.
            - If HedGroupBase, get the source hed_string from the group.
            - If a list, may be a mixture of HedTags and HedGroups. Use the hed_string parameter as the source.

        """
        if isinstance(contents, HedGroupBase):
            span = contents.span
            hed_string = contents._hed_string
            contents = contents.children
        else:
            if hed_string:
                span = 0, len(hed_string)
            else:
                span = 0, 0

        # Possibly temporary: Have frozen groups always know their parents
        self._parent = None

        super().__init__(hed_string=hed_string, startpos=span[0], endpos=span[1])
        if contents is not None:
            self._children = frozenset(copy.copy(child) if not isinstance(child, HedGroupBase)
                                       else HedGroupFrozen(child) for child in contents)
            for child in self._children:
                child._parent = self
        else:
            self._children = None

    def __hash__(self):
        """ Get a hash of this HedFrozenGroup. """
        return hash((self._children, self.is_group))

    def get_all_tags(self):
        """ Return HedTags, including descendants.

        Returns:
            list: A list of all the HedTags in this group including descendants.

        Notes:
            - This list is cached when initially called since its contents never change.

        """
        if not hasattr(self, "_tags"):
            self._tags = super().get_all_tags()
        return self._tags

    def get_all_groups(self, also_return_depth=False):
        """ Return HedGroups, including descendants and self.

        Args:
            also_return_depth (bool): If True, this yields tuples (group, depth) rather than just groups.

        Returns:
            list: The list of all HedGroups in this group, including descendants and self.

        """
        if also_return_depth:
            if not hasattr(self, "_groups1"):
                self._groups1 = super().get_all_groups(also_return_depth=also_return_depth)
            return self._groups1
        else:
            if not hasattr(self, "_groups2"):
                self._groups2 = super().get_all_groups(also_return_depth=also_return_depth)
            return self._groups2

    def get_frozen(self):
        """ Return this frozen group.

        Returns:
            HedGroupFrozen: This same group.
        """
        return self
