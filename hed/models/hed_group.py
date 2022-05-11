from hed.models.hed_tag import HedTag
import copy
from hed.models.hed_group_base import HedGroupBase


class HedGroup(HedGroupBase):
    """ Represents a single parenthesized hed string. """

    def __init__(self, hed_string="", startpos=None, endpos=None, contents=None):
        """ Return an empty HedGroup object.

        Args:
            hed_string (str or None): Source hed string for this group.
            startpos (int or None):   Starting index of group(including parentheses) in hed_string.
            endpos (int or None):     Position after the end (including parentheses) in hed_string.
            contents (list or None):  A list of HedTags and/or HedGroups that will be set as the contents of this group.

        Notes:
            contents is mainly used for processing definitions.

        """

        super().__init__(hed_string=hed_string, startpos=startpos, endpos=endpos)
        if contents:
            self._children = contents
        else:
            self._children = []
        self._original_children = self._children
        self.mutable = True  # If False, this group is potentially referenced in other places and should not be altered

    def __eq__(self, other):
        """ Test if the same object or a HedGroup with same contents.

            Args:
                other (object):  Any object.

            Returns:
                bool:  True if other is the same as this HedGroup or is a HedGroup with the same contents.

        TODO: check to see if can be moved to HedGroupBase.

        """

        if self is other:
            return True
        if not isinstance(other, HedGroup):
            return False

        if self.children != other.children:
            return False
        if self.is_group != other.is_group:
            return False
        return True

    def append(self, tag_or_group):
        """ Add a tag or group to this group.

        Args:
            tag_or_group (HedTag or HedGroup): The new object to add to this group.

        Raises:
            ValueError: If a HedGroupFrozen.

        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        self._children.append(tag_or_group)

    def check_if_in_original(self, tag_or_group):
        """ Check if the tag or group was in the original string, even if it has since been removed.

        Args:
            tag_or_group (HedTag or HedGroup): The HedTag or HedGroup to be looked for in this group.

        Returns:
            bool:  True if in this group.

        Notes:
            Creates a list of full tags and groups contained in this group.

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
        """ Replace an existing tag or group in the group with a new tag, list, or group.

        Args:
            item_to_replace (HedTag or HedGroup): The item to  replace must exist or this will raise an error.
            new_contents (HedTag, HedGroup or list of HedTag and/or HedGroup): Replacement contents.

        Raises:
            ValueError:  If this HedGroup is not mutable.

        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        if self._original_children is self._children:
            self._original_children = self._children.copy()

        replace_index = -1
        for i, child in enumerate(self._children):
            if item_to_replace is child:
                replace_index = i
                break
        self._children[replace_index] = new_contents

    def __copy__(self):
        """ Return a shallow mutable copy with a new _children list, rather than the same list.

        Returns:
            HedGroup:  A mutable shallow copy of this HedGroup.

        Notes:
            The child HedTags and HedGroups are the same objects (similar to list copy).
            This operation is mainly used for handling definitions.

        TODO: Check to see if can be moved to HedGroupBase.

        """
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        result._children = self._children.copy()
        result.mutable = True
        return result

    def cascade_mutable(self, value):
        """ Set the mutable property for all child tags and groups.

        Args:
            value (bool):  True if all should be mutable, False if not.

        """
        self.mutable = value
        for child in self._children:
            if isinstance(child, HedGroup):
                child.cascade_mutable(value)
            else:
                child.mutable = value

    def remove(self, items_to_remove):
        """Remove any tags/groups in items_to_remoe found in this HedGroup.

        Args:
            items_to_remove (list):  List of HedGroups and/or HedTags to remove.

        Notes:
            Any groups that become empty will also be pruned.
            Identity, not equivalence is used in determining whether or not to remove.

        """
        all_groups = self.get_all_groups()
        self._remove(items_to_remove, all_groups)

    def _remove(self, items_to_remove, all_groups):
        """ Needs to be documented.

        Args:
            items_to_remove ( ):
            all_groups ( ):

        Returns:

        Raise:
            ValueError: ?

        """
        empty_groups = []
        for remove_child in items_to_remove:
            for group in all_groups:
                # only proceed if we have an EXACT match for this child
                if any(remove_child is child for child in group._children):
                    if not group.mutable:
                        raise ValueError("Trying to alter immutable group")
                    if group._original_children is group._children:
                        group._original_children = group._children.copy()

                    group._children = [child for child in group._children if child is not remove_child]
                    # If this was the last child, flag this group to be removed on a second pass
                    if not group._children and group is not self:
                        empty_groups.append(group)
                    break

        if empty_groups:
            return self.remove(empty_groups)

    def make_tag_mutable(self, tag):
        """ Replace the given tag in this group with a tag that can be altered and return new version.

        Args:
            tag (HedTag): The tag to make mutable.

        Returns:
            HedTag: A mutable new copy of the tag, or the old mutable one.

        Raises:
            ValueError:  If this HedGroup is not already mutable, the operation fails.

        Notes:
            This method is more or less exclusively for definition expansion.

        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        if not tag.mutable:
            tag_copy = copy.copy(tag)
            tag_copy.mutable = True
            self.replace(tag, tag_copy)
            return tag_copy
        return tag

    def get_frozen(self):
        """ Returns a frozen (non-mutable) copy of this HedGroup.

        Returns:
            HedGroupFrozen: A frozen copy of this HedGroup.

        Notes:
            The tags still point to the same place.  Do not alter them.

        """
        return HedGroupFrozen(self)


class HedGroupFrozen(HedGroupBase):
    """ This is the same as a HedGroup, except it is frozen as sets and cannot be altered further.

        Searching and getting all tags/groups will be faster.

        Additionally, HedGroupFrozen is order-agnostic: (a, b) = (b, a)

    """
    def __init__(self, contents, hed_string=None):
        """ Initialize a frozen group.

        Args:
            contents (HedGroupBase or list): Used to set the contents of this group.
                If HedGroupBase, get the source hed_string from the group.
                If a list, may be a mixture of HedTags and HedGroups. Use the hed_string parameter as the source.
            hed_string (str or None): If contents is a list, this is the raw string the contents came from.

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
            self._children = frozenset(child if not isinstance(child, HedGroupBase)
                                       else HedGroupFrozen(child) for child in contents)
            for child in self.groups():
                child._parent = self
        else:
            self._children = None


    def __hash__(self):
        """ Get a hash of this HedFrozenGroup."""
        return hash((self._children, self.is_group))

    def __eq__(self, other):
        """
        TODO:  Put in the HedGroupBase

        """
        if self is other:
            return True

        if not isinstance(other, HedGroupFrozen):
            return False

        if self._children != other._children:
            return False

        if self.is_group != other.is_group:
            return False
        return True

    def get_all_tags(self):
        """ Return all the HedTags in this group, including descendants.

        Returns:
            list: A list of all the HedTags in this group including descendants.

        Notes:
            This list is cached when initially called since its contents never change.

        """
        if not hasattr(self, "_tags"):
            self._tags = super().get_all_tags()
        return self._tags

    def get_all_groups(self, also_return_depth=False):
        """ Return all the HedGroups, including descendants and self.

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

        Notes:
            The base
        """
        return self
