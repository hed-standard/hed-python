from hed.models.hed_tag import HedTag
import copy
from hed.models.hed_group_base import HedGroupBase


class HedGroup(HedGroupBase):
    """ Represents a single parenthesized hed string. """

    def __init__(self, hed_string="", startpos=None, endpos=None,
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
        contents : [HedTag or HedGroup]
            A list of tags and groups that will be set as the contents of this group.
        """
        super().__init__(hed_string=hed_string, startpos=startpos, endpos=endpos)
        if contents:
            self._children = contents
        else:
            self._children = []
        self._original_children = self._children
        self.mutable = True  # If False, this group is potentially referenced in other places and should not be altered

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, HedGroup):
            return False

        if self._children != other._children:
            return False
        if self.is_group != other.is_group:
            return False
        return True

    def append(self, new_tag_or_group):
        """
        Add a tag or group to this group.

        Parameters
        ----------
        new_tag_or_group : HedTag or HedGroup
            The new object to add
        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        self._children.append(new_tag_or_group)

    def check_if_in_original_tags_and_groups(self, tag_or_group):
        """
            Checks if the tag or group was in the original string, even if it has since been removed.

        Returns
        -------

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

        if self._original_children is self._children:
            self._original_children = self._children.copy()

        replace_index = -1
        for i, child in enumerate(self._children):
            if tag_or_group is child:
                replace_index = i
                break
        self._children[replace_index] = new_contents

    def __copy__(self):
        """
            Return a shallow copy with a new _children list, rather than the same list

            Also mark the copy as mutable.

        Returns
        -------

        """
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        result._children = self._children.copy()
        result.mutable = True
        return result

    def cascade_mutable(self, value):
        """
            Sets the mutable property for all child tags and groups.

        Parameters
        ----------
        value: bool
            If they should be mutable

        Returns
        -------
        """
        self.mutable = value
        for child in self._children:
            if isinstance(child, HedGroup):
                child.cascade_mutable(value)
            else:
                child.mutable = value

    def remove_groups(self, remove_groups):
        """
            Remove any tags/groups in remove_groups found in this hed string.

            Any groups that become empty will also be pruned.

        Parameters
        ----------
        remove_groups : [HedGroup or HedTag]
            A list of groups or tags to remove.
        """
        empty_groups = []
        all_groups = self.get_all_groups()
        for remove_child in remove_groups:
            for group in all_groups:
                if remove_child in group._children:
                    if not group.mutable:
                        raise ValueError("Trying to alter immutable group")
                    if group._original_children is group._children:
                        group._original_children = group._children.copy()

                    group._children = [child for child in group._children if child is not remove_child]
                    if not group._children and group is not self:
                        empty_groups.append(group)
                    break

        if empty_groups:
            return self.remove_groups(empty_groups)

    def make_tag_mutable(self, tag):
        """
            Replace the given tag in the group with a tag you can alter.

            This is more or less exclusively for def expansion.

        Parameters
        ----------
        tag: HedTag
            The tag you want to make mutable

        Returns
        -------
        mutable_tag: HedTag
            A mutable new copy of the tag, or the old mutable one.
        """
        if not self.mutable:
            raise ValueError("Trying to alter immutable group")

        if not tag.mutable:
            tag_copy = copy.copy(tag)
            tag_copy.mutable = True
            self.replace_tag(tag, tag_copy)
            return tag_copy
        return tag

    def get_frozen(self):
        """
            Returns a frozen copy of this HedGroup.

        Returns: HedGroupFrozen
            A frozen copy of this HedGroup.  Note: tags still point to the same place.  Do not alter them.

        """
        return HedGroupFrozen(self)


class HedGroupFrozen(HedGroupBase):
    """
        This is the same as a HedGroup, except it is frozen as sets and cannot be altered further.

        Searching and getting all tags/groups will be faster.  Additionally, HedGroupFrozen is order-agnostic.
        (a, b) = (b, a)
    """
    def __init__(self, contents, hed_string=None):
        """

        Args:
            contents: HedGroup or [HedGroup or HedTag]
                If this is a group, get the source hed_string from the group.
                If a list, it gets the source hed_string from the parameter.
            hed_string: str or None
                If using a list, this is the raw string the contents came from
        """
        if isinstance(contents, HedGroupBase):
            span = contents.span
            hed_string = contents._hed_string
            contents = contents._children
        else:
            if hed_string:
                span = 0, len(hed_string)
            else:
                span = 0, 0

        super().__init__(hed_string=hed_string, startpos=span[0], endpos=span[1])
        if contents is not None:
            self._children = frozenset(child if not isinstance(child, HedGroupBase)
                                       else HedGroupFrozen(child) for child in contents)
        else:
            self._children = None

    def __hash__(self):
        return hash((self._children, self.is_group))

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, HedGroupFrozen):
            return False

        if self._children != other._children:
            return False

        if self.is_group != other.is_group:
            return False
        return True

    # Cache these values as we know this is frozen
    def get_all_tags(self):
        """
        Returns all the tags, including descendants.

        Returns
        -------
        tag_list: [HedTag]
            The list of all tags in this group, including descendants.
        """
        if not hasattr(self, "_tags"):
            self._tags = super().get_all_tags()

        return self._tags

    def get_all_groups(self, also_return_depth=False):
        """
        Returns all the HedGroups, including descendants and self.

        Parameters
        ----------
        also_return_depth : bool
            If True, this yields tuples(group, depth) rather than just groups

        Returns
        -------
        group_list: [HedGroup]
            The list of all HedGroups in this group, including descendants and self.
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
        """
            Returns this frozen group.  This is just used for the hed validator.

        Returns: HedGroupFrozen
            This same group.

        """
        return self
