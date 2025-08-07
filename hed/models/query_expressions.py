""" Classes representing parsed query expressions. """
from hed.models.query_util import SearchResult


class Expression:
    """ Base class for parsed query expressions. """
    def __init__(self, token, left=None, right=None):
        self.left = left
        self.right = right
        self.token = token
        self._match_mode = "/" in token.text
        self._must_not_be_in_line = False
        if token.text.startswith("@"):
            self._must_not_be_in_line = True
            token.text = token.text[1:]
        if token.text.startswith('"') and token.text.endswith('"') and len(token.text) > 2:
            self._match_mode = 1
            token.text = token.text[1:-1]
        if "*" in token.text:
            self._match_mode = 2
            token.text = token.text.replace("*", "")

    @staticmethod
    def _get_parent_groups(search_results):
        found_parent_groups = []
        if search_results:
            for group in search_results:
                if not group.group.is_group:
                    continue
                if group.group._parent:
                    found_parent_groups.append(SearchResult(group.group._parent, group.group))

        return found_parent_groups

    def __str__(self):
        output_str = ""
        if self.left:
            output_str += str(self.left)
        output_str += " " + str(self.token)
        if self.right:
            output_str += str(self.right)
        return output_str

    def handle_expr(self, hed_group, exact=False):
        """Handles parsing the given expression, recursively down the list as needed.

           BaseClass implementation is search terms.

           Parameters:
               hed_group(HedGroup): The object to search
               exact(bool): If True, we are only looking for groups containing this term directly, not descendants.
           """
        if self._match_mode == 2:
            groups_found = hed_group.find_wildcard_tags([self.token.text], recursive=True, include_groups=2)
        elif self._match_mode:
            groups_found = hed_group.find_exact_tags([self.token.text], recursive=True, include_groups=2)
        else:
            groups_found = hed_group.find_tags_with_term(self.token.text, recursive=True, include_groups=2)

        if self._must_not_be_in_line:
            # If we found this, and it cannot be in the line.
            if groups_found:
                groups_found = []
            else:
                groups_found = [([], group) for group in hed_group.get_all_groups()]

        # If we're checking for all groups, also need to add parents.
        if exact:
            all_found_groups = [SearchResult(group, tag) for tag, group in groups_found]
        else:
            all_found_groups = []
            for tag, group in groups_found:
                while group:
                    all_found_groups.append(SearchResult(group, tag))
                    # This behavior makes it eat higher level groups at higher levels
                    tag = group
                    group = group._parent
        return all_found_groups


class ExpressionAnd(Expression):
    def handle_expr(self, hed_group, exact=False):
        groups1 = self.left.handle_expr(hed_group, exact=exact)
        if not groups1:
            return groups1
        groups2 = self.right.handle_expr(hed_group, exact=exact)

        return self.merge_and_groups(groups1, groups2)

    @staticmethod
    def merge_and_groups(groups1, groups2):
        """Finds any shared results

        Parameters:
            groups1(list): a list of search results
            groups2(list): a list of search results

        Returns:
            list: Groups in both lists narrowed down results to where none of the tags overlap.
        """
        return_list = []
        for group in groups1:
            for other_group in groups2:
                if group.group is other_group.group:
                    # At this point any shared tags between the two groups invalidates it.
                    if any(tag is tag2 and tag is not None for tag in group.tags for tag2 in other_group.tags):
                        continue
                    # Merge the two groups tags into one new result, now that we've verified they're unique
                    merged_result = group.merge_and_result(other_group)

                    dont_add = False
                    # This is trash and slow
                    for finalized_value in return_list:
                        if merged_result.has_same_tags(finalized_value):
                            dont_add = True
                            break
                    if dont_add:
                        continue
                    return_list.append(merged_result)

        return return_list

    def __str__(self):
        output_str = "("
        if self.left:
            output_str += str(self.left)
        output_str += " " + str(self.token)
        if self.right:
            output_str += str(self.right)
        output_str += ")"
        return output_str


class ExpressionWildcardNew(Expression):
    def handle_expr(self, hed_group, exact=False):
        groups_found = []
        if self.token.text == "?":
            # Any tag or group
            groups_searching = hed_group.get_all_groups()
            for group in groups_searching:
                for child in group.children:
                    groups_found.append((child, group))
        elif self.token.text == "??":
            groups_searching = hed_group.get_all_groups()
            for group in groups_searching:
                for child in group.tags():
                    groups_found.append((child, group))
        elif self.token.text == "???":
            # Any group
            groups_searching = hed_group.get_all_groups()
            for group in groups_searching:
                for child in group.groups():
                    groups_found.append((child, group))

        # Wildcards are only found in containing groups.  I believe this is correct.
        # todo: Is this code still needed for this kind of wildcard?  We already are registering every group, just not
        # every group at every level.
        all_found_groups = [SearchResult(group, tag) for tag, group in groups_found]
        return all_found_groups


class ExpressionOr(Expression):
    def handle_expr(self, hed_group, exact=False):
        groups1 = self.left.handle_expr(hed_group, exact=exact)
        # Don't early out as we need to gather all groups in case tags appear more than once etc
        groups2 = self.right.handle_expr(hed_group, exact=exact)
        # todo: optimize this eventually
        # Filter out duplicates
        duplicates = []
        for group in groups1:
            for other_group in groups2:
                if group.has_same_tags(other_group):
                    duplicates.append(group)

        groups1 = [group for group in groups1 if not any(other_group is group for other_group in duplicates)]

        return groups1 + groups2

    def __str__(self):
        output_str = "("
        if self.left:
            output_str += str(self.left)
        output_str += " " + str(self.token)
        if self.right:
            output_str += str(self.right)
        output_str += ")"
        return output_str


class ExpressionNegation(Expression):
    def handle_expr(self, hed_group, exact=False):
        found_groups = self.right.handle_expr(hed_group, exact=exact)

        # Todo: this may need more thought with respects to wildcards and negation
        # negated_groups = [group for group in hed_group.get_all_groups() if group not in groups]
        # This simpler version works on python >= 3.9
        # negated_groups = [SearchResult(group, []) for group in hed_group.get_all_groups() if group not in groups]
        # Python 3.7/8 compatible version.
        negated_groups = [SearchResult(group, []) for group in hed_group.get_all_groups()
                          if not any(group is found_group.group for found_group in found_groups)]

        return negated_groups


class ExpressionDescendantGroup(Expression):
    def handle_expr(self, hed_group, exact=False):
        found_groups = self.right.handle_expr(hed_group)
        found_parent_groups = self._get_parent_groups(found_groups)
        return found_parent_groups


class ExpressionExactMatch(Expression):
    def __init__(self, token, left=None, right=None):
        super().__init__(token, left, right)
        self.optional = "any"

    @staticmethod
    def _filter_exact_matches(search_results):
        filtered_list = []
        for group in search_results:
            if len(group.group.children) == len(group.tags):
                filtered_list.append(group)

        return filtered_list

    def handle_expr(self, hed_group, exact=False):
        found_groups = self.right.handle_expr(hed_group, exact=True)
        if self.optional == "any":
            return self._get_parent_groups(found_groups)

        filtered_list = self._filter_exact_matches(found_groups)
        if filtered_list:
            return self._get_parent_groups(filtered_list)

        # Basically if we don't have an exact match above, do the more complex matching including optional
        if self.left:
            optional_groups = self.left.handle_expr(hed_group, exact=True)
            found_groups = ExpressionAnd.merge_and_groups(found_groups, optional_groups)

        filtered_list = self._filter_exact_matches(found_groups)
        if filtered_list:
            return self._get_parent_groups(filtered_list)

        return []
