# Simplified example code for running xml2_wiki

from shutil import move
from hed.schema import duplicate_nodes

if __name__ == '__main__':
    local_hed_xml = "data/HED7.1.1.xml"
    output_location, errors = duplicate_nodes.check_for_duplicate_tags(local_hed_xml)
    move(output_location, "duplicate_tags_in_HEDXML.txt")
