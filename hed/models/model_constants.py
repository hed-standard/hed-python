""" Defined constants for definitions, def labels, and expanded labels. """


class DefTagNames:
    """ Source names for definitions, def labels, and expanded labels. """

    DEF_KEY = 'Def'
    DEF_EXPAND_KEY = 'Def-expand'
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
