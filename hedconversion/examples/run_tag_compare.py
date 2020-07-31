# Simplified example code for running xml2_wiki

from shutil import move
from hed.converter import tag_compare
from hed.converter import constants

if __name__ == '__main__':
    result_dict = tag_compare.check_for_duplicate_tags("HED7.1.1.xml")
    output_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    move(output_location, "results.txt")
