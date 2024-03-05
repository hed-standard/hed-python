""" Defined constants for definitions, def labels, and expanded labels. """
class DefTagNames:
    """ Source names for definitions, def labels, and expanded labels. """

    DEF_ORG_KEY = 'Def'
    DEF_EXPAND_ORG_KEY = 'Def-expand'
    DEFINITION_ORG_KEY = "Definition"
    DEF_KEY = DEF_ORG_KEY.lower()
    DEF_EXPAND_KEY = DEF_EXPAND_ORG_KEY.lower()
    DEFINITION_KEY = DEFINITION_ORG_KEY.lower()
    DEF_KEYS = (DEF_KEY, DEF_EXPAND_KEY)

    ONSET_ORG_KEY = "Onset"
    OFFSET_ORG_KEY = "Offset"
    INSET_ORG_KEY = "Inset"
    DURATION_ORG_KEY = "Duration"
    DELAY_ORG_KEY = "Delay"

    ONSET_KEY = ONSET_ORG_KEY.lower()
    OFFSET_KEY = OFFSET_ORG_KEY.lower()
    INSET_KEY = INSET_ORG_KEY.lower()
    DURATION_KEY = DURATION_ORG_KEY.lower()
    DELAY_KEY = DELAY_ORG_KEY.lower()

    TEMPORAL_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY}
    DURATION_KEYS = {DURATION_KEY, DELAY_KEY}

    ALL_TIME_KEYS = TEMPORAL_KEYS.union(DURATION_KEYS)
