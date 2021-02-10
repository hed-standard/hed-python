from enum import Enum


class ErrorSeverity:
    ERROR = 1
    WARNING = 2


class ErrorContext(Enum):
    """Indicates the context this error took place in, each error potentially having multiple contexts"""
    CUSTOM_TITLE = 'title'
    FILE_NAME = 'filename'
    SIDECAR_COLUMN_NAME = 'sidecarColumnName'
    SIDECAR_KEY_NAME = 'sidecarKeyName'
    SIDECAR_HED_STRING = 'sidecarHedString'
    ROW = 'row'
    COLUMN = 'column'
    # Use this one to display any passed in message without modification


class ValidationErrors:
    # General validation errors
    UNIT_CLASS_INVALID_UNIT = 'unitClassInvalidUnit'
    EXTRA_DELIMITER = 'extraDelimiter'
    INVALID_CHARACTER = 'invalidCharacter'
    INVALID_COMMA = 'extraCommaOrInvalid'
    COMMA_MISSING = 'commaMissing'
    DUPLICATE = 'duplicateTag'
    PARENTHESES = 'parentheses'
    REQUIRE_CHILD = 'childRequired'
    EXTRA_TILDE = 'tooManyTildes'
    MULTIPLE_UNIQUE = 'multipleUniqueTags'
    INVALID_TAG = 'invalidTag'


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
    WRONG_NUMBER_ORG_TAGS = 'wrongNumberOrgTags'
    WRONG_NUMBER_GROUP_TAGS = 'wrongNumberGroupTags'
    DUPLICATE_DEFINITION = 'duplicateDefinition'
    TAG_IN_SCHEMA = 'defAlreadyInSchema'
