from defusedxml.lxml import parse
from hed.converter import utils
from hed.converter import constants

class TagEntry:
    """This is a single entry in the tag dictionary.

    If there are no duplicate tags in the schema, each tag also points to its parent and children.

    """
    def __init__(self, short_org_tag, long_org_tag, extension_allowed=False, parent=None):
        self.short_org_tag = short_org_tag
        self.long_org_tag = long_org_tag
        self.takes_value = False
        self.extension_allowed = extension_allowed

        self.parent_tag = parent
        self.children = []
        if self.parent_tag:
            self.parent_tag.add_child(self)

    def add_child(self, child):
        self.children.append(child)
        child.parent_tag = self

    def is_child_of(self, parent_entry):
        if self.parent_tag != parent_entry:
            return False
        return True

    def has_direct_child_with_takes_value(self):
        for tag_entry in self.children:
            if tag_entry.takes_value:
                return True
        return False

    def get_tag_string(self, remainder, return_long_version=False):
        tag_string = self.short_org_tag
        if return_long_version:
            tag_string = self.long_org_tag
        if self.takes_value:
            if remainder.rfind('/') != -1:
                # raise ValueError(
                #     f"Invalid syntax in takes value{tag_string}.  Did you mean to make an extension tag?")
                return None
            return f"{tag_string}/{remainder}"
        elif self.extension_allowed and remainder is not None:
            return f"{tag_string}/{remainder}"
        elif remainder:
            return None
        return tag_string


class TagCompare:
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
        # Create a map so we can go from child to parent easily.
        self.parent_map = {c: p for p in hed_tree.iter() for c in p}
        self._reset_tag_compare()

        mark_next_node_as_extension_allowed = False
        current_tag_entry = None
        for elem in hed_tree.iter():
            if elem.tag == "unitModifiers" or elem.tag == "unitClasses":
                break

            if "extensionAllowed" in elem.attrib:
                mark_next_node_as_extension_allowed = True

            if elem.tag == "name":
                # handle special case where text is just "#"
                if elem.text and "#" in elem.text:
                    current_tag_entry.takes_value = True
                else:
                    nodes_in_parent = self._count_parent_nodes(elem)
                    while len(self.tag_name_stack) >= nodes_in_parent and len(self.tag_name_stack) > 0:
                        self.tag_name_stack.pop()
                    self.tag_name_stack.append(elem.text)
                    current_tag_entry = self._add_tag(elem.text, self.tag_name_stack, mark_next_node_as_extension_allowed)
                    mark_next_node_as_extension_allowed = False

        self._finalize_processing()

    def _finalize_processing(self):
        if not self.has_duplicate_tags():
            # Mark child tags as extension allowed as appropriate.
            # This relies on python 3.7 ordered dict behavior.
            for tag_name, tag_entry in self.tag_dict.items():
                parent_tag_entry = tag_entry.parent_tag
                if parent_tag_entry and (parent_tag_entry.extension_allowed and not parent_tag_entry.has_direct_child_with_takes_value()):
                    tag_entry.extension_allowed = True

            # Add the long versions of the tag to the dictionary too.
            self.tag_dict.update(dict((self._get_clean_tag(v.long_org_tag), v) for k, v in self.tag_dict.items()))

    def _reset_tag_compare(self):
        self.tag_name_stack = []
        self.tag_dict = {}
        self.current_depth_check = ["node"]
        self.no_duplicate_tags = True

    def _get_clean_tag(self, tag):
        return tag.lower()

    def _add_tag(self, new_tag, tag_stack, extension_allowed=False):
        clean_tag = self._get_clean_tag(new_tag)
        full_tag = "/".join(tag_stack)
        parent_tag_entry = None
        # There is no clean tree to make if we have any duplicate tags, so just stop trying.
        if not self.has_duplicate_tags() and len(tag_stack) > 1:
            parent_tag = self._get_clean_tag(tag_stack[-2])
            parent_tag_entry = self.tag_dict[parent_tag]

        new_tag_entry = TagEntry(new_tag, full_tag, extension_allowed, parent_tag_entry)

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

    def _get_root_tag_entry(self, hed_tag):
        """This returns the tag entry for the first sub_tag in hed_tag.

           It does not validate anything after the first / found.

           Parameters:
           hed_tag: A short or long formatted hed tag

           Returns:
            Tuple (tag_entry, remainder_of_tag)
            Returns None, None if nothing passed or it is not a tag.
        """
        if hed_tag is None:
            return None, None

        remainder = hed_tag
        index = hed_tag.find('/')
        if index != -1:
            split_tag, remainder = self._get_clean_tag(remainder[:index]), remainder[index + 1:]
        else:
            split_tag = self._get_clean_tag(remainder)
            remainder = None

        if split_tag in self.tag_dict:
            return self.tag_dict[split_tag], remainder

        return None, None

    def find_duplicate_tags(self):
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
        for line in self.dupe_tag_iter(True):
            print(line)

    def get_tag_entry(self, tag):
        """This takes a hed tag(short or long form) and finds the lowest level valid tag_entry

            eg 'Event'                    - Returns (entry for 'Event', None)
               'Event/Sensory event'      - Returns (entry for 'Sensory event', None)
            Takes Value:
               'Item/Sound/Environmental sound/Unique Value'      - Returns (entry for 'Environmental Sound', "Unique Value")
            Extension Allowed:
                'Experiment control/demo_extension'                   - Returns (entry for 'Experiment Control', "demo_extension")
                'Event/Experiment control/demo_extension/second_part'  - Returns (entry for 'Experiment Control', "demo_extension/second_part")

            Returns:
            tuple.  (tag_entry, remainder of tag).  If not found, (None, None)

        """
        if self.has_duplicate_tags():
            raise ValueError("Cannot process tags when duplicate tags exist in schema.")

        current_tag_entry, remainder = self._get_root_tag_entry(tag)
        while True:
            possible_child_tag_entry, possible_remainder = self._get_root_tag_entry(remainder)

            if not possible_child_tag_entry:
                break

            if possible_child_tag_entry:
                if not possible_child_tag_entry.is_child_of(current_tag_entry):
                    return None, None

            current_tag_entry = possible_child_tag_entry
            remainder = possible_remainder

        return current_tag_entry, remainder

    def short_to_long_tag(self, short_tag):
        tag_entry, remainder = self.get_tag_entry(short_tag)
        if tag_entry:
            final_tag = tag_entry.get_tag_string(remainder, return_long_version=True)
            return final_tag

        return None

    def long_to_short_tag(self, long_tag):
        tag_entry, remainder = self.get_tag_entry(long_tag)
        if tag_entry:
            final_tag = tag_entry.get_tag_string(remainder)
            return final_tag

        return None
        #raise ValueError(f"Invalid short tag {short_tag}")

    def has_duplicate_tags(self):
        return not self.no_duplicate_tags


def check_for_duplicate_tags(local_xml_file):
    """Checks if a source XML file has duplicate tags.

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


def convert_tag_to_long(short_tag, local_xml_file):
    tag_compare = TagCompare(local_xml_file)
    return tag_compare.short_to_long_tag(short_tag)


def convert_tag_to_short(full_tag, local_xml_file):
    tag_compare = TagCompare(local_xml_file)
    return tag_compare.long_to_short_tag(full_tag)
