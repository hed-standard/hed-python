
class ErrorContext:
    """Indicates the context this error took place in, each error potentially having multiple contexts"""
    FILE_NAME = 'filename'
    SIDECAR_COLUMN_NAME = 'sidecarColumnName'
    SIDECAR_CUE_NAME = 'sidecarCueName'
    SIDECAR_HED_STRING = 'sidecarHedString'
    ROW = 'row'
    COLUMN = 'column'


class ValidationErrors:
    # General validation errors
    INVALID_FILENAME = 'invalidFileName'
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
