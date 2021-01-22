from enum import Enum

from hed.schema import constants
from hed.util import file_util
from hed.util.hed_schema import HedSchema
from hed.util.exceptions import HedFileError
from hed.schema.schema_validator import validate_schema

class MainParseMode(Enum):
    MainTags = 1
    UnitClassTags = 2
    UnitModifierTags = 3


class HEDXml2Wiki:
    def __init__(self):
        self.parent_map = None
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.parse_mode = MainParseMode.MainTags
        self.output = []

    def count_parent_nodes(self, node, tags_to_check=None):
        """Count what depth this node should be considered, counting only tags in tags_to_check"""
        if tags_to_check is None:
            tags_to_check = ["node"]
        nodes_in_parent = 0
        parent_elem = node
        while parent_elem in self.parent_map:
            if parent_elem.tag in tags_to_check:
                nodes_in_parent += 1
            parent_elem = self.parent_map[parent_elem]

        return nodes_in_parent

    def flush_current_tag(self):
        if self.current_tag_string or self.current_tag_extra:
            if self.current_tag_extra:
                new_tag = f"{self.current_tag_string} <nowiki>{self.current_tag_extra}</nowiki>"
            else:
                new_tag = self.current_tag_string
            # print(new_tag)
            self.output.append(new_tag)
            self.current_tag_string = ""
            self.current_tag_extra = ""

    def add_blank_line(self):
        self.output.append("")

    def process_tree(self, hed_tree):
        # Create a map so we can go from child to parent easily.
        self.parent_map = {c: p for p in hed_tree.iter() for c in p}
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.parse_mode = MainParseMode.MainTags
        self.output = []

        parse_mode = MainParseMode.MainTags
        for elem in hed_tree.iter():
            if elem.tag == "HED":
                hed_attrib_string = self.get_attribs_from_root_hed_node(elem)
                self.current_tag_string = f"HED {hed_attrib_string}"
                self.flush_current_tag()
                self.add_blank_line()
                self.current_tag_string = "!# start hed"
                self.flush_current_tag()
                continue
            elif elem.tag == "unitClasses":
                self.flush_current_tag()
                parse_mode = MainParseMode.UnitClassTags

                section_text_name = "Unit classes"
                self.current_tag_string += "\n"
                self.current_tag_string += f"'''{section_text_name}'''"
                self.add_blank_line()
            elif elem.tag == "unitModifiers":
                self.flush_current_tag()
                parse_mode = MainParseMode.UnitModifierTags

                section_text_name = "Unit modifiers"
                self.current_tag_string += "\n"
                self.current_tag_string += f"'''{section_text_name}'''"
                # self.add_blank_line()

            nodes_in_parent = None
            if parse_mode == MainParseMode.MainTags:
                nodes_in_parent = self.count_parent_nodes(elem) - 1
                if elem.tag == "node":
                    self.flush_current_tag()
            elif parse_mode == MainParseMode.UnitClassTags:
                nodes_in_parent = self.count_parent_nodes(elem,
                                                          tags_to_check=["unitClasses", "units"])
                if elem.tag == "unit" or elem.tag == "unitClass":
                    self.flush_current_tag()

                # Handle old style units where they don't have separate tags.
                if elem.tag == "units" and not elem.text.isspace():
                    self.flush_current_tag()
                    unit_list = elem.text.split(',')
                    for unit in unit_list:
                        prefix = "*" * nodes_in_parent
                        self.current_tag_string += f"{prefix} {unit}"
                        self.flush_current_tag()

            elif parse_mode == MainParseMode.UnitModifierTags:
                nodes_in_parent = self.count_parent_nodes(elem, tags_to_check=["unitModifiers"])
                if elem.tag == "unitModifier":
                    self.flush_current_tag()

            # stuff that applies to all modes
            if elem.tag == "name" or elem.tag == "unit":
                # handle special case where text is just "#"
                if elem.text and "#" in elem.text:
                    prefix = "*" * nodes_in_parent
                    self.current_tag_string += f"{prefix}"
                    self.current_tag_extra = f"{elem.text} {self.current_tag_extra}"
                else:
                    if nodes_in_parent == 0:
                        self.current_tag_string += f"'''{elem.text}'''"
                        self.add_blank_line()
                    elif nodes_in_parent > 0:
                        prefix = "*" * nodes_in_parent
                        self.current_tag_string += f"{prefix} {elem.text}"
                    elif nodes_in_parent == -1:
                        self.current_tag_string += elem.tag

            self.add_elem_desc(elem)
            self.add_elem_attributes(elem)

        self.flush_current_tag()
        self.current_tag_string = "!# end hed"
        self.flush_current_tag()

        return self.output

    def add_elem_desc(self, elem):
        """Add description from passed in elem to current tag"""
        if elem.tag == "description":
            if self.current_tag_extra:
                self.current_tag_extra += " "
            self.current_tag_extra += f"[{elem.text}]"

    def add_elem_attributes(self, elem):
        """Add all attributes from the passed in elem to current tag"""
        if len(elem.attrib) > 0:
            self.current_tag_extra += "{"
            is_first = True
            sorted_keys = []
            # This is purely optional, but makes comparing easier when it's identical
            expected_key_order = ["takesValue", "isNumeric", "requireChild", "required", "unique",
                                  "predicateType", "position", "unitClass", "default"]
            for expected_key in expected_key_order:
                if expected_key in elem.attrib:
                    sorted_keys.append(expected_key)
            for attrib_name in elem.attrib:
                if attrib_name not in sorted_keys:
                    sorted_keys.append(attrib_name)

            for attrib_name in sorted_keys:
                attrib_val = elem.attrib[attrib_name]
                if attrib_name == "unitClass":
                    unit_classes = attrib_val.split(",")
                    for unit_class in unit_classes:
                        if not is_first:
                            self.current_tag_extra += ", "
                        is_first = False
                        self.current_tag_extra += f"{attrib_name}={unit_class}"
                else:
                    if not is_first:
                        self.current_tag_extra += ", "
                    is_first = False
                    if attrib_val == "true":
                        self.current_tag_extra += attrib_name
                    elif attrib_val.isdigit():
                        self.current_tag_extra += f"{attrib_name}={attrib_val}"
                    else:
                        self.current_tag_extra += f"{attrib_name}={attrib_val}"
            self.current_tag_extra += "}"

    @staticmethod
    def get_attribs_from_root_hed_node(elem):
        attrib_values = [f"{attr}:{elem.attrib[attr]}" for attr in constants.HED_VALID_ATTRIBUTES if
                         attr in elem.attrib]
        final_attrib_string = ", ".join(attrib_values)
        return final_attrib_string


