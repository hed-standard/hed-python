from defusedxml.lxml import parse
from hed.converter import utils
from hed.converter import constants


class TagEntry:
    """This is a single entry in the tag dictionary.

       Keeps track of the human formatted short/long form of each tag.
    """

    def __init__(self, short_org_tag, long_org_tag):
        self.short_org_tag = short_org_tag
        self.long_org_tag = long_org_tag

    def get_tag_string(self, remainder, return_long_version=False):
        tag_string = self.short_org_tag
        if return_long_version:
            tag_string = self.long_org_tag
        if remainder:
            return tag_string + remainder
        return tag_string


class TagCompare:
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

        self._finalize_processing()

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
        hed_tags = self._split_hed_string(hed_string)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                tag_entry, remainder = self.get_tag_entry(tag)
                # This is notably faster "inline" rather than calling a conversion function
                converted_tag = None
                if tag_entry:
                    converted_tag = tag_entry.short_org_tag + remainder

                if converted_tag is None:
                    converted_tag = tag
                final_string += converted_tag
            else:
                final_string += tag

        return final_string

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
        hed_tags = self._split_hed_string(hed_string)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                tag_entry, remainder = self.get_tag_entry(tag)
                # This is notably faster "inline" rather than calling a conversion function
                converted_tag = None
                if tag_entry:
                    converted_tag = tag_entry.long_org_tag + remainder

                if converted_tag is None:
                    converted_tag = tag
                final_string += converted_tag
            else:
                final_string += tag

        return final_string

    def convert_to_long_tag(self, hed_tag):
        """Convert a single tag from any form to the longest form

            eg  Event/Sensory event -> Event/Sensory event
                Sensory event -> Event/Sensory event
         Parameters
            ----------
            hed_tag: str
                a single hed tag
            Returns
            -------
                str: The converted tag
        """
        tag_entry, remainder = self.get_tag_entry(hed_tag)
        if tag_entry:
            final_tag = tag_entry.get_tag_string(remainder, return_long_version=True)
            return final_tag

        return None

    def convert_to_short_tag(self, hed_tag):
        """Convert a single tag from any form to the shortest form

            eg  Event/Sensory event -> Sensory event
                Sensory event -> Sensory event
         Parameters
            ----------
            hed_tag: str
                a single hed tag
            Returns
            -------
                str: The converted tag
        """
        tag_entry, remainder = self.get_tag_entry(hed_tag)
        if tag_entry:
            final_tag = tag_entry.get_tag_string(remainder)
            return final_tag

        return None

    def get_tag_entry(self, hed_tag):
        """This takes a hed tag(short or long form) and finds the lowest level valid tag_entry.
            Note: NO validation is done for if tags take value or allow extensions, the following is just examples.

            eg 'Event'                    - Returns (entry for 'Event', "")
               'Event/Sensory event'      - Returns (entry for 'Sensory event', "")
            Takes Value:
               'Item/Sound/Environmental sound/Unique Value'
                                          - Returns (entry for 'Environmental Sound', "Unique Value")
            Extension Allowed:
                'Experiment control/demo_extension'
                                          - Returns (entry for 'Experiment Control', "demo_extension")
                'Event/Experiment control/demo_extension/second_part'
                                          - Returns (entry for 'Experiment Control', "demo_extension/second_part")

            Returns
            -------
            tuple.  (tag_entry, remainder of tag).  If not found, (None, None)

        """
        if not self.no_duplicate_tags:
            raise ValueError("Cannot process tags when duplicate tags exist in schema.")

        clean_tag = hed_tag.lower()
        if clean_tag in self.tag_dict:
            return self.tag_dict[clean_tag], ""

        found_index = clean_tag.rfind("/")
        while found_index != -1:
            check_tag = clean_tag[:found_index]
            remainder = hed_tag[found_index:]
            if check_tag in self.tag_dict:
                return self.tag_dict[check_tag], remainder

            found_index = clean_tag.rfind("/", 0, found_index)

        return None, None

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

    def _finalize_processing(self):
        if not self.has_duplicate_tags():
            # Also add every intermediate version of every tag.
            # eg: Attribute/Sensory/Visual/Color should also add:
            # Color, Visual/Color, Sensory/Visual/Color
            new_entries = {}
            for tag_entry in self.tag_dict.values():
                clean_tag = tag_entry.long_org_tag.lower()
                slash_delimiter = '/'
                found_index = clean_tag.find(slash_delimiter)
                while found_index != -1:
                    new_clean_tag = clean_tag[found_index + 1:]
                    new_entries[clean_tag] = tag_entry
                    clean_tag = new_clean_tag
                    found_index = clean_tag.find(slash_delimiter)

            self.tag_dict.update(new_entries)

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

    @staticmethod
    def _split_hed_string(hed_string):
        """Takes a hed string and splits it into delimiters and tags

            Note: This does not validate tags in any form.

        Parameters
        ----------
            hed_string: string
                the hed string to split
        Returns
        -------
        list of tuples.
            each tuple: (is_hed_tag, (start_pos, end_pos))
            is_hed_tag: bool
                This is a hed tag if true, delimiter if not
            start_pos: int
                index of start of string in hed_string
            end_pos: int
                index of end of string in hed_string
        """
        tag_delimiters = ",()~"
        current_spacing = 0
        inside_d = True
        result_positions = []
        start_pos = None
        last_end_pos = None
        for i, char in enumerate(hed_string):
            if char == " ":
                current_spacing += 1
                continue

            if char in tag_delimiters:
                if not inside_d:
                    inside_d = True
                    if start_pos is not None:
                        last_end_pos = i - current_spacing
                        # view_string = hed_string[start_pos: last_end_pos]
                        result_positions.append((True, (start_pos, last_end_pos)))
                        current_spacing = 0
                        start_pos = None
                continue

            # If we have a current delimiter, end it here.
            if inside_d and last_end_pos is not None:
                # view_string = hed_string[last_end_pos: i]
                result_positions.append((False, (last_end_pos, i)))
                last_end_pos = None

            current_spacing = 0
            inside_d = False
            if start_pos is None:
                start_pos = i

        if last_end_pos is not None and len(hed_string) != last_end_pos:
            # view_string = hed_string[last_end_pos: len(hed_string)]
            result_positions.append((False, (last_end_pos, len(hed_string))))
        if start_pos is not None:
            # view_string = hed_string[start_pos: len(hed_string)]
            result_positions.append((True, (start_pos, len(hed_string) - current_spacing)))

        # debug_result_strings = [hed_string[startpos:endpos] for (is_hed_string, (startpos, endpos)) in result_positions]
        return result_positions


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
    tag_compare = TagCompare(local_xml_file)
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
