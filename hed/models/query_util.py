""" Classes representing HED search results and tokens. """


class SearchResult:
    """ Holder for and manipulation of search results. """
    def __init__(self, group, tag):
        self.group = group
        # todo: rename tag: children
        if not isinstance(tag, list):
            new_tags = [tag]
        else:
            new_tags = tag.copy()
        self.tags = new_tags

    def merge_and_result(self, other):
        """Returns a new result, with the combined tags/groups from this and other."""
        # Returns a new
        new_tags = self.tags.copy()
        for tag in other.tags:
            if any(tag is this_tag for this_tag in self.tags):
                continue
            new_tags.append(tag)
        new_tags.sort(key=lambda x: str(x))

        if self.group != other.group:
            raise ValueError("Internal error")
        return SearchResult(self.group, new_tags)

    def has_same_tags(self, other):
        """Checks if these two results have the same tags/groups by identity(not equality)"""
        if self.group != other.group:
            return False

        if len(self.tags) != len(other.tags):
            return False

        return all(tag is tag2 for tag, tag2 in zip(self.tags, other.tags))

    def __str__(self):
        return str(self.group) + " Tags: " + "---".join([str(tag) for tag in self.tags])


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