def convert_hed_xml_2_wiki(hed_xml_url, local_xml_file=None, check_for_issues=True,
                           display_filename=None):
    """Converts the local HED xml file into a wikimedia file

    Parameters
    ----------
    hed_xml_url: str or None
        url pointing to the .xml file to use
    local_xml_file: str or None
        filepath to local xml hed schema(overrides hed_xml_url)
    check_for_issues : bool
        After conversion checks for warnings like capitalization or invalid characters.
    display_filename: str
        If present, it will display errors as coming from this filename instead of the actual source.
        Useful for temporary files and similar.
    Returns
    -------
    mediawiki_filename: str
        Location of output mediawiki file, None on complete failure
    issues_list: [{}]
        returns a list of error/warning dictionaries
    """
    if local_xml_file is None:
        local_xml_file = file_util.url_to_file(hed_xml_url)

    try:
        hed_xml_tree = HedSchema.parse_hed_xml_file(local_xml_file, display_filename)
    except HedFileError as e:
        return None, e.format_error_message()

    xml2wiki = HEDXml2Wiki()
    output_strings = xml2wiki.process_tree(hed_xml_tree)
    local_mediawiki_file = file_util.write_strings_to_file(output_strings, ".mediawiki")

    issue_list = []
    if check_for_issues:
        warnings = validate_schema(local_xml_file, display_filename=display_filename)
        issue_list += warnings

    return local_mediawiki_file, issue_list
