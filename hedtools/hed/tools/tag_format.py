from hed.util import error_reporter
from hed.util.error_types import SchemaErrors, ErrorContext
from hed.util import hed_string_util
from hed.util.hed_schema import HedSchema


class TagFormat:
    """
    Class to convert hed3 tags between short and long form.
    """

    def __init__(self, hed_xml_file=None, hed_schema=None, error_handler=None):
        """

        Parameters
        ----------
        hed_xml_file : str
            hed xml schema filepath to create HedSchema from
        hed_schema : HedSchema, default None
             Used in place of hed_xml_file
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        """
        if hed_schema is None:
            hed_schema = HedSchema(hed_xml_file)
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        self._error_handler = error_handler
        self._short_tag_mapping = hed_schema.short_tag_mapping

    def convert_hed_string_to_short(self, hed_string):
        """
        Convert a hed3 string from any form to the shortest.

        This goes through the hed string, splits it into tags, then converts
        each tag individually

        Parameters
        ----------
        hed_string: str
            a hed string containing any number of tags
        Returns
        -------
            converted_string: str
                The converted string
            errors: list
                a list of validation errors while converting
        """
        if not self._short_tag_mapping:
            error = self._error_handler.format_schema_error(SchemaErrors.INVALID_SCHEMA, hed_tag=hed_string)
            return hed_string, error

        hed_string = hed_string_util.remove_slashes_and_spaces(hed_string)

        errors = []
        if hed_string == "":
            errors += self._error_handler.format_schema_error(SchemaErrors.EMPTY_TAG_FOUND, "")
            return hed_string, errors

        hed_tags = hed_string_util.split_hed_string(hed_string)
        final_string = ""

        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                short_tag_string, single_error = self._convert_to_short_tag(tag)
                if single_error:
                    for error in single_error:
                        errors += self._error_handler.reformat_schema_error(error, hed_string, startpos)
                final_string += short_tag_string
            else:
                final_string += tag
                # no_spaces_delimiter = tag.replace(" ", "")
                # final_string += no_spaces_delimiter

        return final_string, errors

    def convert_hed_string_to_long(self, hed_string):
        """
        Convert a hed3 string from any form to the longest.

        This goes through the hed string, splits it into tags, then converts
        each tag individually

        Parameters
        ----------
        hed_string: str
            a hed string containing any number of tags
        Returns
        -------
        converted_string: str
            The converted string
        errors: list
            a list of validation errors while converting
        """
        if not self._short_tag_mapping:
            error = self._error_handler.format_schema_error(SchemaErrors.INVALID_SCHEMA, hed_string)
            return hed_string, error

        hed_string = hed_string_util.remove_slashes_and_spaces(hed_string)

        errors = []
        if hed_string == "":
            errors += self._error_handler.format_schema_error(SchemaErrors.EMPTY_TAG_FOUND, "")
            return hed_string, errors

        hed_tags = hed_string_util.split_hed_string(hed_string)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                converted_tag, single_error = self._convert_to_long_tag(tag)
                if single_error:
                    for error in single_error:
                        errors += self._error_handler.reformat_schema_error(error, hed_string, startpos)
                final_string += converted_tag
            else:
                final_string += tag
                # no_spaces_delimiter = tag.replace(" ", "")
                # final_string += no_spaces_delimiter

        return final_string, errors

    def _convert_to_long_tag(self, hed_tag):
        """
        This takes a hed tag(short or long form) and converts it to the long form
        Works left to right.(mostly relevant for errors)
        Note: This only does minimal validation

        eg 'Event'                    - Returns ('Event', None)
           'Sensory event'            - Returns ('Event/Sensory event', None)
        Takes Value:
           'Environmental sound/Unique Value'
                                      - Returns ('Item/Sound/Environmental Sound/Unique Value', None)
        Extension Allowed:
            'Experiment control/demo_extension'
                                      - Returns ('Event/Experiment Control/demo_extension/', None)
            'Experiment control/demo_extension/second_part'
                                      - Returns ('Event/Experiment Control/demo_extension/second_part', None)


        Parameters
        ----------
        hed_tag: str
            A single hed tag(long or short)
        Returns
        -------
        converted_tag: str
            The converted tag
        errors: list
            a list of errors while converting
        """
        # Remove leading and trailing slashes
        if hed_tag.startswith('/'):
            hed_tag = hed_tag[1:]
        if hed_tag.endswith('/'):
            hed_tag = hed_tag[:-1]

        clean_tag = hed_tag.lower()
        split_tags = clean_tag.split("/")

        index_end = 0
        found_unknown_extension = False
        found_index_end = 0
        found_long_org_tag = None
        # Iterate over tags left to right keeping track of current index
        for tag in split_tags:
            tag_len = len(tag)
            # Skip slashes
            if index_end != 0:
                index_end += 1
            index_start = index_end
            index_end += tag_len

            # If we already found an unknown tag, it's implicitly an extension.  No known tags can follow it.
            if not found_unknown_extension:
                if tag not in self._short_tag_mapping:
                    found_unknown_extension = True
                    if not found_long_org_tag:
                        error = self._error_handler.format_schema_error(SchemaErrors.NO_VALID_TAG_FOUND, hed_tag,
                                                                   index_start, index_end)
                        return hed_tag, error
                    continue

                long_org_tag = self._short_tag_mapping[tag]
                tag_string = long_org_tag.lower()
                main_hed_portion = clean_tag[:index_end]

                # Verify the tag has the correct path above it.
                if not tag_string.endswith(main_hed_portion):
                    error = self._error_handler.format_schema_error(SchemaErrors.INVALID_PARENT_NODE, hed_tag,
                                                               index_start, index_end,
                                                               long_org_tag)
                    return hed_tag, error
                found_index_end = index_end
                found_long_org_tag = long_org_tag
            else:
                # These means we found a known tag in the remainder/extension section, which is an error
                if tag in self._short_tag_mapping:
                    error = self._error_handler.format_schema_error(SchemaErrors.INVALID_PARENT_NODE, hed_tag,
                                                               index_start, index_end,
                                                               self._short_tag_mapping[tag])
                    return hed_tag, error

        remainder = hed_tag[found_index_end:]

        long_tag_string = found_long_org_tag + remainder
        return long_tag_string, []

    def _convert_to_short_tag(self, hed_tag):
        """
        This takes a hed tag(short or long form) and converts it to the short form
        Works left to right.(mostly relevant for errors)
        Note: This only does minimal validation

        eg 'Event'                    - Returns ('Event', [])
           'Event/Sensory event'      - Returns ('Sensory event', [])
        Takes Value:
           'Item/Sound/Environmental sound/Unique Value'
                                      - Returns ('Environmental Sound/Unique Value', [])
        Extension Allowed:
            'Event/Experiment control/demo_extension'
                                      - Returns ('Experiment Control/demo_extension/', [])
            'Event/Experiment control/demo_extension/second_part'
                                      - Returns ('Experiment Control/demo_extension/second_part', [])


        Parameters
        ----------
        hed_tag: str
            A single hed tag(long or short)
        Returns
        -------
        converted_tag: str
            The converted tag
        errors: list
            a list of errors while converting
        """
        # Remove leading and trailing slashes
        if hed_tag.startswith('/'):
            hed_tag = hed_tag[1:]
        if hed_tag.endswith('/'):
            hed_tag = hed_tag[:-1]

        clean_tag = hed_tag.lower()
        split_tag = clean_tag.split("/")

        found_long_org_tag = None
        index = len(hed_tag)
        last_found_index = index
        found_short_tag = None
        # Iterate over tags right to left keeping track of current character index
        for tag in reversed(split_tag):
            # As soon as we find a non extension tag, mark down the index and bail.
            if tag in self._short_tag_mapping:
                found_long_org_tag = self._short_tag_mapping[tag]
                found_short_tag = tag
                last_found_index = index
                index -= len(tag)
                break

            last_found_index = index
            index -= len(tag)
            # Skip slashes
            if index != 0:
                index -= 1

        if found_long_org_tag is None:
            error = self._error_handler.format_schema_error(SchemaErrors.NO_VALID_TAG_FOUND, hed_tag,
                                                       index, last_found_index)
            return hed_tag, error

        # Verify the tag has the correct path above it.
        main_hed_portion = clean_tag[:last_found_index]
        tag_string = found_long_org_tag.lower()
        if not tag_string.endswith(main_hed_portion):
            error = self._error_handler.format_schema_error(SchemaErrors.INVALID_PARENT_NODE, hed_tag, index,
                                                       last_found_index, found_long_org_tag)
            return hed_tag, error

        remainder = hed_tag[last_found_index:]
        short_tag = found_long_org_tag[-len(found_short_tag):]
        short_tag_string = short_tag + remainder
        return short_tag_string, []

    def _convert_file(self, input_file, conversion_function):
        """  Runs a passed in conversion function over a given HedFileInput object
        Parameters
        ----------
        input_file : HedFileInput
            The file to convert hed strings in
        conversion_function : (str) -> (str, [])
            Conversion function for any given hed string.
        Returns
        -------
        input_file: HedFileInput
            The same passed in object converted in place
        error_list: []
            list of dicts of errors while converting
        """
        error_list = []
        for row_number, row_hed_string, column_to_hed_tags_dictionary in input_file:
            for column_number in column_to_hed_tags_dictionary:
                self._error_handler.push_error_context(ErrorContext.COLUMN, row_number, column_context=column_number)
                old_text = column_to_hed_tags_dictionary[column_number]
                new_text, errors = conversion_function(old_text)
                input_file.set_cell(row_number, column_number, new_text,
                                    include_column_prefix_if_exist=False)

                self._error_handler.pop_error_context()

        return input_file, error_list

    def convert_file_to_short_tags(self, input_file):
        """
        Takes an input file and iterates over each cell with tags and converts to short.

        Parameters
        ----------
        input_file : a HedFileInput
            The file to convert hed strings in
        Returns
        -------
        input_file: HedFileInput
            The same passed in object converted in place
        error_list: []
            list of dicts of errors while converting
        """
        return self._convert_file(input_file, self.convert_hed_string_to_short)

    def convert_file_to_long_tags(self, input_file):
        """Takes an input file and iterates over each cell with tags and converts to long.
        Parameters
        ----------
        input_file : a HedFileInput
            The file to convert hed strings in
        Returns
        -------
        input_file: HedFileInput
            The same passed in object converted in place
        error_list: []
            list of dicts of errors while converting
        """
        return self._convert_file(input_file, self.convert_hed_string_to_long)
