""" A single parenthesized HED string. """
from __future__ import annotations
from hed.models.hed_tag import HedTag
from hed.models.model_constants import DefTagNames
import copy
from typing import Iterable, Union


class HedGroup:
    """ A single parenthesized HED string. """

    def __init__(self, hed_string="", startpos=None, endpos=None, contents=None):
        """ Return an empty HedGroup object.

        Parameters:
            hed_string (str or None): Source HED string for this group.
            startpos (int or None):   Starting index of group(including parentheses) in hed_string.
            endpos (int or None):     Position after the end (including parentheses) in hed_string.
            contents (list or None):  A list of HedTags and/or HedGroups that will be set as the contents of this group.
                                      Mostly used during definition expansion.
        """
        self._startpos = startpos
        self._endpos = endpos
        self._hed_string = hed_string
        self._parent = None

        if contents:
            self.children = contents
            for child in self.children:
                child._parent = self
        else:
            self.children = []
        self._original_children = self.children

    def append(self, tag_or_group):
        """ Add a tag or group to this group.

        Parameters:
            tag_or_group (HedTag or HedGroup): The new object to add to this group.
        """
        tag_or_group._parent = self
        self.children.append(tag_or_group)

    def check_if_in_original(self, tag_or_group) -> bool:
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

    @staticmethod
    def replace(item_to_replace, new_contents):
        """ Replace an existing tag or group.

            Note: This is a static method that relies on the parent attribute of item_to_replace.

        Parameters:
            item_to_replace (HedTag or HedGroup): The item to replace must exist or this will raise an error.
            new_contents (HedTag or HedGroup): Replacement contents.

        Raises:
            KeyError: Item_to_replace does not exist.
            AttributeError: Item_to_replace has no parent set.
        """
        parent = item_to_replace._parent
        parent._replace(item_to_replace=item_to_replace, new_contents=new_contents)

    def _replace(self, item_to_replace, new_contents):
        """ Replace an existing tag or group.

        Parameters:
            item_to_replace (HedTag or HedGroup): The item to replace must exist and be a direct child,
                                                  or this will raise an error.
            new_contents (HedTag or HedGroup): Replacement contents.

        Raises:
            KeyError: Item_to_replace does not exist.
        """
        if self._original_children is self.children:
            self._original_children = self.children.copy()

        for i, child in enumerate(self.children):
            if item_to_replace is child:
                self.children[i] = new_contents
                new_contents._parent = self
                return

        raise KeyError(f"The tag {item_to_replace} not found in the group.")

    def remove(self, items_to_remove: Iterable[Union[HedTag, 'HedGroup']]):
        """ Remove any tags/groups in items_to_remove.

        Parameters:
            items_to_remove (list):  List of HedGroups and/or HedTags to remove by identity.

        Notes:
            - Any groups that become empty will also be pruned.
            - If you pass a child and parent group, the child will also be removed from the parent.
        """
        empty_groups = []
        # Filter out duplicates
        items_to_remove = {id(item): item for item in items_to_remove}.values()

        for item in items_to_remove:
            group = item._parent
            if group._original_children is group.children:
                group._original_children = group.children.copy()

            group.children.remove(item)
            if not group.children and group is not self:
                empty_groups.append(group)

        if empty_groups:
            self.remove(empty_groups)

        # Do this last to avoid confusing typing
        for item in items_to_remove:
            item._parent = None

    def __copy__(self):
        raise ValueError("Cannot make shallow copies of HedGroups")

    def copy(self) -> "HedGroup":
        """ Return a deep copy of this group.

        Returns:
            HedGroup: The copied group.

        """
        save_parent = self._parent
        self._parent = None
        return_copy = copy.deepcopy(self)
        self._parent = save_parent
        return return_copy

    def sort(self):
        """ Sort the tags and groups in this HedString in a consistent order."""
        self._sorted(update_self=True)

    def sorted(self) -> "HedGroup":
        """ Return a sorted copy of this HED group

        Returns:
            HedGroup: The sorted copy.
        """
        string_copy = self.copy()
        string_copy._sorted(update_self=True)
        return string_copy

    def _sorted(self, update_self=False) -> list:
        """ Return a sorted copy of this HED group as a list of its children.

        Parameters:
            update_self (bool): If True, update the contents of this group to be sorted as well.

        Returns:
            list: The list of all tags in this group, with subgroups being returned as further nested lists.
        """
        tag_list = []
        group_list = []
        queue_list = list(self.children)
        for child in queue_list:
            if isinstance(child, HedTag):
                tag_list.append((child, child))
            else:
                group_list.append((child, child._sorted(update_self)))

        tag_list.sort(key=lambda x: str(x[0]))
        group_list.sort(key=lambda x: str(x[0]))
        output_list = tag_list + group_list
        if update_self:
            self.children = [x[0] for x in output_list]
        return [x[1] for x in output_list]

    @property
    def is_group(self):
        """ True if this is a parenthesized group. """
        return True

    def get_all_tags(self) -> list:
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

    def get_all_groups(self, also_return_depth=False) -> list:
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
    def _check_in_group(group, group_list) -> bool:
        """ Return True if the group is list.

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

    def tags(self) -> list:
        """ Return the direct child tags of this group.

        Returns:
            list: All tags directly in this group, filtering out HedGroup children.

        """
        return [tag for tag in self.children if isinstance(tag, HedTag)]

    def groups(self) -> list:
        """ Return the direct child groups of this group.

        Returns:
            list: All groups directly in this group, filtering out HedTag children.

        """
        return [group for group in self.children if isinstance(group, HedGroup)]

    def get_first_group(self) -> HedGroup:
        """ Return the first group in this HED string or group.

            Useful for things like Def-expand where they only have a single group.

        Returns:
            HedGroup: The first group.

        Raises:
            ValueError: If there are no groups.

        """
        return self.groups()[0]

    def get_original_hed_string(self) -> str:
        """ Get the original HED string.

        Returns:
            str: The original string with no modification.

        """
        return self._hed_string[self._startpos:self._endpos]

    @property
    def span(self) -> tuple[int, int]:
        """ Return the source span.

        Returns:
            tuple[int, int]: start and end index of the group (including parentheses) from the source string.

        """
        return self._startpos, self._endpos

    def __str__(self) -> str:
        """ Convert this HedGroup to a string.

        Returns:
            str: The group as a string, including any modified HedTags.

        """
        if self.is_group:
            return "(" + ",".join([str(child) for child in self.children]) + ")"
        return ",".join([str(child) for child in self.children])

    def get_as_short(self) -> str:
        """ Return this HedGroup as a short tag string.

        Returns:
            str: The group as a string with all tags as short tags.

        """
        return self.get_as_form("short_tag")

    def get_as_long(self) -> str:
        """ Return this HedGroup as a long tag string.

        Returns:
            str: The group as a string with all tags as long tags.

        """
        return self.get_as_form("long_tag")

    def get_as_form(self, tag_attribute) -> str:
        """ Get the string corresponding to the specified form.

        Parameters:
            tag_attribute (str): The hed_tag property to use to construct the string (usually short_tag or long_tag).

        Returns:
            str: The constructed string after transformation.
        """
        result = ",".join([child.__getattribute__(tag_attribute) if isinstance(child, HedTag) else
                           child.get_as_form(tag_attribute) for child in self.children])
        if self.is_group:
            return f"({result})"
        return result

    def lower(self):
        """ Convenience function, equivalent to str(self).lower(). """
        return str(self).lower()

    def casefold(self):
        """ Convenience function, equivalent to str(self).casefold(). """
        return str(self).casefold()

    def get_as_indented(self, tag_attribute="short_tag") -> str:
        """Return the string as a multiline indented format.

        Parameters:
            tag_attribute (str): The hed_tag property to use to construct the string (usually short_tag or long_tag).

        Returns:
            str: The indented string.
        """
        hed_string = self.sorted().get_as_form(tag_attribute)

        level_open = []
        level = 0
        indented = ""
        prev = ''
        for c in hed_string:
            if c == "(":
                level_open.append(level)
                indented += "\n" + "\t" * level + c
                level += 1
            elif c == ")":
                level = level_open.pop()
                if prev == ")":
                    indented += "\n" + "\t" * level + c
                else:
                    indented += c

            else:
                indented += c
            prev = c

        return indented

    def find_placeholder_tag(self) -> Union[HedTag, None]:
        """ Return a placeholder tag, if present in this group.

        Returns:
            Union[HedTag, None]: The placeholder tag if found.

        Notes:
            - Assumes a valid HedString with no erroneous "#" characters.
        """
        for tag in self.get_all_tags():
            if tag.is_placeholder():
                return tag

        return None

    def __bool__(self):
        return bool(self.children)

    def __eq__(self, other):
        """ Test whether other is equal to this object.

            Note: This does not account for sorting.  Objects must be in the same order to match.
        """
        if self is other:
            return True

        # Allow us to compare to a list of groups.
        # Note this comparison will NOT check if the list has the outer parenthesis
        if isinstance(other, list):
            return self.children == other
        if isinstance(other, str):
            return str(self) == other
        if not isinstance(other, HedGroup) or self.children != other.children or self.is_group != other.is_group:
            return False
        return True

    def find_tags(self, search_tags, recursive=False, include_groups=2) -> list:
        """ Find the base tags and their containing groups.
        This searches by short_base_tag, ignoring any ancestors or extensions/values.

        Parameters:
            search_tags (container):  A container of short_base_tags to locate.
            recursive (bool): If true, also check subgroups.
            include_groups (0, 1 or 2): Specify return values.
                If 0: return a list of the HedTags.
                If 1: return a list of the HedGroups containing the HedTags.
                If 2: return a list of tuples (HedTag, HedGroup) for the found tags.

        Returns:
            list: The contents of the list depends on the value of include_groups.
        """
        found_tags = []
        if recursive:
            tags = self.get_all_tags()
        else:
            tags = self.tags()
        search_tags = {tag.casefold() for tag in search_tags}
        for tag in tags:
            if tag.short_base_tag.casefold() in search_tags:
                found_tags.append((tag, tag._parent))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_wildcard_tags(self, search_tags, recursive=False, include_groups=2) -> list:
        """ Find the tags and their containing groups.

            This searches tag.short_tag.casefold(), with an implicit wildcard on the end.

            e.g. "Eve" will find Event, but not Sensory-event.

        Parameters:
            search_tags (container): A container of the starts of short tags to search.
            recursive (bool): If True, also check subgroups.
            include_groups (0, 1 or 2): Specify return values.
                If 0: return a list of the HedTags.
                If 1: return a list of the HedGroups containing the HedTags.
                If 2: return a list of tuples (HedTag, HedGroup) for the found tags.

        Returns:
            list: The contents of the list depends on the value of include_groups.
        """
        found_tags = []
        if recursive:
            tags = self.get_all_tags()
        else:
            tags = self.tags()

        search_tags = {search_tag.casefold() for search_tag in search_tags}

        for tag in tags:
            for search_tag in search_tags:
                if tag.short_tag.casefold().startswith(search_tag):
                    found_tags.append((tag, tag._parent))
                    # We can't find the same tag twice
                    break

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_exact_tags(self, exact_tags, recursive=False, include_groups=1) -> list:
        """  Find the given tags.  This will only find complete matches, any extension or value must also match.

        Parameters:
            exact_tags (list of HedTag): A container of tags to locate.
            recursive (bool): If true, also check subgroups.
            include_groups (bool): 0, 1 or 2.
                If 0: Return only tags
                If 1: Return only groups
                If 2 or any other value: Return both
        Returns:
            list: A list of tuples. The contents depend on the values of the include_group.
        """
        found_tags = []
        if recursive:
            tags = self.get_all_tags()
        else:
            tags = self.tags()

        for tag in tags:
            if tag in exact_tags:
                found_tags.append((tag, tag._parent))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags

    def find_def_tags(self, recursive=False, include_groups=3) -> list:
        """ Find def and def-expand tags.

        Parameters:
            recursive (bool): If true, also check subgroups.
            include_groups (int, 0, 1, 2, 3): Options for return values.
                If 0: Return only def and def expand tags/.
                If 1: Return only def tags and def-expand groups.
                If 2: Return only groups containing defs, or def-expand groups.
                If 3 or any other value: Return all 3 as a tuple.
        Returns:
            list: A list of tuples. The contents depend on the values of the include_group.
        """
        if recursive:
            groups = self.get_all_groups()
            def_tags = []
            for group in groups:
                def_tags += self._get_def_tags_from_group(group)
        else:
            def_tags = self._get_def_tags_from_group(self)

        if include_groups == 0 or include_groups == 1 or include_groups == 2:
            return [tag[include_groups] for tag in def_tags]
        return def_tags

    @staticmethod
    def _get_def_tags_from_group(group):
        def_tags = []
        for child in group.children:
            if isinstance(child, HedTag):
                if child.short_base_tag == DefTagNames.DEF_KEY:
                    def_tags.append((child, child, group))
            else:
                for tag in child.tags():
                    if tag.short_base_tag == DefTagNames.DEF_EXPAND_KEY:
                        def_tags.append((tag, child, group))
        return def_tags

    def find_tags_with_term(self, term, recursive=False, include_groups=2) -> list:
        """  Find any tags that contain the given term.

            Note: This can only find identified tags.

        Parameters:
            term (str): A single term to search for.
            recursive (bool): If true, recursively check subgroups.
            include_groups (0, 1 or 2): Controls return values
                If 0: Return only tags.
                If 1: Return only groups.
                If 2 or any other value: Return both.

        Returns:
            list: A list of tuples. The contents depend on the values of the include_group.
        """
        found_tags = []
        if recursive:
            tags = self.get_all_tags()
        else:
            tags = self.tags()

        search_for = term.casefold()
        for tag in tags:
            if search_for in tag.tag_terms:
                found_tags.append((tag, tag._parent))

        if include_groups == 0 or include_groups == 1:
            return [tag[include_groups] for tag in found_tags]
        return found_tags
