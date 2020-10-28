from hed.utilities.util import error_reporter, format_util
from hed.utilities.util.map_schema import MapSchema


class TagFormat:
    """     Class to convert hed3 tags between short and long form.
       """
    def __init__(self, hed_xml_file=None, hed_tree=None):
        self.map_schema = MapSchema(hed_xml_file, hed_tree)

    def convert_hed_string_to_short(self, hed_string):
        """ Convert a hed string from any form to the shortest.

            This goes through the hed string, splits it into tags, then converts
            each tag individually

         Parameters
            ----------
            hed_string: str
                a hed string containing any number of tags
            Returns
            -------
                str: The converted string
        """
        if not self.map_schema.no_duplicate_tags:
            error = error_reporter.report_error_type(error_reporter.INVALID_SCHEMA, hed_string, 0, len(hed_string))
            return hed_string, [error]

        hed_string = format_util.remove_slashes_and_spaces(hed_string)

        errors = []
        if hed_string == "":
            errors.append(error_reporter.report_error_type(error_reporter.EMPTY_TAG_FOUND, ""))
            return hed_string, errors

        hed_tags = format_util.split_hed_string(hed_string)
        final_string = ""

        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                short_tag_string, single_error = self._convert_to_short_tag(tag)
                if single_error:
                    errors.append(single_error)
                final_string += short_tag_string
            else:
                final_string += tag
                # no_spaces_delimeter = tag.replace(" ", "")
                # final_string += no_spaces_delimeter

        return final_string, errors

    def convert_hed_string_to_long(self, hed_string):
        """ Convert a hed string from any form to the longest.

            This goes through the hed string, splits it into tags, then converts
            each tag individually

         Parameters
            ----------
            hed_string: str
                a hed string containing any number of tags
            Returns
            -------
                str: The converted string
        """
        if not self.map_schema.no_duplicate_tags:
            error = error_reporter.report_error_type(error_reporter.INVALID_SCHEMA, hed_string, 0, len(hed_string))
            return hed_string, [error]

        hed_string = format_util.remove_slashes_and_spaces(hed_string)

        errors = []
        if hed_string == "":
            errors.append(error_reporter.report_error_type(error_reporter.EMPTY_TAG_FOUND, ""))
            return hed_string, errors

        hed_tags = format_util.split_hed_string(hed_string)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                converted_tag, single_error = self._convert_to_long_tag(tag)
                if single_error:
                    errors.append(single_error)
                final_string += converted_tag
            else:
                final_string += tag
                # no_spaces_delimeter = tag.replace(" ", "")
                # final_string += no_spaces_delimeter

        return final_string, errors

    def _convert_to_long_tag(self, hed_tag):
        """This takes a hed tag(short or long form) and converts it to the long form
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

            Returns
            -------
            tuple.  (long_tag, error).  If not found, (original_tag, error)

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
        found_tag_entry = None
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
                if tag not in self.map_schema.tag_dict:
                    found_unknown_extension = True
                    if not found_tag_entry:
                        error = error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND, hed_tag,
                                                                 index_start, index_end)
                        return hed_tag, error
                    continue

                tag_entry = self.map_schema.tag_dict[tag]
                tag_string = tag_entry.long_clean_tag
                main_hed_portion = clean_tag[:index_end]

                # Verify the tag has the correct path above it.
                if not tag_string.endswith(main_hed_portion):
                    error = error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, hed_tag,
                                                             index_start, index_end,
                                                             tag_entry.long_org_tag)
                    return hed_tag, error
                found_index_end = index_end
                found_tag_entry = tag_entry
            else:
                # These means we found a known tag in the remainder/extension section, which is an error
                if tag in self.map_schema.tag_dict:
                    error = error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, hed_tag,
                                                             index_start, index_end,
                                                             self.map_schema.tag_dict[tag].long_org_tag)
                    return hed_tag, error

        remainder = hed_tag[found_index_end:]

        long_tag_string = found_tag_entry.long_org_tag + remainder
        return long_tag_string, None

    def _convert_to_short_tag(self, hed_tag):
        """This takes a hed tag(short or long form) and converts it to the long form
            Works right to left.(mostly relevant for errors)
            Note: This only does minimal validation

            eg 'Event'                    - Returns ('Event', None)
               'Event/Sensory event'      - Returns (Sensory event', None)
            Takes Value:
               'Item/Sound/Environmental sound/Unique Value'
                                          - Returns ('Environmental Sound/Unique Value', None)
            Extension Allowed:
                'Event/Experiment control/demo_extension'
                                          - Returns ('Experiment Control/demo_extension/', None)
                'Event/Experiment control/demo_extension/second_part'
                                          - Returns ('Experiment Control/demo_extension/second_part', None)

            Returns
            -------
            tuple.  (short_tag, None or error).  If not found, (original_tag, error)

        """
        # Remove leading and trailing slashes
        if hed_tag.startswith('/'):
            hed_tag = hed_tag[1:]
        if hed_tag.endswith('/'):
            hed_tag = hed_tag[:-1]

        clean_tag = hed_tag.lower()
        split_tag = clean_tag.split("/")

        found_tag_entry = None
        index = len(hed_tag)
        last_found_index = index
        # Iterate over tags right to left keeping track of current character index
        for tag in reversed(split_tag):
            # As soon as we find a non extension tag, mark down the index and bail.
            if tag in self.map_schema.tag_dict:
                found_tag_entry = self.map_schema.tag_dict[tag]
                last_found_index = index
                index -= len(tag)
                break

            last_found_index = index
            index -= len(tag)
            # Skip slashes
            if index != 0:
                index -= 1

        if found_tag_entry is None:
            error = error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND, hed_tag, index, last_found_index)
            return hed_tag, error

        # Verify the tag has the correct path above it.
        main_hed_portion = clean_tag[:last_found_index]
        tag_string = found_tag_entry.long_clean_tag
        if not tag_string.endswith(main_hed_portion):
            error = error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, hed_tag, index, last_found_index,
                                                     found_tag_entry.long_org_tag)
            return hed_tag, error

        remainder = hed_tag[last_found_index:]
        short_tag_string = found_tag_entry.short_org_tag + remainder
        return short_tag_string, None

