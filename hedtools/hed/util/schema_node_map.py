from defusedxml.lxml import parse
import lxml

class TagEntry:
    """This is a single entry in the tag dictionary.

       Keeps track of the human formatted short/long form of each tag.
    """

    def __init__(self, short_org_tag, long_org_tag):
        self.short_org_tag = short_org_tag
        self.long_org_tag = long_org_tag
        self.long_clean_tag = long_org_tag.lower()


class SchemaNodeMap:
    """     Helper class for seeing if a schema has any duplicate tags/validate basic existence
       """
    def __init__(self, hed_xml_file=None, hed_tree=None, use_full_name_as_key=False):
        self.parent_map = None
        self.tag_dict = {}
        self.current_depth_check = []
        self.tag_name_stack = []
        self.no_duplicate_tags = True
        self.use_full_name_as_key = use_full_name_as_key

        if hed_tree is not None:
            self.process_tree(hed_tree)
        elif hed_xml_file:
            try:
                hed_tree = parse(hed_xml_file)
            except lxml.etree.XMLSyntaxError as e:
                raise SchemaError(e.msg)
            hed_tree = hed_tree.getroot()
            self.process_tree(hed_tree)

    def process_tree(self, hed_tree):
        """Primary setup function.  Takes an XML tree and sets up the mapping dict."""
        # Create a map so we can go from child to parent easily.
        self.parent_map = {c: p for p in hed_tree.iter() for c in p}
        self._reset_map_schema()

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

    def _reset_map_schema(self):
        self.tag_name_stack = []
        self.tag_dict = {}
        self.current_depth_check = ["node"]
        self.no_duplicate_tags = True

    def _add_tag(self, new_tag, tag_stack):
        full_tag = "/".join(tag_stack)
        if self.use_full_name_as_key:
            clean_tag = full_tag.lower()
        else:
            clean_tag = new_tag.lower()
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

