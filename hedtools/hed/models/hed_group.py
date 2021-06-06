from hed.models.hed_tag import HedTag


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