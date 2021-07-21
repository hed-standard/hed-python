"""
Example of converting a hed schema from .xml format to .mediawiki format.

Functions Demonstrated:
wiki2xml.convert_schema_to_format - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
hed.get_printable_issue_string - method that converts the list of issues to a human readable form.
"""

from shutil import move
import hed
from hed import schema
from hed.util.file_util import write_strings_to_file

if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
    local_hed_file = None
    hed_schema = schema.load_schema(hed_file_path=local_hed_file, hed_url_path=hed_xml_url)
    file_strings, errors = schema.convert_schema_to_format(hed_schema, save_as_mediawiki=True)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED7.1.1.xml")
    if file_strings:
        mediawiki_location = write_strings_to_file(file_strings)
        move(mediawiki_location, "HED7.1.1.mediawiki")
