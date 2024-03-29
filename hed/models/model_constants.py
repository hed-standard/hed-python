COLUMN_TO_HED_TAGS = "column_to_hed_tags"
ROW_HED_STRING = "HED"
COLUMN_ISSUES = "column_issues"
ROW_ISSUES = "row_issues"


class DefTagNames:
    """ Source names for definitions, def labels, and expanded labels"""

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

    ONSET_KEY = ONSET_ORG_KEY.lower()
    OFFSET_KEY = OFFSET_ORG_KEY.lower()
    INSET_KEY = INSET_ORG_KEY.lower()

    TEMPORAL_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY}
