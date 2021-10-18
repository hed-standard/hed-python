from hed.schema.hed_tag import HedTag


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
        self._original_children = self._children
        self._startpos = startpos
        self._endpos = endpos
        self._include_paren = include_paren
        self._hed_string = hed_string
        self.is_definition = False

    def append(self, new_tag_or_group):
        """
        Add a tag or group to this group.

        Parameters
        ----------
        new_tag_or_group : HedTag or HedGroup
            The new object to add
        """
        self._children.append(new_tag_or_group)

    def __bool__(self):
        return bool(self._children)

    def get_direct_children(self):
        """
        Returns an iterator over all HedTags and HedGroups that are in this group.  Not recursive.

        Returns
        -------
        iterator over the direct children
        """
        return self._children

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

    def get_original_tags_and_groups(self):
        """
            Returns all original tags and groups.  Applies if a tag was deleted or replaced

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
        return final_list

    def is_group(self):
        """
            This is a hed string contained by parenthesis.

        Returns
        -------

        """
        return self._include_paren

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
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = current_group_or_tag._children + node_list
                final_list.append(current_group_or_tag)

        if also_return_depth:
            top_groups = self.groups()

            final_list = [(group, group in top_groups) for group in final_list]
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

    def groups(self):
        """
        Returns the direct child groups of this group, filtering out HedTag children

        Returns
        -------
        group_list: [HedGroup]
            The list of all tags directly in this group.
        """
        return [group for group in self._children if isinstance(group, HedGroup)]

    def get_original_hed_string(self):
        """
            Get the original hed string with zero modification

        Returns
        -------
        hed_string: str
            The original string
        """
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
        return ",".join([str(child) for child in self._children])

    def get_as_short(self):
        """
        Convert this HedGroup to a short tag string

        Returns
        -------
        str
            Returns the group as a string, returning all tags as short tags.
        """
        return self.get_as_form("short_tag")

    def get_as_long(self):
        """
        Convert this HedGroup to a long tag string

        Returns
        -------
        str
            Returns the group as a string, returning all tags as long tags.
        """
        return self.get_as_form("long_tag")

    def get_as_form(self, tag_attribute, tag_transformer=None):
        """

        Parameters
        ----------
        tag_attribute : str
            The hed_tag property to use to construct the string.  Most commonly short_tag or long_tag.
        tag_transformer: func or None
            A function that is applied to each tag string before returning.
            signature: str def(HedTag, str)
        Returns
        -------
        group_as_string: str
            The constructed string
        """
        if tag_transformer:
            result = ",".join([tag_transformer(child, child.__getattribute__(tag_attribute))
                               if isinstance(child, HedTag) else child.get_as_form(tag_attribute, tag_transformer)
                               for child in self._children])
        else:
            result = ",".join([child.__getattribute__(tag_attribute) if isinstance(child, HedTag) else
                               child.get_as_form(tag_attribute) for child in self._children])
        if self._include_paren:
            return f"({result})"
        return result

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
        if self._original_children is self._children:
            self._original_children = self._children.copy()
        new_object = new_contents
        if isinstance(new_contents, list):
            new_object = HedGroup(tag._hed_string, startpos=tag.span[0], endpos=tag.span[1], contents=new_contents)

        replace_index = self._children.index(tag)
        self._children[replace_index] = new_object

    def remove_groups(self, remove_groups):
        """
        Takes a list of HedGroups, and removes any that exist from this HedString.

        Parameters
        ----------
        remove_groups : [HedGroup or HedTag]
            A list of groups or tags to remove
        """
        if self._original_children is self._children:
            self._original_children = self._children.copy()

        if self in remove_groups:
            self._children = []
            self._hed_string = ""
            return

        for group in self.get_all_groups():
            group._children = [child for child in group._children if child not in remove_groups]

    def replace_placeholder(self, placeholder_value):
        """
            Replace any placeholders with the given value.

        Parameters
        ----------
        placeholder_value : str
            The placeholder value to fill in

        Returns
        -------
        """
        for tag in self.get_all_tags():
            tag.replace_placeholder(placeholder_value)

    def without_defs(self):
        """
            Return this as a string, with definitions having been removed.

        Returns
        -------

        """
        if self._include_paren:
            return "(" + ",".join([str(child) for child in self._children if not child.is_definition]) + ")"
        return ",".join([str(child) for child in self._children if not child.is_definition])
