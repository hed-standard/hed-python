""" Known error codes as reported in the HED specification. """

known_error_codes = {
    "hed_validation_errors": [
        "CHARACTER_INVALID",
        "COMMA_MISSING",
        "DEF_EXPAND_INVALID",
        "DEF_INVALID",
        "DEFINITION_INVALID",
        "ELEMENT_DEPRECATED",
        "PARENTHESES_MISMATCH",
        "PLACEHOLDER_INVALID",
        "REQUIRED_TAG_MISSING",
        "SIDECAR_BRACES_INVALID",
        "SIDECAR_INVALID",
        "SIDECAR_KEY_MISSING",
        "STYLE_WARNING",
        "TAG_EMPTY",
        "TAG_EXPRESSION_REPEATED",
        "TAG_EXTENDED",
        "TAG_EXTENSION_INVALID",
        "TAG_GROUP_ERROR",
        "TAG_INVALID",
        "TAG_NAMESPACE_PREFIX_INVALID",
        "TAG_NOT_UNIQUE",
        "TAG_REQUIRES_CHILD",
        "TEMPORAL_TAG_ERROR",
        "TILDES_UNSUPPORTED",
        "UNITS_INVALID",
        "UNITS_MISSING",
        "VALUE_INVALID",
        "VERSION_DEPRECATED"
    ],
    "schema_validation_errors": [
        "SCHEMA_ATTRIBUTE_INVALID",
        "SCHEMA_ATTRIBUTE_VALUE_INVALID",
        "SCHEMA_CHARACTER_INVALID",
        "SCHEMA_DUPLICATE_NODE",
        "SCHEMA_HEADER_INVALID",
        "SCHEMA_LIBRARY_INVALID",
        "SCHEMA_SECTION_MISSING",
        "SCHEMA_VERSION_INVALID",
        "WIKI_DELIMITERS_INVALID",
        "WIKI_LINE_START_INVALID",
        "WIKI_SEPARATOR_INVALID",
        "XML_SYNTAX_INVALID"
    ]
}
