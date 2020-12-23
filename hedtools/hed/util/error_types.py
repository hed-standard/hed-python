
class ValidationErrors:
    # General validation errors
    ROW = 'row'
    COLUMN = 'column'
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
    # These are for json sidecar validation errors(sidecars can also produce most normal errors)
    SIDECAR_FILE_NAME = 'sidecarFilename'
    SIDECAR_COLUMN_NAME = 'sidecarColumnName'
    SIDECAR_HED_STRING = 'sidecarHedString'
    INVALID_FILENAME = 'sidecarInvalidFilename'
    CANNOT_PARSE_JSON = 'cannotParseJson'
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