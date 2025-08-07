""" Holder for and manipulation of search results. """
import re

from hed.models.query_expressions import Expression, ExpressionAnd, ExpressionWildcardNew, ExpressionOr, \
    ExpressionNegation, ExpressionDescendantGroup, ExpressionExactMatch
from hed.models.query_util import Token


class QueryHandler:
    """Parse a search expression into a form than can be used to search a HED string."""

    def __init__(self, expression_string):
        """Compiles a QueryHandler for a particular expression, so it can be used to search HED strings.

        Basic Input Examples:

        'Event' - Finds any strings with Event, or a descendent tag of Event such as Sensory-event.

        'Event && Action' - Find any strings with Event and Action, including descendant tags.

        'Event || Action' - Same as above, but it has either.

        '"Event"' - Finds the Event tag, but not any descendent tags.

        `Def/DefName/*` - Find Def/DefName instances with placeholders, regardless of the value of the placeholder.

        'Eve*' - Find any short tags that begin with Eve*, such as Event, but not Sensory-event.

        '[Event && Action]' - Find a group that contains both Event and Action(at any level).

        '{Event && Action}' - Find a group with Event And Action at the same level.

        '{Event && Action:}' - Find a group with Event And Action at the same level, and nothing else.

        '{Event && Action:Agent}' - Find a group with Event And Action at the same level, and optionally an Agent tag.

        Practical Complex Example:

        {(Onset || Offset), (Def || {Def-expand}): ???} - A group with an onset tag,
                                    a def tag or def-expand group, and an optional wildcard group

        Parameters:
            expression_string(str): The query string.
        """
        self.tokens = []
        self.at_token = -1
        self.tree = self._parse(expression_string.casefold())
        self._org_string = expression_string

    def search(self, hed_string_obj) -> list:
        """ Search for the query in the given HED string.

        Parameters:
            hed_string_obj (HedString): String to search

        Returns:
            list[any]: List of search result. Generally you should just treat this as a bool. True if a match was found.
        """
        current_node = self.tree

        result = current_node.handle_expr(hed_string_obj)
        return result

    def __str__(self):
        return str(self.tree)

    def _get_next_token(self):
        """Returns the current token and advances the counter"""
        self.at_token += 1
        if self.at_token >= len(self.tokens):
            raise ValueError("Parse error in get next token")
        return self.tokens[self.at_token]

    def _next_token_is(self, kinds):
        """Returns the current token if it matches kinds, and advances the counter"""
        if self.at_token + 1 >= len(self.tokens):
            return None
        if self.tokens[self.at_token + 1].kind in kinds:
            return self._get_next_token()
        return None

    def _parse(self, expression_string):
        """Parse the string and build an expression tree"""
        self.tokens = self._tokenize(expression_string)

        expr = self._handle_or_op()

        if self.at_token + 1 != len(self.tokens):
            raise ValueError("Parse error in search string")

        return expr

    @staticmethod
    def _tokenize(expression_string):
        """Tokenize the expression string into a list"""
        grouping_re = r"\[\[|\[|\]\]|\]|}|{|:"
        paren_re = r"\)|\(|~"
        word_re = r"\?+|\&\&|\|\||,|[\"_\-a-zA-Z0-9/.^#\*@]+"
        re_string = fr"({grouping_re}|{paren_re}|{word_re})"
        token_re = re.compile(re_string)

        tokens = token_re.findall(expression_string)
        tokens = [Token(token) for token in tokens]

        return tokens

    def _handle_and_op(self):
        expr = self._handle_negation()
        next_token = self._next_token_is([Token.And])
        while next_token:
            right = self._handle_negation()
            if next_token.kind == Token.And:
                expr = ExpressionAnd(next_token, expr, right)
            next_token = self._next_token_is([Token.And])
        return expr

    def _handle_or_op(self):
        expr = self._handle_and_op()
        next_token = self._next_token_is([Token.Or])
        while next_token:
            right = self._handle_and_op()
            if next_token.kind == Token.Or:
                expr = ExpressionOr(next_token, expr, right)
            next_token = self._next_token_is([Token.Or])
        return expr

    def _handle_negation(self):
        next_token = self._next_token_is([Token.LogicalNegation])
        if next_token == Token.LogicalNegation:
            interior = self._handle_grouping_op()
            if "?" in str(interior):
                raise ValueError("Cannot negate wildcards, or expressions that contain wildcards."
                                 "Use {required_expression : optional_expression}.")
            expr = ExpressionNegation(next_token, right=interior)
            return expr
        else:
            return self._handle_grouping_op()

    def _handle_grouping_op(self):
        next_token = self._next_token_is(
            [Token.LogicalGroup, Token.DescendantGroup, Token.ExactMatch])
        if next_token == Token.LogicalGroup:
            expr = self._handle_or_op()
            next_token = self._next_token_is([Token.LogicalGroupEnd])
            if next_token != Token.LogicalGroupEnd:
                raise ValueError("Parse error: Missing closing paren")
        elif next_token == Token.DescendantGroup:
            interior = self._handle_or_op()
            expr = ExpressionDescendantGroup(next_token, right=interior)
            next_token = self._next_token_is([Token.DescendantGroupEnd])
            if next_token != Token.DescendantGroupEnd:
                raise ValueError("Parse error: Missing closing square bracket")
        elif next_token == Token.ExactMatch:
            interior = self._handle_or_op()
            expr = ExpressionExactMatch(next_token, right=interior)
            next_token = self._next_token_is([Token.ExactMatchEnd, Token.ExactMatchOptional])
            if next_token == Token.ExactMatchOptional:
                # We have an optional portion - this needs to now be an exact match
                expr.optional = "none"
                next_token = self._next_token_is([Token.ExactMatchEnd])
                if next_token != Token.ExactMatchEnd:
                    optional_portion = self._handle_or_op()
                    expr.left = optional_portion
                    next_token = self._next_token_is([Token.ExactMatchEnd])
                if "~" in str(expr):
                    raise ValueError("Cannot use negation in exact matching groups,"
                                     " as it's not clear what is being matched.\n"
                                     "{thing and ~(expression)} is allowed.")

            if next_token is None:
                raise ValueError("Parse error: Missing closing curly bracket")
        else:
            next_token = self._get_next_token()
            if next_token and next_token.kind == Token.Wildcard:
                expr = ExpressionWildcardNew(next_token)
            elif next_token:
                expr = Expression(next_token)
            else:
                expr = None

        return expr
