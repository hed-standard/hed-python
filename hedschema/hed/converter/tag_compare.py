from defusedxml.lxml import parse
from hed.converter import utils
from hed.converter import constants


class TagCompare():
    def __init__(self):
        self.parent_map = None
        self.tag_dict = {}
        self.tag_dict_dict = {}
        self.current_depth_check = []
        self.tag_name_stack = []

    def process_tree(self, hed_tree):
        # Create a map so we can go from child to parent easily.
        self.parent_map = {c: p for p in hed_tree.iter() for c in p}
        self.tag_dict_dict = {}

        self._start_new_section("Main Tags")

        for elem in hed_tree.iter():
            if elem.tag == "unitClasses":
                self._start_new_section(elem.tag, ["unitClasses", "units"])
            elif elem.tag == "unitModifiers":
                self._start_new_section(elem.tag, ["unitModifiers"])
            if elem.tag == "name" or elem.tag == "unit":
                # handle special case where text is just "#"
                if elem.text and "#" in elem.text:
                    pass
                else:
                    nodes_in_parent = self._count_parent_nodes(elem)
                    while len(self.tag_name_stack) >= nodes_in_parent and len(self.tag_name_stack) > 0:
                        self.tag_name_stack.pop()
                    self.tag_name_stack.append(elem.text)
                    full_tag_name = "/".join(self.tag_name_stack)
                    self._add_tag(elem.text, full_tag_name)

    def _start_new_section(self, dict_name, current_depth_check=None):
        self.tag_name_stack = []
        self.tag_dict = {}
        self.tag_dict_dict[dict_name] = self.tag_dict
        if current_depth_check is None:
            current_depth_check = ["node"]
        self.current_depth_check = current_depth_check

    def _add_tag(self, new_tag, full_tag):
        if new_tag not in self.tag_dict:
            self.tag_dict[new_tag] = [full_tag]
        else:
            self.tag_dict[new_tag].append(full_tag)

    def _count_parent_nodes(self, node):
        nodes_in_parent = 0
        parent_elem = node
        while parent_elem in self.parent_map:
            if parent_elem.tag in self.current_depth_check:
                nodes_in_parent += 1
            parent_elem = self.parent_map[parent_elem]

        return nodes_in_parent

    def find_duplicate_tags(self):
        duplicate_dict = {}
        for dict_name in self.tag_dict_dict:
            tag_dict = self.tag_dict_dict[dict_name]
            for tag_name in tag_dict:
                modified_name = f'{dict_name}: {tag_name}'
                if len(tag_dict[tag_name]) > 1:
                    duplicate_dict[modified_name] = tag_dict[tag_name]

        return duplicate_dict

    def dupe_tag_iter(self):
        """Returns an iterator that goes over each line of the duplicate tags dict, including descriptive ones."""
        duplicate_dict = self.find_duplicate_tags()
        for tag_name in duplicate_dict:
            yield f"Duplicate tag found {tag_name} - {len(duplicate_dict[tag_name])} versions"
            for full_tag in duplicate_dict[tag_name]:
                yield f"\t{full_tag}"

    def print_tag_dict(self):
        for line in self.dupe_tag_iter():
            print(line)


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
    hed_tree = parse(local_xml_file)
    hed_tree = hed_tree.getroot()
    xml2wiki = TagCompare()
    xml2wiki.process_tree(hed_tree)
    dupe_tag_file = None
    if any(xml2wiki.dupe_tag_iter()):
        dupe_tag_file = utils.write_text_iter_to_file(xml2wiki.dupe_tag_iter())

    hed_info_dictionary = {constants.HED_XML_TREE_KEY: hed_tree,
                           constants.HED_XML_VERSION_KEY: None,
                           constants.HED_CHANGE_LOG_KEY: None,
                           constants.HED_WIKI_PAGE_KEY: None,
                           constants.HED_INPUT_LOCATION_KEY: local_xml_file,
                           constants.HED_OUTPUT_LOCATION_KEY: dupe_tag_file}
    return hed_info_dictionary

