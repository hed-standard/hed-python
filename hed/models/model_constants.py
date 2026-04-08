"""Defined constants for definitions, def labels, and expanded labels."""

from enum import IntEnum


class TopTagReturnType(IntEnum):
    """Return-type selector for :meth:`~hed.models.HedString.find_top_level_tags`.

    Pass one of these constants as the ``include_groups`` argument to control
    whether the method returns anchor tags, containing groups, or (tag, group) pairs.
    """

    TAGS = 0
    GROUPS = 1
    BOTH = 2


class DefTagNames:
    """Source names for definitions, def labels, and expanded labels."""

    DEF_KEY = "Def"
    DEF_EXPAND_KEY = "Def-expand"
    DEFINITION_KEY = "Definition"

    ONSET_KEY = "Onset"
    OFFSET_KEY = "Offset"
    INSET_KEY = "Inset"
    DURATION_KEY = "Duration"
    DELAY_KEY = "Delay"

    TEMPORAL_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY}
    DURATION_KEYS = {DURATION_KEY, DELAY_KEY}

    ALL_TIME_KEYS = TEMPORAL_KEYS.union(DURATION_KEYS)
    TIMELINE_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY, DELAY_KEY}
