
class ErrorSeverity:
    ERROR = 1
    WARNING = 10


class ErrorContext:
    """Indicates the context this error took place in, each error potentially having multiple contexts"""
    # Use this one to display any passed in message without modification
    CUSTOM_TITLE = 'ec_title'
    FILE_NAME = 'ec_filename'
    SIDECAR_COLUMN_NAME = 'ec_sidecarColumnName'
    SIDECAR_KEY_NAME = 'ec_sidecarKeyName'
    ROW = 'ec_row'
    COLUMN = 'ec_column'
    HED_STRING = 'ec_HedString'


class ValidationErrors:
    # General validation errors
    HED_CHARACTER_INVALID = 'HED_CHARACTER_INVALID'
    HED_COMMA_MISSING = 'HED_COMMA_MISSING'
    HED_DEF_UNMATCHED = "HED_DEF_UNMATCHED"
    HED_DEFINITION_INVALID = "HED_DEFINITION_INVALID"
    # HED_GENERIC_ERROR
    # HED_GENERIC_WARNING
    # HED_LIBRARY_UNMATCHED
    HED_NODE_NAME_EMPTY = 'HED_NODE_NAME_EMPTY'
    #HED_ONSET_OFFSET_ERROR
    HED_PARENTHESES_MISMATCH = 'HED_PARENTHESES_MISMATCH'
    HED_PLACEHOLDER_INVALID = 'HED_PLACEHOLDER_INVALID'
    HED_REQUIRED_TAG_MISSING = 'HED_REQUIRED_TAG_MISSING'
    HED_SIDECAR_KEY_MISSING = 'HED_SIDECAR_KEY_MISSING'
    HED_STYLE_WARNING = 'HED_STYLE_WARNING'
    HED_TAG_EMPTY = 'HED_TAG_EMPTY'
    HED_TAG_EXTENDED = 'HED_TAG_EXTENDED'
    HED_TAG_GROUP_ERROR = "HED_TAG_GROUP_ERROR"
    HED_TAG_INVALID = "HED_TAG_INVALID"
    HED_TAG_NOT_UNIQUE = 'HED_TAG_NOT_UNIQUE'
    HED_TAG_REPEATED = 'HED_TAG_REPEATED'
    HED_TAG_REQUIRES_CHILD = 'HED_TAG_REQUIRES_CHILD'
    HED_TILDES_UNSUPPORTED = 'HED_TILDES_UNSUPPORTED'
    # HED_UNITS_DEFAULT_USED
    HED_UNITS_INVALID = 'HED_UNITS_INVALID'
    HED_UNITS_MISSING = 'HED_UNITS_MISSING'
    HED_VALUE_INVALID = 'HED_VALUE_INVALID'
    # HED_VALUE_IS_NODE
    # HED_VERSION_WARNING


    # Below here shows what the given error maps to
    # HED_TAG_EMPTY
    HED_GROUP_EMPTY = 'emptyHedGroup'
    # HED_CHARACTER_INVALID
    INVALID_TAG_CHARACTER = 'invalidTagCharacter'

    # These are all HED_TAG_INVALID
    INVALID_EXTENSION = 'invalidExtension'
    INVALID_PARENT_NODE = "invalidParent"
    NO_VALID_TAG_FOUND = "invalidTag"

    # These are misc errors that need categorization.
    HED_TOP_LEVEL_TAG = "HED_TOP_LEVEL_TAG"
    HED_MULTIPLE_TOP_TAGS = "HED_MULTIPLE_TOP_TAGS"
    HED_TAG_GROUP_TAG = "HED_TAG_GROUP_TAG"

    HED_DEF_VALUE_MISSING = "HED_DEF_VALUE_MISSING"
    HED_DEF_VALUE_EXTRA = "HED_DEF_VALUE_EXTRA"

class SidecarErrors:
    # These are for json sidecar validation errors(sidecars can also produce most normal validation errors)
    BLANK_HED_STRING = 'blankValueString'
    WRONG_HED_DATA_TYPE = 'wrongHedDataType'
    INVALID_POUND_SIGNS_VALUE = 'invalidNumberPoundSigns'
    INVALID_POUND_SIGNS_CATEGORY = 'tooManyPoundSigns'
    UNKNOWN_COLUMN_TYPE = 'sidecarUnknownColumn'


class SchemaErrors:
    DUPLICATE_TERMS = 'duplicateTerms'


class SchemaWarnings:
    INVALID_CHARACTERS_IN_DESC = "invalidCharDesc"
    INVALID_CHARACTERS_IN_TAG = "invalidCharTag"
    INVALID_CAPITALIZATION = 'invalidCaps'


# These are all HED_DEFINITION_INVALID errors
class DefinitionErrors:
    WRONG_NUMBER_DEFINITION_TAGS = 'wrongNumberDefTags'
    WRONG_NUMBER_GROUP_TAGS = 'wrongNumberGroupTags'
    WRONG_NUMBER_PLACEHOLDER_TAGS = 'wrongNumberPlaceholderTags'
    DUPLICATE_DEFINITION = 'duplicateDefinition'
    TAG_IN_SCHEMA = 'defAlreadyInSchema'
    INVALID_DEFINITION_EXTENSION = 'invalidDefExtension'
