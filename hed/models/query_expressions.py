"""Classes representing parsed query expressions."""

from hed.models.query_util import SearchResult


class Expression:
    """Base class for parsed query expressions."""

    MATCH_TERM = 0  # Bare term: ancestor search via tag_terms
    MATCH_EXACT = 1  # Slash-path or quoted: exact tag match
    MATCH_WILDCARD = 2  # Asterisk prefix match on short_tag

    def __init__(self, token, left=None, right=None):
        self.left = left
        self.right = right
        self.token = token
        self._match_mode = Expression.MATCH_EXACT if "/" in token.text else Expression.MATCH_TERM
        self._must_not_be_in_line = False
        if token.text.startswith("@"):
            self._must_not_be_in_line = True
            token.text = token.text[1:]
        if token.text.startswith('"') and token.text.endswith('"') and len(token.text) > 2:
            self._match_mode = Expression.MATCH_EXACT
            token.text = token.text[1:-1]
        if "*" in token.text:
            self._match_mode = Expression.MATCH_WILDCARD
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
        if self._match_mode == Expression.MATCH_WILDCARD:
            groups_found = hed_group.find_wildcard_tags([self.token.text], recursive=True, include_groups=2)
        elif self._match_mode == Expression.MATCH_EXACT:
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
    """Query expression node for the logical AND (&&) operator.

    Both sub-expressions must match within the same HED group.
    """

    def handle_expr(self, hed_group, exact=False):
        """Return groups that satisfy both the left and right sub-expressions.

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): If True, require exact child matching.

        Returns:
            list: Merged :class:`~hed.models.query_util.SearchResult` objects matching both sub-expressions.

        """
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
            list: Groups in both lists narrowed down to results where none of the children overlap.
        """
        return_list = []
        seen = set()
        for group in groups1:
            for other_group in groups2:
                if group.group is other_group.group:
                    # At this point any shared children between the two groups invalidates it.
                    if any(tag is tag2 and tag is not None for tag in group.children for tag2 in other_group.children):
                        continue
                    # Merge the two groups' children into one new result, now that we've verified they're unique
                    merged_result = group.merge_and_result(other_group)
                    if merged_result not in seen:
                        seen.add(merged_result)
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
    """Query expression node for wildcard tokens (``?``, ``??``, ``???``).

    - ``?``  — matches any tag or group child.
    - ``??`` — matches any tag child.
    - ``???`` — matches any group child.
    """

    def handle_expr(self, hed_group, exact=False):
        """Return groups containing children that match the wildcard token.

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): Unused; present for API consistency with :meth:`Expression.handle_expr`.

        Returns:
            list: :class:`~hed.models.query_util.SearchResult` objects for each matching child.

        """
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

        # Wildcards are only found in containing groups — not propagated to every parent level.
        all_found_groups = [SearchResult(group, tag) for tag, group in groups_found]
        return all_found_groups


class ExpressionOr(Expression):
    """Query expression node for the logical OR (||) operator.

    At least one sub-expression must match within the HED group.
    """

    def handle_expr(self, hed_group, exact=False):
        """Return groups that satisfy the left or right sub-expression (or both).

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): If True, require exact child matching.

        Returns:
            list: Combined (deduplicated) :class:`~hed.models.query_util.SearchResult` objects.

        """
        groups1 = self.left.handle_expr(hed_group, exact=exact)
        # Don't early out as we need to gather all groups in case children appear more than once etc
        groups2 = self.right.handle_expr(hed_group, exact=exact)
        # Filter out results from groups1 that are already represented in groups2
        groups2_set = set(groups2)
        groups1 = [g for g in groups1 if g not in groups2_set]
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
    """Query expression node for logical negation (~).

    Returns all groups that do *not* match the sub-expression.
    """

    def handle_expr(self, hed_group, exact=False):
        """Return groups that do not satisfy the right sub-expression.

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): If True, require exact child matching.

        Returns:
            list: :class:`~hed.models.query_util.SearchResult` objects for non-matching groups.

        """
        found_groups = self.right.handle_expr(hed_group, exact=exact)
        found_group_ids = {id(found_group.group) for found_group in found_groups}
        negated_groups = [
            SearchResult(group, []) for group in hed_group.get_all_groups() if id(group) not in found_group_ids
        ]

        return negated_groups


class ExpressionDescendantGroup(Expression):
    """Query expression node that searches within descendant groups.

    Matches the right sub-expression anywhere in the group hierarchy and
    returns the nearest ancestor groups that contain the match.
    """

    def handle_expr(self, hed_group, exact=False):
        """Return parent groups whose descendants match the right sub-expression.

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): Unused; present for API consistency with :meth:`Expression.handle_expr`.

        Returns:
            list: :class:`~hed.models.query_util.SearchResult` objects for matching ancestor groups.

        """
        found_groups = self.right.handle_expr(hed_group)
        found_parent_groups = self._get_parent_groups(found_groups)
        return found_parent_groups


class ExpressionExactMatch(Expression):
    """Query expression node that requires an exact (curly-brace) group match.

    The matched group must contain exactly the children specified; no extra
    children are allowed unless they are declared optional via the left sub-expression.
    """

    def __init__(self, token, left=None, right=None):
        super().__init__(token, left, right)
        self.optional = "any"

    @staticmethod
    def _filter_exact_matches(search_results):
        filtered_list = []
        for group in search_results:
            if len(group.group.children) == len(group.children):
                filtered_list.append(group)

        return filtered_list

    def handle_expr(self, hed_group, exact=False):
        """Return groups that exactly match the required (and optional) sub-expressions.

        Parameters:
            hed_group (HedGroup): The HED group to search within.
            exact (bool): Propagated to sub-expression matching; always True internally.

        Returns:
            list: :class:`~hed.models.query_util.SearchResult` objects for exact-matching groups.

        """
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
