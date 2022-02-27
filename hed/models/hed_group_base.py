from hed.models.hed_tag import HedTag


class HedGroupBase:
    """ This is an abstract baseclass used for HedGroup API, so it's shared with HedGroupFrozen """

    def __init__(self, hed_string="", startpos=None, endpos=None):
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
        """
        self._startpos = startpos
        self._endpos = endpos
        self._hed_string = hed_string
        self.mutable = True  # If False, this group is potentially referenced in other places and should not be altered

        # placeholder just to make IDE not complain
        self._children = None

    @property
    def is_group(self):
        """
            Returns True if this is a group with parenthesis.
        """
        return True

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
            if isinstance(current_group_or_tag, HedGroupBase):
                node_list = list(current_group_or_tag._children) + node_list
            else:
                final_list.append(current_group_or_tag)
        return final_list

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
            if isinstance(current_group_or_tag, HedGroupBase):
                node_list = list(current_group_or_tag._children) + node_list
                final_list.append(current_group_or_tag)

        if also_return_depth:
            top_groups = self.groups()

            final_list = [(group, self._check_in_group(group, top_groups)) for group in final_list]
        return final_list

    @staticmethod
    def _check_in_group(group, group_list):
        for val in group_list:
            if val is group:
                return True
        return False

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
        return [group for group in self._children if isinstance(group, HedGroupBase)]

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
        if self.is_group:
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
        if self.is_group:
            return f"({result})"
        return result

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def find_placeholder_tag(self):
        """
            If a placeholder tag is present, this will return it.

            Assumes a valid HedString with no erroneous "#" characters.

        Returns
        -------
        found_tag: HedTag or None
            The placeholder tag if found.
        """
        for tag in self.get_all_tags():
            if "#" in tag.org_tag:
                return tag

        return None

    def __bool__(self):
        return bool(self._children)

    def find_tags(self, anchors, recursive=False, include_groups=2):
        """
            Find tags given anchors.

            Note: This can only find identified tags.  By default, definition, def, def-expand, onset, and offset
                are identified, even without a schema.

        Args:
            anchors: container
                A container of short_base_tags to locate
            recursive: bool
                If true, also check subgroups.
            include_groups: 0, 1 or 2
                If 0: Return only tags
                If 1: return only groups
                If 2 or any other value: return both
                
        returns:
        list:
        tag: HedTag
            The located tag
        group: HedGroup
            The group the located tag is in
        """
        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self, )

        for sub_group in groups:
            for tag in sub_group.tags():
                if tag.short_base_tag.lower() in anchors:
                    found_tags.append((tag, sub_group))
                    
        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_exact_tags(self, tags_or_groups, recursive=False):
        """
            Find the given tags_or_groups.  Note if you pass in groups it will only find EXACT matches.

            If this is a HedGroup, order matters.  (b, a) != (a, b)

            If this is a HedGroupFrozen:
            if "(a, b)" in tags_or_groups, then it will match 1 and 2, but not 3.
            1. (a, b)
            2. (b, a)
            3. (a, b, c)

            Note: This can only find identified tags.  By default, definition, def, def-expand, onset, and offset
                are identified, even without a schema.

        Args:
            tags_or_groups: [HedTag or HedGroupBase]
                A container of tags to locate
            recursive: bool
                If true, also check subgroups.

        returns:
        group_list: [HedGroupBase]
            A list of all groups the given tags/groups were found in.
        """
        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self,)

        for sub_group in groups:
            for search_tag in tags_or_groups:
                if search_tag in sub_group._children:
                    found_tags.append(sub_group)

        return found_tags

    def find_def_tags(self, recursive=False, include_groups=3):
        """
            Find any def and def-expand tags in the group.

        Args:
            recursive: bool
                If true, also check subgroups.
            include_groups: int, 0, 1, 2, 3
                If 0: Return only def and def expand tags
                If 1: Return only def tags and def-expand groups
                If 2: Return only groups containing defs, or def-expand groups
                If 3 or any other value: Return all 3 as a tuple.
        Returns:
        list:
        def_tag: HedTag
            The located def tag
        def_expand_group: HedGroup or None
            If this is a def-expand rather than def tag, this will be the entire def-expand group.
        group: HedGroup
            The group the def tag or def expand group is in.
        """
        from hed.models.def_dict import DefTagNames
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self, )

        def_tags = []
        for group in groups:
            for child in group.get_direct_children():
                if isinstance(child, HedTag):
                    if child.short_base_tag.lower() == DefTagNames.DEF_KEY:
                        def_tags.append((child, child, group))
                else:
                    for tag in child.tags():
                        if tag.short_base_tag.lower() == DefTagNames.DEF_EXPAND_KEY:
                            def_tags.append((tag, child, group))

        if include_groups == 0 or include_groups == 1 or include_groups == 2:
            return [tag[include_groups] for tag in def_tags]
        return def_tags
