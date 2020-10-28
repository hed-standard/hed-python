# Simplified example code for running xml2_wiki

from shutil import move
from hed.utilities.util import map_schema
from hed.schema.util import constants

if __name__ == '__main__':
    result_dict = map_schema.check_for_duplicate_tags("HED7.1.1.xml")
    output_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    move(output_location, "results.txt")
