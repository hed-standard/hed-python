# Simplified example code for running xml2_wiki

from shutil import move
from hed.tools import duplicate_tags
from hed.schematools import constants

if __name__ == '__main__':
    result_dict = duplicate_tags.check_for_duplicate_tags("data/HED7.1.1.xml")
    output_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    move(output_location, "results.txt")
