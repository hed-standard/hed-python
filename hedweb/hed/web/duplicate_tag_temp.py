from hed.util.file_util import write_text_iter_to_file
from hed.schematools import constants as converter_constants
from hed.web.schema_node_map_temp import SchemaNodeMap


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
    map_schema = SchemaNodeMap(local_xml_file)
    dupe_tag_file = None
    if map_schema.has_duplicate_tags():
        dupe_tag_file = write_text_iter_to_file(map_schema.dupe_tag_iter(True))
    map_schema.print_tag_dict()
    hed_info_dictionary = {converter_constants.HED_XML_TREE_KEY: None,
                           converter_constants.HED_XML_VERSION_KEY: None,
                           converter_constants.HED_CHANGE_LOG_KEY: None,
                           converter_constants.HED_WIKI_PAGE_KEY: None,
                           converter_constants.HED_INPUT_LOCATION_KEY: local_xml_file,
                           converter_constants.HED_OUTPUT_LOCATION_KEY: dupe_tag_file}
    return hed_info_dictionary
