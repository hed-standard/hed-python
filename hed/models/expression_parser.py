import re


# todo: Add support for early outs with and(only try to match groups we already matched instead of all groups)
class search_result:
    def __init__(self, group, tag):
        self.group = group
        # todo: rename tag: children
        if not isinstance(tag, list):
            new_tags = [tag]
        else:
            new_tags = tag.copy()
        self.tags = new_tags

    def __eq__(self, other):
        if isinstance(other, search_result):
            return self.group == other.group
        return other == self.group

    def merge_result(self, other):
        # Returns a new
        new_tags = self.tags.copy()
        for tag in other.tags:
            if any(tag is this_tag for this_tag in self.tags):
                continue
            new_tags.append(tag)
        new_tags.sort(key=lambda x: str(x))

        if self.group != other.group:
            raise ValueError("Internal error")
        return search_result(self.group, new_tags)

    def has_same_tags(self, other):
        if self.group != other.group:
            return False

        if len(self.tags) != len(other.tags):
            return False

        return all(tag is tag2 for tag, tag2 in zip(self.tags, other.tags))

    def __str__(self):
        return str(self.group) + " Tags: " + "---".join([str(tag) for tag in self.tags])

    def get_tags_only(self):
        from hed import HedTag
        return [tag for tag in self.tags if isinstance(tag, HedTag)]

    def get_groups_only(self):
        from hed import HedTag
        return [tag for tag in self.tags if not isinstance(tag, HedTag)]


class Token:
    And = 0
    Tag = 1
    ContainingGroup = 2
    ContainingGroupEnd = 3
    DescendantGroup = 4
    DescendantGroupEnd = 5
    Or = 6
    LogicalGroup = 7
    LogicalGroupEnd = 8
    LogicalNegation = 9
    Wildcard = 10
    ExactMatch = 11
    ExactMatchEnd = 12
    NotInLine = 13  # Not currently a token. In development and may become one.

    def __init__(self, text):
        tokens = {
            ",": Token.And,
            "and": Token.And,
            "or": Token.Or,
            "[[": Token.ContainingGroup,
            "]]": Token.ContainingGroupEnd,
            "[": Token.DescendantGroup,
            "]": Token.DescendantGroupEnd,
            "(": Token.LogicalGroup,
            ")": Token.LogicalGroupEnd,
            "~": Token.LogicalNegation,
            "?": Token.Wildcard, # Any tag or group
            "??": Token.Wildcard, # Any tag
            "???": Token.Wildcard, # Any Group
            "{": Token.ExactMatch, # Nothing else
            "}": Token.ExactMatchEnd,  # Nothing else
            "@": Token.NotInLine
        }
        self.kind = tokens.get(text, Token.Tag)
        self.text = text

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if self.kind == other:
            return True
        return False


class Expression:
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

    def __str__(self):
        output_str = ""
        if self.left:
            output_str += str(self.left)
        output_str += " " + str(self.token)
        if self.right:
            output_str += str(self.right)
        return output_str

    def handle_expr(self, hed_group, exact=False):
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
                groups_found = [(None, group) for group in hed_group.get_all_groups()]

        # If we're checking for all groups, also need to add parents.
        if exact:
            all_found_groups = [search_result(group, tag) for tag, group in groups_found]
        else:
            all_found_groups = []
            for tag, group in groups_found:
                while group:
                    all_found_groups.append(search_result(group, tag))
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
        # this is slow...
        return_list = []
        for group in groups1:
            for other_group in groups2:
                if group.group is other_group.group:
                    # At this point any shared tags between the two groups invalidates it.
                    if any(tag is tag2 for tag in group.tags for tag2 in other_group.tags):
                        continue
                    merged_result = group.merge_result(other_group)

                    dont_add = False
                    # This is trash and slow
                    for finalized_value in return_list:
                        if merged_result.has_same_tags(finalized_value):
                            dont_add = True
                            break
                    if dont_add:
                        continue
                    return_list.append(merged_result)

        # finally simplify the list and remove duplicates.

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
        all_found_groups = [search_result(group, tag) for tag, group in groups_found]
        return all_found_groups

class ExpressionOr(Expression):
    def handle_expr(self, hed_group, exact=False):
        groups1 = self.left.handle_expr(hed_group, exact=exact)
        # Don't early out as we need to gather all groups incase tags appear more than once etc
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
        #negated_groups = [group for group in hed_group.get_all_groups() if group not in groups]
        # This simpler version works on python >= 3.9
        # negated_groups = [search_result(group, []) for group in hed_group.get_all_groups() if group not in groups]
        # Python 3.7/8 compatible version.
        negated_groups = [search_result(group, []) for group in hed_group.get_all_groups()
                          if not any(group is found_group.group for found_group in found_groups)]

        return negated_groups

class ExpressionContainingGroup(Expression):
    def handle_expr(self, hed_group, exact=False):
        result = self.right.handle_expr(hed_group, exact=True)
        found_groups = result
        if result:
            found_parent_groups = []
            for group in found_groups:
                if not group.group.is_group:
                    continue
                if group.group._parent:
                    found_parent_groups.append(search_result(group.group._parent, group.group))

            if found_parent_groups:
                return found_parent_groups

        return []


