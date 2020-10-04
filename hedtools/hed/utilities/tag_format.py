from defusedxml.lxml import parse
from hed.schema import utils
from hed.schema import constants
from hed.utilities import error_reporter
from hed.utilities import format_util

class TagEntry:
    """This is a single entry in the tag dictionary.

       Keeps track of the human formatted short/long form of each tag.
    """

    def __init__(self, short_org_tag, long_org_tag):
        self.short_org_tag = short_org_tag
        self.long_org_tag = long_org_tag
        self.long_clean_tag = long_org_tag.lower()

class TagFormat:
    """     Helper class for seeing if a schema has any duplicate tags, and also has functions to convert
        hed strings and tags short<>long
       """
    def __init__(self, hed_xml_file=None, hed_tree=None):
        self.parent_map = None
        self.tag_dict = {}
        self.current_depth_check = []
        self.tag_name_stack = []
        self.no_duplicate_tags = True

        if hed_tree is not None:
            self.process_tree(hed_tree)
        elif hed_xml_file:
            hed_tree = parse(hed_xml_file)
            hed_tree = hed_tree.getroot()
            self.process_tree(hed_tree)

    def process_tree(self, hed_tree):
        """Primary setup function.  Takes an XML tree and sets up the mapping dict."""
        # Create a map so we can go from child to parent easily.
        self.parent_map = {c: p for p in hed_tree.iter() for c in p}
        self._reset_tag_compare()

        for elem in hed_tree.iter():
            if elem.tag == "unitModifiers" or elem.tag == "unitClasses":
                break

            if elem.tag == "name":
                # handle special case where text is just "#"
                if elem.text and "#" in elem.text:
                    pass
                else:
                    nodes_in_parent = self._count_parent_nodes(elem)
                    while len(self.tag_name_stack) >= nodes_in_parent and len(self.tag_name_stack) > 0:
                        self.tag_name_stack.pop()
                    self.tag_name_stack.append(elem.text)
                    self._add_tag(elem.text, self.tag_name_stack)

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
        if not self.no_duplicate_tags:
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
        if not self.no_duplicate_tags:
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
                if tag not in self.tag_dict:
                    found_unknown_extension = True
                    if not found_tag_entry:
                        error = error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND, hed_tag,
                                                                 index_start, index_end)
                        return hed_tag, error
                    continue

                tag_entry = self.tag_dict[tag]
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
                if tag in self.tag_dict:
                    error = error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, hed_tag,
                                                             index_start, index_end,
                                                             self.tag_dict[tag].long_org_tag)
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
            if tag in self.tag_dict:
                found_tag_entry = self.tag_dict[tag]
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

    def has_duplicate_tags(self):
        """Converting functions don't make much sense to work if we have duplicate tags and are disabled"""
        return not self.no_duplicate_tags

    def find_duplicate_tags(self):
        """Finds all tags that are not unique.

        Returns
        -------
            dict: (duplicate_tag_name : list of tag entries with this name)
        """
        duplicate_dict = {}
        for tag_name in self.tag_dict:
            modified_name = f'{tag_name}'
            if isinstance(self.tag_dict[tag_name], list):
                duplicate_dict[modified_name] = self.tag_dict[tag_name]

        return duplicate_dict

    def dupe_tag_iter(self, return_detailed_info=False):
        """Returns an iterator that goes over each line of the duplicate tags dict, including descriptive ones."""
        duplicate_dict = self.find_duplicate_tags()
        for tag_name in duplicate_dict:
            if return_detailed_info:
                yield f"Duplicate tag found {tag_name} - {len(duplicate_dict[tag_name])} versions"
            for tag_entry in duplicate_dict[tag_name]:
                if return_detailed_info:
                    yield f"\t{tag_entry.short_org_tag}: {tag_entry.long_org_tag}"
                else:
                    yield f"{tag_entry.long_org_tag}"

    def print_tag_dict(self):
        """Utility function that prints the human readable form of duplicate tags to console."""
        for line in self.dupe_tag_iter(True):
            print(line)

    def _reset_tag_compare(self):
        self.tag_name_stack = []
        self.tag_dict = {}
        self.current_depth_check = ["node"]
        self.no_duplicate_tags = True

    def _add_tag(self, new_tag, tag_stack):
        clean_tag = new_tag.lower()
        full_tag = "/".join(tag_stack)
        new_tag_entry = TagEntry(new_tag, full_tag)
        if clean_tag not in self.tag_dict:
            self.tag_dict[clean_tag] = new_tag_entry
        else:
            self.no_duplicate_tags = False
            if not isinstance(self.tag_dict[clean_tag], list):
                self.tag_dict[clean_tag] = [self.tag_dict[clean_tag]]
            self.tag_dict[clean_tag].append(new_tag_entry)

        return new_tag_entry

    def _count_parent_nodes(self, node):
        nodes_in_parent = 0
        parent_elem = node
        while parent_elem in self.parent_map:
            if parent_elem.tag in self.current_depth_check:
                nodes_in_parent += 1
            parent_elem = self.parent_map[parent_elem]

        return nodes_in_parent


def check_for_duplicate_tags(local_xml_file):
    """Checks if a source XML file has duplicate tags.

        If there are no duplicates, returns None.
        If there are any duplicates, points to a file containing the formatted result.
    Parameters
    ----------
        local_xml_file: string
    Returns
    -------
    dictionary
            Contains source file location, dest, etc
    """
    tag_compare = TagFormat(local_xml_file)
    dupe_tag_file = None
    if tag_compare.has_duplicate_tags():
        dupe_tag_file = utils.write_text_iter_to_file(tag_compare.dupe_tag_iter(True))
    tag_compare.print_tag_dict()
    hed_info_dictionary = {constants.HED_XML_TREE_KEY: None,
                           constants.HED_XML_VERSION_KEY: None,
                           constants.HED_CHANGE_LOG_KEY: None,
                           constants.HED_WIKI_PAGE_KEY: None,
                           constants.HED_INPUT_LOCATION_KEY: local_xml_file,
                           constants.HED_OUTPUT_LOCATION_KEY: dupe_tag_file}
    return hed_info_dictionary
