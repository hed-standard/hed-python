"""Classes representing HED search results and tokens."""


class SearchResult:
    """Holder for and manipulation of search results.

    Represents a query match result consisting of:
    - group: The containing HedGroup where matches were found
    - children: The specific matched elements (tags/groups) within that group
                (NOT all children of the group - only those that satisfied the query)

    Example: When searching for "Red" in the HED string "(Red, Blue, Green)":
        - group = the containing group (Red, Blue, Green)
        - children = [Red] (only the matched tag)
    """

    def __init__(self, group, children):
        """Initialize a search result.

        Parameters:
            group (HedGroup): The group where the children were found.
            children (HedTag, HedGroup, or list): The matched child elements (tags or groups)
                that satisfied the query condition. Can be:
                - Single tag/group that matched
                - List of tags/groups that matched
                - Empty list (for negation or when group matched but no specific children)
        """
        self.group = group
        if not isinstance(children, list):
            new_children = [children]
        else:
            new_children = children.copy()
        self.children = new_children

    def merge_and_result(self, other):
        """Returns a new result with the combined children from this and other.

        Parameters:
            other (SearchResult): Another search result to merge with this one.

        Returns:
            SearchResult: A new SearchResult containing unique children from both results.

        Raises:
            ValueError: If the groups are not the same.
        """
        new_children = self.children.copy()
        for child in other.children:
            if any(child is this_child for this_child in self.children):
                continue
            new_children.append(child)
        new_children.sort(key=str)

        if self.group != other.group:
            raise ValueError("Internal error")
        return SearchResult(self.group, new_children)

    def has_same_children(self, other):
        """Checks if these two results have the same children by identity (not equality).

        Parameters:
            other (SearchResult): Another search result to compare with this one.

        Returns:
            bool: True if both results have the same group and identical children.
        """
        if self.group != other.group:
            return False

        if len(self.children) != len(other.children):
            return False

        return all(child is child2 for child, child2 in zip(self.children, other.children, strict=False))

    # Backward compatibility alias
    has_same_tags = has_same_children

    def __str__(self):
        return str(self.group) + " Children: " + "---".join([str(child) for child in self.children])


class Token:
    """Represents a single term/character"""

    And = 0
    Tag = 1
    DescendantGroup = 4
    DescendantGroupEnd = 5
    Or = 6
    LogicalGroup = 7
    LogicalGroupEnd = 8
    LogicalNegation = 9
    Wildcard = 10
    ExactMatch = 11
    ExactMatchEnd = 12
    ExactMatchOptional = 14
    NotInLine = 13  # Not currently a token. In development and may become one.

    def __init__(self, text):
        """Initialize a token for query parsing.

        Parameters:
            text (str): The text representation of the token.
        """
        tokens = {
            ",": Token.And,
            "&&": Token.And,
            "||": Token.Or,
            "[": Token.DescendantGroup,
            "]": Token.DescendantGroupEnd,
            "(": Token.LogicalGroup,
            ")": Token.LogicalGroupEnd,
            "~": Token.LogicalNegation,
            "?": Token.Wildcard,  # Any tag or group
            "??": Token.Wildcard,  # Any tag
            "???": Token.Wildcard,  # Any Group
            "{": Token.ExactMatch,  # Nothing else
            "}": Token.ExactMatchEnd,  # Nothing else
            ":": Token.ExactMatchOptional,
            "@": Token.NotInLine,
        }
        self.kind = tokens.get(text, Token.Tag)
        self.text = text

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if self.kind == other:
            return True
        return False
