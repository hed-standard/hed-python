
class ErrorSeverity:
    ERROR = 1
    WARNING = 2


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
    UNIT_CLASS_INVALID_UNIT = 'unitClassInvalidUnit'
    EMPTY_TAG = 'extraComma'
    INVALID_CHARACTER = 'invalidCharacter'
    COMMA_MISSING = 'commaMissing'
    DUPLICATE = 'duplicateTag'
    PARENTHESES = 'parentheses'
    REQUIRE_CHILD = 'childRequired'
    MULTIPLE_UNIQUE = 'multipleUniqueTags'
    INVALID_TAG = 'invalidTag'
    EXTRA_SLASHES_OR_SPACES = 'extraSlashes'
    TILDES_NOT_SUPPORTED = 'invalidTilde'


class ValidationWarnings:
    REQUIRED_PREFIX_MISSING = 'requiredPrefixMissing'
    CAPITALIZATION = 'capitalization'
    UNIT_CLASS_DEFAULT_USED = 'unitClassDefaultUsed'


class SidecarErrors:
    # These are for json sidecar validation errors(sidecars can also produce most normal validation errors)
    BLANK_HED_STRING = 'blankValueString'
    WRONG_HED_DATA_TYPE = 'wrongHedDataType'
    INVALID_NUMBER_POUND_SIGNS = 'invalidNumberPoundSigns'
    TOO_MANY_POUND_SIGNS = 'tooManyPoundSigns'
    TOO_FEW_CATEGORIES = 'tooFewCategories'
    UNKNOWN_COLUMN_TYPE = 'sidecarUnknownColumn'


class SchemaErrors:
    # Schema mapping errors
    INVALID_PARENT_NODE = "invalidParent"
    NO_VALID_TAG_FOUND = "invalidTag"
    INVALID_SCHEMA = 'invalidSchema'
    EMPTY_TAG_FOUND = 'emptyTag'
    DUPLICATE_TERMS = 'duplicateTerms'


class SchemaWarnings:
    INVALID_CHARACTERS_IN_DESC = "invalidCharDesc"
    INVALID_CHARACTERS_IN_TAG = "invalidCharTag"
    INVALID_CAPITALIZATION = 'invalidCaps'


class DefinitionErrors:
    WRONG_NUMBER_DEF_TAGS = 'wrongNumberDefTags'
    WRONG_NUMBER_GROUP_TAGS = 'wrongNumberGroupTags'
    WRONG_NUMBER_PLACEHOLDER_TAGS = 'wrongNumberPlaceholderTags'
    DUPLICATE_DEFINITION = 'duplicateDefinition'
    TAG_IN_SCHEMA = 'defAlreadyInSchema'
    INVALID_DEF_EXTENSION = 'invalidDefExtension'