class ExpressionDescendantGroup(Expression):
    def handle_expr(self, hed_group, exact=False):
        found_groups = self.right.handle_expr(hed_group)
        found_parent_groups = []
        if found_groups:
            for group in found_groups:
                if not group.group.is_group:
                    continue
                if group.group._parent:
                    found_parent_groups.append(search_result(group.group._parent, group.group))

        if found_parent_groups:
            return found_parent_groups
        return []


class ExpressionExactMatch(Expression):
    def handle_expr(self, hed_group, exact=False):
        found_groups = self.right.handle_expr(hed_group, exact=True)
        if found_groups:
            return_list = []
            for group in found_groups:
                if len(group.group.children) == len(group.tags):
                    return_list.append(group)

            if return_list:
                return return_list

        return []


class QueryParser:
    """Parse a search expression into a form than can be used to search a hed string."""
    def __init__(self, expression_string):
        self.tokens = []
        self.at_token = -1
        self.tree = self._parse(expression_string.lower())
        self._org_string = expression_string

    def __str__(self):
        return str(self.tree)

    def _get_next_token(self):
        self.at_token += 1
        if self.at_token >= len(self.tokens):
            raise ValueError("Parse error in get next token")
        return self.tokens[self.at_token]

    def _next_token_is(self, kinds):
        if self.at_token + 1 >= len(self.tokens):
            return None
        if self.tokens[self.at_token + 1].kind in kinds:
            return self._get_next_token()
        return None

    def current_token(self):
        if self.at_token + 1 >= len(self.tokens):
            return None
        return self.tokens[self.at_token].text

    def _handle_and_op(self):
        expr = self._handle_negation()
        next_token = self._next_token_is([Token.And, Token.Or])
        while next_token:
            right = self._handle_negation()
            if next_token.kind == Token.And:
                expr = ExpressionAnd(next_token, expr, right)
            elif next_token.kind == Token.Or:
                expr = ExpressionOr(next_token, expr, right)
            next_token = self._next_token_is([Token.And, Token.Or])

        return expr

    def _handle_negation(self):
        next_token = self._next_token_is([Token.LogicalNegation])
        if next_token == Token.LogicalNegation:
            interior = self._handle_grouping_op()
            expr = ExpressionNegation(next_token, right=interior)
            return expr
        else:
            return self._handle_grouping_op()

    def _handle_grouping_op(self):
        next_token = self._next_token_is([Token.ContainingGroup, Token.LogicalGroup, Token.DescendantGroup, Token.ExactMatch])
        if next_token == Token.ContainingGroup:
            interior = self._handle_and_op()
            expr = ExpressionContainingGroup(next_token, right=interior)
            next_token = self._next_token_is([Token.ContainingGroupEnd])
            if next_token != Token.ContainingGroupEnd:
                raise ValueError("Parse error: Missing closing square brackets")
        # Can we move this to the and_or level?  or does that break everything...?
        elif next_token == Token.LogicalGroup:
            expr = self._handle_and_op()
            next_token = self._next_token_is([Token.LogicalGroupEnd])
            if next_token != Token.LogicalGroupEnd:
                raise ValueError("Parse error: Missing closing paren")
        elif next_token == Token.DescendantGroup:
            interior = self._handle_and_op()
            expr = ExpressionDescendantGroup(next_token, right=interior)
            next_token = self._next_token_is([Token.DescendantGroupEnd])
            if next_token != Token.DescendantGroupEnd:
                raise ValueError("Parse error: Missing closing square bracket")
        elif next_token == Token.ExactMatch:
            interior = self._handle_and_op()
            expr = ExpressionExactMatch(next_token, right=interior)
            next_token = self._next_token_is([Token.ExactMatchEnd])
            if next_token != Token.ExactMatchEnd:
                raise ValueError("Parse error: Missing closing curly bracket")
        else:
            next_token = self._get_next_token()
            if next_token and next_token.kind == Token.Wildcard:
                expr = ExpressionWildcardNew(next_token)
            elif next_token:
                expr = Expression(next_token)

        return expr

    def _parse(self, expression_string):
        self.tokens = self._tokenize(expression_string)

        expr = self._handle_and_op()

        if self.at_token + 1 != len(self.tokens):
            raise ValueError("Parse error in search string")

        return expr

    def _tokenize(self, expression_string):
        grouping_re = r"\[\[|\[|\]\]|\]|}|{"
        paren_re = r"\)|\(|~"
        word_re = r"\?+|\band\b|\bor\b|,|[\"_\-a-zA-Z0-9/.^#\*@]+"
        re_string = fr"({grouping_re}|{paren_re}|{word_re})"
        token_re = re.compile(re_string)

        tokens = token_re.findall(expression_string)
        tokens = [Token(token) for token in tokens]

        return tokens

    def search(self, hed_string_obj):
        current_node = self.tree

        result = current_node.handle_expr(hed_string_obj)
        return result
