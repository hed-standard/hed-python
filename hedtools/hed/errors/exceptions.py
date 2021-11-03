

class HedExceptions:
    # A list of all exceptions that can be generated by the hedtools.
    FILE_NOT_FOUND = 'fileNotFound'
    BAD_PARAMETERS = 'badParameters'
    CANNOT_PARSE_XML = 'cannotParseXML'
    CANNOT_PARSE_JSON = 'cannotParseJson'
    INVALID_EXTENSION = 'invalidExtension'

    # These are actual schema issues, not that the file cannot be found or parsed
    SCHEMA_HEADER_MISSING = 'schemaHeaderMissing'
    SCHEMA_HEADER_INVALID = 'schemaHeaderInvalid'
    BAD_HED_LIBRARY_NAME = 'badHedLibraryName'
    BAD_HED_SEMANTIC_VERSION = 'BadHedSemanticVersion'
    SCHEMA_START_MISSING = 'schemaStartMissing'
    SCHEMA_END_INVALID = 'schemaEndMissing'
    HED_END_INVALID = 'hedEndMissing'
    INVALID_SECTION_SEPARATOR = 'invalidSectionSeparator'

    HED_SCHEMA_NODE_NAME_INVALID = 'HED_SCHEMA_NODE_NAME_INVALID'
    HED_WIKI_DELIMITERS_INVALID = 'HED_WIKI_DELIMITERS_INVALID'

    SCHEMA_DUPLICATE_PREFIX = 'schemaDuplicatePrefix'


class HedFileError(Exception):
    """Exception raised when a file cannot be parsed due to being malformed, file IO, etc."""
    def __init__(self, error_type, message, filename):
        self.error_type = error_type
        self.message = message
        self.filename = filename

    def format_error_message(self, include_tabbing=True, return_string_only=False,
                             name=None):
        """This takes a HedFileError exception and translates it to human readable

        Parameters
        ----------
        include_tabbing : bool
            Prefixes string with a tab if True
        return_string_only : bool
            If True, returns a string rather than an "error object"
        name : str or None
            Overrides the filename from the error if present.
            This is useful on the web code and similar that deals with temporary filenames.
        Returns
        -------
        error_list: [{}]
            A list(of one) error formatted into a human readable dictionary.
        """
        error_prefix = "ERROR: "
        if include_tabbing:
            error_prefix = "\t" + error_prefix

        error_type, message, filename = self.error_type, self.message, self.filename
        if name:
            filename = name
        error_types = {
            HedExceptions.FILE_NOT_FOUND: f"{error_prefix}{message}.  '{filename}'",
            HedExceptions.INVALID_EXTENSION: f"{error_prefix}Invalid extension.  '{filename}'",
            HedExceptions.CANNOT_PARSE_XML: f"{error_prefix}Cannot parse schema XML: "
                                            f"{message}.  '{filename}'",
            HedExceptions.CANNOT_PARSE_JSON: f"{error_prefix}Cannot parse json: {message}. '{filename}'",
            HedExceptions.SCHEMA_HEADER_MISSING: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.SCHEMA_HEADER_INVALID: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.BAD_HED_LIBRARY_NAME: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.BAD_HED_SEMANTIC_VERSION: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.SCHEMA_START_MISSING: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.SCHEMA_END_INVALID: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.HED_END_INVALID: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.INVALID_SECTION_SEPARATOR: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.HED_SCHEMA_NODE_NAME_INVALID: f"{error_prefix}{self.message}.  '{filename}'",
            HedExceptions.HED_WIKI_DELIMITERS_INVALID: f"{error_prefix}{self.message}.  '{filename}'"
        }
        default_error_message = f'{error_prefix}Internal Error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type,
                        'message': error_message}

        if return_string_only:
            return error_object['message']

        return [error_object]
