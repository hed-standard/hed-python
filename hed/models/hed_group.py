from hed.models.hed_tag import HedTag
import copy


class HedGroup:
    """ A single parenthesized hed string. """

    def __init__(self, hed_string="", startpos=None, endpos=None, contents=None):
        """ Return an empty HedGroup object.

        Parameters:
            hed_string (str or None): Source hed string for this group.
            startpos (int or None):   Starting index of group(including parentheses) in hed_string.
            endpos (int or None):     Position after the end (including parentheses) in hed_string.
            contents (list or None):  A list of HedTags and/or HedGroups that will be set as the contents of this group.

        Notes:
            - contents parameter is mainly used for processing definitions.

        """
        self._startpos = startpos
        self._endpos = endpos
        self._hed_string = hed_string
        self._parent = None

        if contents:
            self._children = contents
            for child in self._children:
                child._parent = self
        else:
            self._children = []
        self._original_children = self._children

    def append(self, tag_or_group):
        """ Add a tag or group to this group.

        Parameters:
            tag_or_group (HedTag or HedGroup): The new object to add to this group.

        Raises:
            ValueError: If a HedGroupFrozen.

        """
        tag_or_group._parent = self
        self._children.append(tag_or_group)

    def check_if_in_original(self, tag_or_group):
        """ Check if the tag or group in original string.

        Parameters:
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

        Parameters:
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

        Parameters:
            items_to_remove (list):  List of HedGroups and/or HedTags to remove.

        Notes:
            - Any groups that become empty will also be pruned.
            - Identity, not equivalence is used in determining whether to remove.

        """
        all_groups = self.get_all_groups()
        self._remove(items_to_remove, all_groups)

    def _remove(self, items_to_remove, all_groups):
        """ Needs to be documented.

        Parameters:
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

    def __copy__(self):
        raise ValueError("Cannot make shallow copies of HedGroups")

    def copy(self):
        """ Return a deep copy of this group.

        Returns:
            HedGroup: The copied group.

        Notes:
            - The parent tag is removed.

        """
        save_parent = self._parent
        self._parent = None
        return_copy = copy.deepcopy(self)
        self._parent = save_parent
        return return_copy

    def sort(self):
        """ Sort the tags and groups in this HedString in a consistent order.

        Returns:
            self
        """
        self.sorted(update_self=True)
        return self

    def sorted(self, update_self=False):
        """ Returns a sorted copy of this hed group as a list of it's children

        Parameters:
            update_self (bool): If True, update the contents of this group to be sorted as well.

        Returns:
            list: The list of all tags in this group, with subgroups being returned as further nested lists
        """
        output_list = []
        queue_list = list(self.children)
        for child in queue_list:
            if isinstance(child, HedTag):
                output_list.append((child, child))
            else:
                output_list.append((child, child.sorted(update_self)))

        output_list.sort(key=lambda x: str(x[0]))
        if update_self:
            self._children = [x[0] for x in output_list]
        return [x[1] for x in output_list]

    @property
    def children(self):
        """ A list of the direct children. """
        return self._children

    @property
    def is_group(self):
        """ True if this is a parenthesized group. """
        return True

    def get_all_tags(self):
        """ Return HedTags, including descendants.

        Returns:
            list:  A list of all the tags in this group including descendants.

        """
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = list(current_group_or_tag.children) + node_list
            else:
                final_list.append(current_group_or_tag)
        return final_list

    def get_all_groups(self, also_return_depth=False):
        """ Return HedGroups, including descendants and self.

        Parameters:
            also_return_depth (bool): If True, yield tuples (group, depth) rather than just groups.

        Returns:
            list: The list of all HedGroups in this group, including descendants and self.

        """
        node_list = [self]
        final_list = []

        # Using an iterator is worse performance wise here.
        while node_list:
            current_group_or_tag = node_list.pop(0)
            if isinstance(current_group_or_tag, HedGroup):
                node_list = list(current_group_or_tag.children) + node_list
                final_list.append(current_group_or_tag)

        if also_return_depth:
            top_groups = self.groups()

            final_list = [(group, self._check_in_group(group, top_groups)) for group in final_list]
        return final_list

    @staticmethod
    def _check_in_group(group, group_list):
        """ Return true if the group is list.

        Parameters:
            group (HedGroup): The group to check for.
            group_list (list):    A list of groups to search.

        Returns:
            bool: True if group is in the group list.

        """
        for val in group_list:
            if val is group:
                return True
        return False

    def tags(self):
        """ Return the direct child tags of this group.

        Returns:
            list: All tags directly in this group, filtering out HedGroup children.

        """
        return [tag for tag in self.children if isinstance(tag, HedTag)]

    def groups(self):
        """ Return the direct child groups of this group.

        Returns:
            list: All groups directly in this group, filtering out HedTag children.

        """
        return [group for group in self.children if isinstance(group, HedGroup)]

    def get_original_hed_string(self):
        """ Get the original hed string.

        Returns:
            str: The original string with no modification.

        """
        return self._hed_string[self._startpos:self._endpos]

    @property
    def span(self):
        """ Return the source span.

        Return:
            int: start index of the group (including parentheses) from the source string.
            int: end index of the group (including parentheses) from the source string.

        """
        return self._startpos, self._endpos

    def __str__(self):
        """ Convert this HedGroup to a string.

        Returns:
            str: The group as a string, including any modified HedTags.

        """
        if self.is_group:
            return "(" + ",".join([str(child) for child in self.children]) + ")"
        return ",".join([str(child) for child in self.children])

    def get_as_short(self):
        """ Return this HedGroup as a short tag string.

        Returns:
            str: The group as a string with all tags as short tags.

        """
        return self.get_as_form("short_tag")

    def get_as_long(self):
        """ Return this HedGroup as a long tag string.

        Returns:
            str: The group as a string with all tags as long tags.

        """
        return self.get_as_form("long_tag")

    def get_as_form(self, tag_attribute, tag_transformer=None):
        """ Get the string corresponding to the specified form.

        Parameters:
            tag_attribute (str): The hed_tag property to use to construct the string (usually short_tag or long_tag).
            tag_transformer (func or None): A function that is applied to each tag string before returning.

        Returns:
            str: The constructed string after transformation

        Notes:
            - The signature of a tag_transformer is str def(HedTag, str).

        """
        if tag_transformer:
            result = ",".join([tag_transformer(child, child.__getattribute__(tag_attribute))
                               if isinstance(child, HedTag) else child.get_as_form(tag_attribute, tag_transformer)
                               for child in self.children])
        else:
            result = ",".join([child.__getattribute__(tag_attribute) if isinstance(child, HedTag) else
                               child.get_as_form(tag_attribute) for child in self.children])
        if self.is_group:
            return f"({result})"
        return result

    def lower(self):
        """ Convenience function, equivalent to str(self).lower() """
        return str(self).lower()

    def find_placeholder_tag(self):
        """ Return a placeholder tag, if present in this group.

        Returns:
            HedTag or None: The placeholder tag if found.

        Notes:
            - Assumes a valid HedString with no erroneous "#" characters.

        """
        for tag in self.get_all_tags():
            if "#" in tag.org_tag:
                return tag

        return None

    def __bool__(self):
        return bool(self._children)

    def __eq__(self, other):
        """ Test whether other is equal to this object. """
        if self is other:
            return True

        if not isinstance(other, HedGroup) or self.children != other.children or self.is_group != other.is_group:
            return False
        return True

    def find_tags(self, search_tags, recursive=False, include_groups=2):
        """ Find the tags and their containing groups.

        Parameters:
            search_tags (container):    A container of short_base_tags to locate
            recursive (bool):           If true, also check subgroups.
            include_groups (0, 1 or 2): Specify return values.

        Returns:
            list: The contents of the list depends on the value of include_groups.

        Notes:
            - If include_groups is 0, return a list of the HedTags.
            - If include_groups is 1, return a list of the HedGroups containing the HedTags.
            - If include_groups is 2, return a list of tuples (HedTag, HedGroup) for the found tags.
            - This can only find identified tags.
            - By default, definition, def, def-expand, onset, and offset are identified, even without a schema.

        """
        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self, )

        for sub_group in groups:
            for tag in sub_group.tags():
                if tag.short_base_tag.lower() in search_tags:
                    found_tags.append((tag, sub_group))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_wildcard_tags(self, search_tags, recursive=False, include_groups=2):
        """ Find the tags and their containing groups.

        Parameters:
            search_tags (container):    A container of the starts of short tags to search.
            recursive (bool):           If true, also check subgroups.
            include_groups (0, 1 or 2): Specify return values.

        Returns:
            list: The contents of the list depends on the value of include_groups.

        Notes:
            - If include_groups is 0, return a list of the HedTags.
            - If include_groups is 1, return a list of the HedGroups containing the HedTags.
            - If include_groups is 2, return a list of tuples (HedTag, HedGroup) for the found tags.
            - This can only find identified tags.
            - By default, definition, def, def-expand, onset, and offset are identified, even without a schema.

        """
        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self, )

        for sub_group in groups:
            for tag in sub_group.tags():
                for search_tag in search_tags:
                    if tag.short_tag.lower().startswith(search_tag):
                        found_tags.append((tag, sub_group))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_exact_tags(self, tags_or_groups, recursive=False, include_groups=1):
        """  Find the given tags or groups.

        Parameters:
            tags_or_groups (HedTag, HedGroup): A container of tags to locate.
            recursive (bool): If true, also check subgroups.
            include_groups(bool): 0, 1 or 2
                If 0: Return only tags
                If 1: Return only groups
                If 2 or any other value: Return both
        Returns:
            list: A list of HedGroups the given tags/groups were found in.

        Notes:
            - If you pass in groups it will only find EXACT matches.
            - This can only find identified tags.
            - By default, definition, def, def-expand, onset, and offset are identified, even without a schema.
            - If this is a HedGroup, order matters.  (b, a) != (a, b)
            - If this is a HedGroupFrozen:
                    if "(a, b)" in tags_or_groups, then it will match 1 and 2, but not 3.
                        1. (a, b)
                        2. (b, a)
                        3. (a, b, c)

        """
        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self,)

        for sub_group in groups:
            for search_tag in tags_or_groups:
                for tag in sub_group.children:
                    if tag == search_tag:
                        found_tags.append((tag, sub_group))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]

        return found_tags

    def find_def_tags(self, recursive=False, include_groups=3):
        """ Find def and def-expand tags
        Parameters:
            recursive (bool): If true, also check subgroups.
            include_groups (int, 0, 1, 2, 3): options for how to expand or include groups
        Returns:
            list: A list of tuples. The contents depends on the values of the include group.
        Notes:
            - The include_groups option controls the tag expansion as follows:
                - If 0: Return only def and def expand tags/.
                - If 1: Return only def tags and def-expand groups.
                - If 2: Return only groups containing defs, or def-expand groups.
                - If 3 or any other value: Return all 3 as a tuple.
        """
        from hed.models.definition_dict import DefTagNames
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self, )

        def_tags = []
        for group in groups:
            for child in group.children:
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

    def find_tags_with_term(self, term, recursive=False, include_groups=2):
        """  Find any tags that contain the given term.

            Note: This can only find identified tags.

        Parameters:
            term (str): A single term to search for.
            recursive (bool): If true, recursively check subgroups.
            include_groups: 0, 1 or 2
                If 0: Return only tags
                If 1: Return only groups
                If 2 or any other value: Return both

        Returns:
            list:

        """

        found_tags = []
        if recursive:
            groups = self.get_all_groups()
        else:
            groups = (self,)

        search_for = term.lower()
        for sub_group in groups:
            for tag in sub_group.tags():
                if search_for in tag.tag_terms:
                    found_tags.append((tag, sub_group))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags
