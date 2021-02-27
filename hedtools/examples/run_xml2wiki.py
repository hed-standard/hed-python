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


if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
    local_xml_file = None
    mediawiki_location, errors = schema.convert_schema_to_format(hed_xml_url, local_xml_file, save_as_mediawiki=True)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED7.1.1.xml")
    if mediawiki_location:
        move(mediawiki_location, "HED7.1.1.mediawiki")
